"""Allowlisted AI diagnostics. Never serialize exceptions, headers, prompts or credentials."""

import json
import logging
import os
from contextvars import ContextVar
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler

REQUEST_ID = ContextVar("ai_request_id", default=None)
LOGGER = logging.getLogger("finz.ai")
LOGGER.setLevel(logging.INFO)
SAFE_CODES = frozenset(
    """invalid_request failed_precondition parameter_unknown authentication
payment_required permission_denied not_found model_not_found rate_limit_exceeded quota_exceeded
insufficient_quota too_many_requests api_error service_unavailable deadline_exceeded
INVALID_ARGUMENT UNAUTHENTICATED PERMISSION_DENIED NOT_FOUND RESOURCE_EXHAUSTED UNAVAILABLE
INTERNAL DEADLINE_EXCEEDED API_KEY_INVALID API_KEY_EXPIRED API_KEY_SERVICE_BLOCKED
API_KEY_HTTP_REFERRER_BLOCKED API_KEY_IP_ADDRESS_BLOCKED API_KEY_ANDROID_APP_BLOCKED
API_KEY_IOS_APP_BLOCKED BILLING_DISABLED CONSUMER_INVALID ACCESS_TOKEN_EXPIRED
rate_limit_error rate_limit_exceeded invalid_api_key billing_error""".split()
)


def safe_code(value):
    return value if isinstance(value, str) and value in SAFE_CODES else None


def safe_upstream_id(headers, secrets):
    if not headers:
        return None
    for name in ("x-request-id", "x-goog-request-id", "request-id"):
        value = headers.get(name)
        if isinstance(value, str) and 0 < len(value) <= 128:
            if any(secret and secret in value for secret in secrets):
                return None
            if all(c.isascii() and (c.isalnum() or c in "-_:./") for c in value):
                return value
    return None


def emit(
    provider,
    endpoint,
    elapsed_ms,
    *,
    status=None,
    upstream_code=None,
    upstream_request_id=None,
    network_reason=None,
    code=None,
):
    record = {
        "event": "ai_upstream",
        "at": datetime.now(UTC).isoformat(),
        "request_id": REQUEST_ID.get(),
        "provider": provider,
        "method": "POST",
        "endpoint": endpoint,
        "upstream_status": status,
        "upstream_code": upstream_code,
        "upstream_request_id": upstream_request_id,
        "network_reason": network_reason,
        "code": code,
        "latency_ms": elapsed_ms,
    }
    LOGGER.info(json.dumps(record, ensure_ascii=True, separators=(",", ":")))


def file_handler(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Reject symlinks and make the local diagnostic file private.
    flags = os.O_CREAT | os.O_APPEND | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    os.fchmod(fd, 0o600)
    os.close(fd)
    handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    LOGGER.addHandler(handler)
    return handler
