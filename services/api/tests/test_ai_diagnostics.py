"""Provider diagnostics must retain evidence without retaining credentials or raw bodies."""

import io
import json
import logging
import socket
import ssl
import urllib.error
from email.message import Message

import pytest

from finz_api.ai.diagnostics import LOGGER, REQUEST_ID, file_handler
from finz_api.ai.gateway import AIProviderRegistry, GeminiAdapter, ProviderError, http_transport

from .test_ai_settings import MemorySecrets, save


def opener_error(monkeypatch, status, code, *, message="private upstream content", headers=None):
    class Opener:
        def open(self, *args, **kwargs):
            raise urllib.error.HTTPError(
                "https://generativelanguage.googleapis.com/v1beta/interactions",
                status,
                "unlogged reason",
                headers or {},
                io.BytesIO(json.dumps({"error": {"code": code, "message": message}}).encode()),
            )

    monkeypatch.setattr("urllib.request.build_opener", lambda *args: Opener())


@pytest.mark.parametrize(
    "status,upstream,code,local",
    [
        (400, "invalid_request", "PROVIDER_BAD_REQUEST", 400),
        (401, "authentication", "API_KEY_INVALID", 401),
        (403, "permission_denied", "PERMISSION_DENIED", 403),
        (404, "model_not_found", "MODEL_NOT_FOUND", 404),
        (429, "rate_limit_exceeded", "RATE_LIMITED", 429),
        (429, "quota_exceeded", "QUOTA_EXCEEDED", 429),
        (503, "service_unavailable", "PROVIDER_UNAVAILABLE", 503),
        (504, "deadline_exceeded", "CONNECTION_TIMEOUT", 504),
    ],
)
def test_upstream_status_and_code_survive(monkeypatch, caplog, status, upstream, code, local):
    opener_error(monkeypatch, status, upstream)
    token = REQUEST_ID.set("diagnostic-correlation")
    try:
        with caplog.at_level(logging.INFO, logger="finz.ai"):
            with pytest.raises(ProviderError) as error:
                http_transport(
                    "https://generativelanguage.googleapis.com/v1beta/interactions", {}, {}
                )
        assert error.value.code == code
        assert error.value.status == local
        assert error.value.upstream_status == status
        assert error.value.upstream_code == upstream
        record = json.loads(caplog.records[-1].message)
        assert record["request_id"] == "diagnostic-correlation"
        assert record["upstream_status"] == status
        assert record["upstream_code"] == upstream
        assert "private upstream content" not in caplog.text
    finally:
        REQUEST_ID.reset(token)


@pytest.mark.parametrize(
    "reason,code,kind",
    [
        (TimeoutError("unsafe details"), "CONNECTION_TIMEOUT", "TIMEOUT"),
        (socket.gaierror("unsafe details"), "NETWORK_ERROR", "DNS"),
        (ssl.SSLCertVerificationError("unsafe details"), "NETWORK_ERROR", "TLS_CERTIFICATE"),
        (ConnectionRefusedError("unsafe details"), "NETWORK_ERROR", "CONNECTION_REFUSED"),
        (ConnectionResetError("unsafe details"), "NETWORK_ERROR", "CONNECTION_RESET"),
    ],
)
def test_urlerror_unwraps_network_reason(monkeypatch, caplog, reason, code, kind):
    class Opener:
        def open(self, *args, **kwargs):
            assert kwargs["timeout"] == 20
            raise urllib.error.URLError(reason)

    monkeypatch.setattr("urllib.request.build_opener", lambda *args: Opener())
    with caplog.at_level(logging.INFO, logger="finz.ai"):
        with pytest.raises(ProviderError) as error:
            http_transport("https://generativelanguage.googleapis.com/v1beta/interactions", {}, {})
    assert error.value.code == code
    assert error.value.network_reason == kind
    assert error.value.upstream_status is None
    assert "unsafe details" not in caplog.text


def test_api_request_id_matches_log_and_frontend_response(client, app, monkeypatch, caplog):
    app.state.ai_secrets = MemorySecrets()
    app.state.ai_registry = AIProviderRegistry({"gemini": GeminiAdapter()})
    assert save(client, "gemini").status_code == 200
    headers = Message()
    headers["x-request-id"] = "google-request-123"
    opener_error(
        monkeypatch,
        503,
        "service_unavailable",
        headers=headers,
        message="test-only-secret-value must not be logged",
    )
    with caplog.at_level(logging.INFO, logger="finz.ai"):
        response = client.post("/api/v1/settings/ai/test", json={"consent": True})
    assert response.status_code == 503
    error = response.json()["error"]
    assert error["upstream_status"] == 503
    assert error["upstream_code"] == "service_unavailable"
    assert error["upstream_request_id"] == "google-request-123"
    record = json.loads(next(r.message for r in caplog.records if r.name == "finz.ai"))
    assert error["request_id"] == response.headers["x-request-id"] == record["request_id"]
    assert "test-only-secret-value" not in caplog.text + response.text
    assert "must not be logged" not in caplog.text + response.text


def test_echoed_secret_code_and_upstream_id_are_not_logged(monkeypatch, caplog):
    secret = "fake-sensitive-token-value"
    headers = Message()
    headers["x-request-id"] = secret
    opener_error(monkeypatch, 400, secret, message=secret, headers=headers)
    with caplog.at_level(logging.INFO, logger="finz.ai"):
        with pytest.raises(ProviderError) as error:
            http_transport(
                "https://generativelanguage.googleapis.com/v1beta/interactions",
                {"x-goog-api-key": secret},
                {"input": secret},
            )
    assert secret not in caplog.text + str(error.value.feedback())
    assert error.value.upstream_code is None
    assert error.value.upstream_request_id is None


def test_private_diagnostic_file(tmp_path):
    path = tmp_path / "private.jsonl"
    handler = file_handler(path)
    try:
        LOGGER.info('{"event":"test"}')
        handler.flush()
        assert path.stat().st_mode & 0o777 == 0o600
        assert json.loads(path.read_text())["event"] == "test"
    finally:
        LOGGER.removeHandler(handler)
        handler.close()
