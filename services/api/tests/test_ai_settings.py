import io
import json
import urllib.error

import pytest
from sqlalchemy import select, text

from finz_api.ai.gateway import (
    AIProviderRegistry,
    ClaudeAdapter,
    GeminiAdapter,
    OpenAIAdapter,
    ProviderConfig,
    ProviderError,
    http_transport,
)
from finz_api.ai.settings import AISetting, OSSecretStore, generate_for_task


class MemorySecrets:
    def __init__(self):
        self.values = {}

    def get(self, ref):
        return self.values.get(ref)

    def set(self, ref, value):
        self.values[ref] = value

    def delete(self, ref):
        self.values.pop(ref, None)


@pytest.fixture
def ai(client, app):
    app.state.ai_secrets = MemorySecrets()
    return client, app


def save(client, provider="openai", model="model-from-user"):
    return client.put(
        "/api/v1/settings/ai",
        json={"provider": provider, "model": model, "api_key": "test-only-secret-value"},
    )


@pytest.mark.parametrize("provider", ["openai", "gemini", "claude"])
def test_save_read_switch_and_remove(ai, provider, caplog):
    client, app = ai
    project = client.post("/api/v1/projects", json={"name": "Dự án riêng"}).json()
    save(client)
    result = save(client, provider)
    assert result.status_code == 200
    data = result.json()
    assert data["active_provider"] == provider
    assert all("test-only-secret-value" not in str(x) for x in (data, caplog.text))
    assert client.get("/api/v1/settings/ai").json() == data
    with app.state.sessions() as session:
        assert "test-only-secret-value" not in str(
            session.execute(text("select * from ai_settings")).all()
        )
    assert client.get("/api/v1/projects/" + project["id"]).json() == project
    result = client.delete("/api/v1/settings/ai/" + provider)
    assert result.status_code == 200
    assert not any(c["provider"] == provider for c in result.json()["configs"])


@pytest.mark.parametrize(
    "provider,adapter,response",
    [
        (
            "openai",
            OpenAIAdapter,
            {
                "status": "completed",
                "output": [
                    {"type": "message", "content": [{"type": "output_text", "text": '{"ok":true}'}]}
                ],
            },
        ),
        (
            "gemini",
            GeminiAdapter,
            {
                "status": "completed",
                "steps": [
                    {"type": "model_output", "content": [{"type": "text", "text": '{"ok":true}'}]}
                ],
            },
        ),
        (
            "claude",
            ClaudeAdapter,
            {
                "type": "message",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": '{"ok":true}'}],
            },
        ),
    ],
)
def test_mock_http_connection_and_task_reuse(ai, provider, adapter, response):
    client, app = ai
    requests = []

    def transport(url, headers, body):
        requests.append((url, body))
        return response

    app.state.ai_registry = AIProviderRegistry({provider: adapter(transport)})
    assert save(client, provider).status_code == 200
    assert requests == []
    assert client.post("/api/v1/settings/ai/test", json={}).status_code == 400
    assert requests == []
    r = client.post("/api/v1/settings/ai/test", json={"consent": True})
    assert r.status_code == 200
    assert r.json()["configs"][0]["status"] == "CONNECTED"
    assert r.json()["configs"][0]["latency_ms"] is not None
    assert len(requests) == 1
    assert "Dự án" not in str(requests)
    with app.state.sessions() as session:
        for task in ("topic_analyst", "seo_critic"):
            out = generate_for_task(
                session,
                app.state.ai_secrets,
                app.state.ai_registry,
                task,
                "Return JSON",
                {"type": "object"},
                consent=True,
            )
            assert out["provider"] == provider
    assert len(requests) == 3
    # An edit invalidates the previous connection result, even with the same key.
    r = client.put("/api/v1/settings/ai", json={"provider": provider, "model": "different-model"})
    assert r.json()["configs"][0]["status"] == "NOT_TESTED"


@pytest.mark.parametrize(
    "code,status",
    [
        ("API_KEY_INVALID", 401),
        ("PERMISSION_DENIED", 403),
        ("MODEL_NOT_FOUND", 404),
        ("QUOTA_EXCEEDED", 429),
        ("RATE_LIMITED", 429),
        ("CONNECTION_TIMEOUT", 504),
        ("PROVIDER_UNAVAILABLE", 503),
        ("INVALID_PROVIDER_RESPONSE", 502),
    ],
)
def test_normalized_failures_do_not_connect_or_leak(ai, code, status):
    client, app = ai
    save(client)

    def transport(*_):
        raise ProviderError(code, status)

    app.state.ai_registry = AIProviderRegistry({"openai": OpenAIAdapter(transport)})
    r = client.post("/api/v1/settings/ai/test", json={"consent": True})
    assert r.status_code == status
    error = r.json()["error"]
    assert error["code"] == code
    assert all(error.get(k) for k in ("reason", "impact", "solution", "next_action"))
    assert "test-only-secret-value" not in r.text
    assert client.get("/api/v1/settings/ai").json()["configs"][0]["status"] == "ERROR"


def test_os_store_fails_closed_without_secure_backend(monkeypatch):
    class Unsafe:
        pass

    monkeypatch.setattr("keyring.get_keyring", lambda: Unsafe())
    with pytest.raises(ProviderError, match="SECRET_STORE_UNAVAILABLE"):
        OSSecretStore().set("reference", "test-secret")


def test_invalid_json_and_incomplete_response_rejected(ai):
    client, app = ai
    save(client)
    for response in (
        {"status": "incomplete"},
        {"status": "completed", "output": []},
        {
            "status": "completed",
            "output": [
                {"type": "message", "content": [{"type": "output_text", "text": "not JSON"}]}
            ],
        },
    ):
        app.state.ai_registry = AIProviderRegistry(
            {"openai": OpenAIAdapter(lambda *args, response=response: response)}
        )
        assert client.post("/api/v1/settings/ai/test", json={"consent": True}).status_code == 502


def test_origin_validation_key_redaction_and_no_automatic_calls(ai):
    client, app = ai
    assert save(client).status_code == 200
    assert (
        client.put(
            "/api/v1/settings/ai",
            headers={"Origin": "https://untrusted.example"},
            json={"provider": "gemini", "model": "x", "api_key": "not-saved"},
        ).status_code
        == 403
    )
    assert len(app.state.ai_secrets.values) == 1
    r = client.put(
        "/api/v1/settings/ai", json={"provider": "bad", "model": "x", "api_key": "private-secret"}
    )
    assert r.status_code == 422
    assert "private-secret" not in r.text
    assert client.get("/api/v1/settings/ai").headers["cache-control"] == "no-store"
    with app.state.sessions() as session:
        assert session.scalar(select(AISetting)).status == "NOT_TESTED"


@pytest.mark.parametrize(
    "status,body,expected",
    [
        (401, {}, "API_KEY_INVALID"),
        (403, {}, "PERMISSION_DENIED"),
        (404, {}, "MODEL_NOT_FOUND"),
        (429, {}, "RATE_LIMITED"),
        (429, {"error": {"code": "insufficient_quota"}}, "QUOTA_EXCEEDED"),
        (503, {}, "PROVIDER_UNAVAILABLE"),
    ],
)
def test_transport_http_error_mapping(monkeypatch, status, body, expected):
    class Opener:
        def open(self, *args, **kwargs):
            raise urllib.error.HTTPError(
                "https://api.openai.com",
                status,
                "secret-not-returned",
                {},
                io.BytesIO(json.dumps(body).encode()),
            )

    monkeypatch.setattr("urllib.request.build_opener", lambda *args: Opener())
    with pytest.raises(ProviderError, match=expected):
        http_transport("https://api.openai.com", {}, {})


@pytest.mark.parametrize(
    "exception,code",
    [
        (TimeoutError(), "CONNECTION_TIMEOUT"),
        (urllib.error.URLError("network unavailable"), "NETWORK_ERROR"),
    ],
)
def test_network_error_mapping(monkeypatch, exception, code):
    class Opener:
        def open(self, *args, **kwargs):
            raise exception

    monkeypatch.setattr("urllib.request.build_opener", lambda *args: Opener())
    with pytest.raises(ProviderError, match=code):
        http_transport("https://api.openai.com", {}, {})


def test_missing_os_secret_invalidates_test_status(ai):
    client, app = ai
    save(client)
    app.state.ai_secrets.values.clear()
    result = client.post("/api/v1/settings/ai/test", json={"consent": True})
    assert result.status_code == 400
    assert client.get("/api/v1/settings/ai").json()["configs"][0]["status"] == "ERROR"


def test_explicit_mock_mode_never_invokes_transport(monkeypatch):
    monkeypatch.setenv("AI_GATEWAY_MODE", "mock")
    calls = []
    registry = AIProviderRegistry({"openai": OpenAIAdapter(lambda *args: calls.append(args))})
    with pytest.raises(ProviderError, match="MOCK_MODE"):
        registry.test_connection(ProviderConfig("openai", "user-model", "fake"), consent=True)
    assert calls == []


def test_gemini_request_matches_revision_and_uses_selected_model():
    captured = []

    def transport(url, headers, payload):
        captured.append((url, headers, payload))
        return {
            "status": "completed",
            "steps": [
                {"type": "model_output", "content": [{"type": "text", "text": '{"ok":true}'}]}
            ],
        }

    GeminiAdapter(transport).generate(
        ProviderConfig("gemini", "selected-model", "fake-key"), "JSON check"
    )
    url, headers, payload = captured[0]
    assert url == "https://generativelanguage.googleapis.com/v1beta/interactions"
    assert headers["Api-Revision"] == "2026-05-20"
    assert headers["x-goog-api-key"] == "fake-key"
    assert payload == {"model": "selected-model", "input": "JSON check", "store": False}
