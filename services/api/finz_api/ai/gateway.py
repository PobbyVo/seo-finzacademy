"""Opt-in provider gateway. Fixed HTTPS endpoints; no project data in connection tests."""

import json
import os
import socket
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Protocol

import jsonschema

from .diagnostics import emit, safe_code, safe_upstream_id

ENDPOINTS = {
    "openai": "https://api.openai.com/v1/responses",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/interactions",
    "claude": "https://api.anthropic.com/v1/messages",
}
ERRORS = {
    "PROVIDER_BAD_REQUEST": (
        "Provider từ chối tham số request (HTTP 400).",
        "Kiểm tra model, tham số và điều kiện tài khoản theo upstream code.",
    ),
    "NETWORK_ERROR": (
        "Không thiết lập được kết nối mạng tới provider.",
        "Kiểm tra DNS, TLS, proxy hoặc tường lửa theo network_reason. "
        "Chưa có HTTP status từ provider.",
    ),
    "MOCK_MODE": (
        "Gateway đang ở chế độ mock, không gọi API thật.",
        "Đặt AI_GATEWAY_MODE=live và khởi động lại khi muốn kiểm tra thật.",
    ),
    "AI_NOT_CONFIGURED": ("Chưa cấu hình AI.", "Lưu provider, model và API key trong Cài đặt."),
    "API_KEY_INVALID": ("API key không hợp lệ.", "Kiểm tra hoặc thay API key của provider."),
    "PERMISSION_DENIED": (
        "Không có quyền truy cập model.",
        "Kiểm tra quyền API và quyền sử dụng model.",
    ),
    "MODEL_NOT_FOUND": (
        "Không tìm thấy model.",
        "Nhập Model ID được cấp quyền trong tài khoản provider.",
    ),
    "QUOTA_EXCEEDED": ("Đã hết hạn mức.", "Kiểm tra billing và hạn mức tại provider."),
    "RATE_LIMITED": (
        "Provider giới hạn tần suất.",
        "Chờ rồi chủ động thử lại; ứng dụng không tự retry.",
    ),
    "CONNECTION_TIMEOUT": ("Provider không phản hồi đúng hạn.", "Kiểm tra mạng và thử lại sau."),
    "PROVIDER_UNAVAILABLE": (
        "Provider đang không sẵn sàng.",
        "Kiểm tra dịch vụ và mạng rồi thử lại.",
    ),
    "INVALID_PROVIDER_RESPONSE": (
        "Phản hồi provider không hợp lệ.",
        "Kiểm tra model và thử lại; không sử dụng kết quả này.",
    ),
    "SECRET_STORE_UNAVAILABLE": (
        "Không truy cập được kho credentials của hệ điều hành.",
        "Mở khóa Keychain/credential manager rồi thử lưu lại.",
    ),
    "CONSENT_REQUIRED": (
        "Chưa đồng ý gửi request AI.",
        "Xác nhận gửi request trước khi kiểm tra hoặc gọi AI.",
    ),
}


class ProviderError(Exception):
    def __init__(
        self,
        code,
        status=502,
        *,
        upstream_status=None,
        upstream_code=None,
        upstream_request_id=None,
        network_reason=None,
    ):
        self.upstream_status = upstream_status
        self.upstream_code = upstream_code
        self.upstream_request_id = upstream_request_id
        self.network_reason = network_reason
        self.code = code
        self.status = status
        super().__init__(code)

    def feedback(self):
        reason, solution = ERRORS[self.code]
        return {
            "code": self.code,
            "upstream_status": self.upstream_status,
            "upstream_code": self.upstream_code,
            "upstream_request_id": self.upstream_request_id,
            "network_reason": self.network_reason,
            "reason": reason,
            "impact": "Chưa xác nhận kết nối; dữ liệu dự án không thay đổi.",
            "solution": solution,
            "next_action": {"label": "Mở Cài đặt AI", "target": "/settings/ai"},
        }


@dataclass(repr=False)
class ProviderConfig:
    provider: str
    model: str
    api_key: str = field(repr=False)


class AIProviderAdapter(Protocol):
    def generate(self, config: ProviderConfig, prompt: str) -> dict: ...


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def upstream_error_fields(exc, secrets):
    """Retain machine codes only. Raw messages may echo keys or project input."""
    try:
        obj = json.loads(exc.read(100_000))
        err = obj.get("error", {})
        if not isinstance(err, dict):
            return None, None
        codes = [err.get("code"), err.get("status"), err.get("type")]
        details = err.get("details", [])
        if isinstance(details, list):
            codes = [d.get("reason") for d in details if isinstance(d, dict)] + codes
        clean = [
            safe_code(c)
            for c in codes
            if isinstance(c, str) and not any(secret and secret in c for secret in secrets)
        ]
        return next((c for c in clean if c), None), err.get("code")
    except (ValueError, AttributeError, OSError):
        return None, None


def network_kind(exc):
    reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    if isinstance(reason, TimeoutError):
        return "TIMEOUT"
    if isinstance(reason, socket.gaierror):
        return "DNS"
    if isinstance(reason, ssl.SSLCertVerificationError):
        return "TLS_CERTIFICATE"
    if isinstance(reason, ssl.SSLError):
        return "TLS"
    if isinstance(reason, ConnectionRefusedError):
        return "CONNECTION_REFUSED"
    if isinstance(reason, ConnectionResetError):
        return "CONNECTION_RESET"
    return "NETWORK"


def http_transport(url, headers, payload):
    provider = next((p for p, e in ENDPOINTS.items() if e == url), "unknown")
    # Only known endpoints may enter logs; never include arbitrary URL query strings.
    endpoint = ENDPOINTS.get(provider, "unknown")
    secrets = [
        v.removeprefix("Bearer ")
        for k, v in headers.items()
        if k.lower() in ("authorization", "x-goog-api-key", "x-api-key")
    ]
    start = time.monotonic()

    def fail(code, status, **diagnostic):
        emit(
            provider,
            endpoint,
            round((time.monotonic() - start) * 1000),
            status=diagnostic.get("upstream_status"),
            upstream_code=diagnostic.get("upstream_code"),
            upstream_request_id=diagnostic.get("upstream_request_id"),
            network_reason=diagnostic.get("network_reason"),
            code=code,
        )
        raise ProviderError(code, status, **diagnostic) from None

    request = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers=headers, method="POST"
    )
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=20) as response:
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                fail("INVALID_PROVIDER_RESPONSE", 502, upstream_status=response.status)
            try:
                obj = json.loads(raw)
            except (ValueError, TypeError):
                fail("INVALID_PROVIDER_RESPONSE", 502, upstream_status=response.status)
            emit(
                provider,
                endpoint,
                round((time.monotonic() - start) * 1000),
                status=response.status,
                upstream_request_id=safe_upstream_id(response.headers, secrets),
            )
            return obj
    except urllib.error.HTTPError as exc:
        upstream_code, _ = upstream_error_fields(exc, secrets)
        code = {
            400: "PROVIDER_BAD_REQUEST",
            401: "API_KEY_INVALID",
            402: "QUOTA_EXCEEDED",
            403: "PERMISSION_DENIED",
            404: "MODEL_NOT_FOUND",
            408: "CONNECTION_TIMEOUT",
            429: "RATE_LIMITED",
            503: "PROVIDER_UNAVAILABLE",
            504: "CONNECTION_TIMEOUT",
        }.get(exc.code, "PROVIDER_UNAVAILABLE" if exc.code >= 500 else "INVALID_PROVIDER_RESPONSE")
        status = exc.code if exc.code in (400, 401, 402, 403, 404, 429, 503, 504) else 502
        if exc.code in (400, 401, 403) and upstream_code in (
            "API_KEY_INVALID",
            "API_KEY_EXPIRED",
            "authentication",
            "invalid_api_key",
        ):
            code, status = "API_KEY_INVALID", 401
        if exc.code == 429 and upstream_code in ("quota_exceeded", "insufficient_quota"):
            code = "QUOTA_EXCEEDED"
        fail(
            code,
            status,
            upstream_status=exc.code,
            upstream_code=upstream_code,
            upstream_request_id=safe_upstream_id(exc.headers, secrets),
        )
    except (urllib.error.URLError, OSError) as exc:
        kind = network_kind(exc)
        fail(
            "CONNECTION_TIMEOUT" if kind == "TIMEOUT" else "NETWORK_ERROR",
            504 if kind == "TIMEOUT" else 503,
            network_reason=kind,
        )


class OpenAIAdapter:
    def __init__(self, transport=http_transport):
        self.transport = transport

    def generate(self, config, prompt):
        obj = self.transport(
            ENDPOINTS["openai"],
            {"Content-Type": "application/json", "Authorization": "Bearer " + config.api_key},
            {"model": config.model, "input": prompt, "store": False, "max_output_tokens": 512},
        )
        if obj.get("status") != "completed":
            raise ProviderError("INVALID_PROVIDER_RESPONSE")
        content = "".join(
            p.get("text", "")
            for item in obj.get("output", [])
            if item.get("type") == "message"
            for p in item.get("content", [])
            if p.get("type") == "output_text"
        )
        return {"content": content, "usage": obj.get("usage")}


class GeminiAdapter:
    def __init__(self, transport=http_transport):
        self.transport = transport

    def generate(self, config, prompt):
        obj = self.transport(
            ENDPOINTS["gemini"],
            {
                "Content-Type": "application/json",
                "x-goog-api-key": config.api_key,
                "Api-Revision": "2026-05-20",
            },
            {"model": config.model, "input": prompt, "store": False},
        )
        if obj.get("status") != "completed":
            raise ProviderError("INVALID_PROVIDER_RESPONSE")
        # Current Interactions returns model_output steps with content blocks.
        content = "".join(
            block.get("text", "")
            for step in obj.get("steps", [])
            if step.get("type") == "model_output"
            for block in step.get("content", [])
            if block.get("type") == "text"
        )
        return {"content": content, "usage": obj.get("usage")}


class ClaudeAdapter:
    def __init__(self, transport=http_transport):
        self.transport = transport

    def generate(self, config, prompt):
        obj = self.transport(
            ENDPOINTS["claude"],
            {
                "Content-Type": "application/json",
                "x-api-key": config.api_key,
                "anthropic-version": "2026-10-21",
            },
            {
                "model": config.model,
                "max_tokens": 512,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        if obj.get("type") != "message" or obj.get("stop_reason") != "end_turn":
            raise ProviderError("INVALID_PROVIDER_RESPONSE")
        content = "".join(
            p.get("text", "") for p in obj.get("content", []) if p.get("type") == "text"
        )
        return {"content": content, "usage": obj.get("usage")}


class AIProviderRegistry:
    def __init__(self, adapters=None):
        self.mode = os.getenv("AI_GATEWAY_MODE", "live")
        if self.mode not in ("live", "mock"):
            raise ValueError("AI_GATEWAY_MODE phải là live hoặc mock.")
        self.adapters = (
            adapters
            if adapters is not None
            else {"openai": OpenAIAdapter(), "gemini": GeminiAdapter(), "claude": ClaudeAdapter()}
        )

    def generate_structured_output(self, config, prompt, schema, *, consent=False):
        if not consent:
            raise ProviderError("CONSENT_REQUIRED", 400)
        if self.mode == "mock":
            raise ProviderError("MOCK_MODE", 400)
        start = time.monotonic()
        try:
            result = self.adapters[config.provider].generate(config, prompt)
            content = result["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError()
            parsed = json.loads(content)
            jsonschema.validate(parsed, schema)
        except ProviderError:
            raise
        except (AttributeError, KeyError, TypeError, ValueError, jsonschema.ValidationError):
            raise ProviderError("INVALID_PROVIDER_RESPONSE") from None
        return {
            "provider": config.provider,
            "model": config.model,
            "content": content,
            "data": parsed,
            "usage": result.get("usage"),
            "latency_ms": round((time.monotonic() - start) * 1000),
        }

    def test_connection(self, config, *, consent=False):
        result = self.generate_structured_output(
            config,
            'Connection check only. Reply with exactly the JSON object {"ok":true}.',
            {
                "type": "object",
                "properties": {"ok": {"const": True}},
                "required": ["ok"],
                "additionalProperties": False,
            },
            consent=consent,
        )
        return {k: result[k] for k in ("provider", "model", "latency_ms")}
