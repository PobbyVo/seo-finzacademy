"""Metadata in SQLite, secrets exclusively in an OS credential backend."""

import os
import threading
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

import keyring
from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from sqlalchemy import Boolean, Column, Integer, String, select

from ..db import Base
from .gateway import ENDPOINTS, AIProviderRegistry, ProviderConfig, ProviderError

LOCK = threading.RLock()


class AISetting(Base):
    __tablename__ = "ai_settings"
    provider = Column(String(20), primary_key=True)
    model = Column(String(160), nullable=False)
    secret_ref = Column(String(36), nullable=False)
    active = Column(Boolean, nullable=False)
    status = Column(String(32), nullable=False)
    tested_at = Column(String(40), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    error_code = Column(String(40), nullable=True)
    revision = Column(Integer, nullable=False)


class SettingsInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    provider: Literal["openai", "gemini", "claude"]
    model: str = Field(min_length=1, max_length=160, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")
    api_key: SecretStr | None = Field(default=None, exclude=True)


class TestInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    consent: bool = False


class SettingsMetadata(BaseModel):
    provider: str
    model: str
    endpoint: str
    has_key: bool
    active: bool
    status: str
    tested_at: str | None
    latency_ms: int | None
    error_code: str | None


class SettingsResponse(BaseModel):
    gateway_mode: Literal["live", "mock"]
    active_provider: str | None
    configs: list[SettingsMetadata]
    endpoints: dict[str, str]


class OSSecretStore:
    def backend(self):
        backend = keyring.get_keyring()
        # Refuse file-based/plaintext third-party fallbacks and fail closed on headless hosts.
        name = type(backend).__module__
        if not name.startswith(
            (
                "keyring.backends.macOS",
                "keyring.backends.Windows",
                "keyring.backends.SecretService",
                "keyring.backends.kwallet",
            )
        ):
            raise ProviderError("SECRET_STORE_UNAVAILABLE", 503)
        return backend

    def get(self, ref):
        try:
            return self.backend().get_password("finz-seo-assistant", ref)
        except ProviderError:
            raise
        except Exception:
            raise ProviderError("SECRET_STORE_UNAVAILABLE", 503) from None

    def set(self, ref, key):
        try:
            self.backend().set_password("finz-seo-assistant", ref, key)
        except ProviderError:
            raise
        except Exception:
            raise ProviderError("SECRET_STORE_UNAVAILABLE", 503) from None

    def delete(self, ref):
        try:
            backend = self.backend()
            if backend.get_password("finz-seo-assistant", ref) is not None:
                backend.delete_password("finz-seo-assistant", ref)
        except ProviderError:
            raise
        except Exception:
            raise ProviderError("SECRET_STORE_UNAVAILABLE", 503) from None


def metadata(row):
    return dict(
        provider=row.provider,
        model=row.model,
        endpoint=ENDPOINTS[row.provider],
        has_key=bool(row.secret_ref),
        active=row.active,
        status=row.status,
        tested_at=row.tested_at,
        latency_ms=row.latency_ms,
        error_code=row.error_code,
    )


def read_settings(session):
    rows = session.scalars(select(AISetting).order_by(AISetting.provider)).all()
    return {
        "gateway_mode": os.getenv("AI_GATEWAY_MODE", "live"),
        "active_provider": next((r.provider for r in rows if r.active), None),
        "configs": [metadata(r) for r in rows],
        "endpoints": ENDPOINTS,
    }


def save_settings(session, body, secrets):
    with LOCK:
        row = session.get(AISetting, body.provider)
        old_ref = row.secret_ref if row else None
        key = body.api_key.get_secret_value() if body.api_key else None
        if key is not None and (not key.strip() or len(key) > 4096 or "\n" in key or "\r" in key):
            raise ProviderError("API_KEY_INVALID", 401)
        if not old_ref and not key:
            raise ProviderError("AI_NOT_CONFIGURED", 400)
        ref = str(uuid4()) if key else old_ref
        if key:
            secrets.set(ref, key)
        try:
            for existing in session.scalars(select(AISetting)).all():
                existing.active = False
            if row is None:
                row = AISetting(provider=body.provider, revision=0)
                session.add(row)
            row.model = body.model
            row.secret_ref = ref
            row.active = True
            row.status = "NOT_TESTED"
            row.tested_at = None
            row.latency_ms = None
            row.error_code = None
            row.revision += 1
            session.commit()
        except Exception:
            session.rollback()
            if key:
                secrets.delete(ref)
            raise
        if key and old_ref:
            secrets.delete(old_ref)
        return read_settings(session)


def selected_config(session, secrets, *, require_connected=True):
    row = session.scalar(select(AISetting).where(AISetting.active.is_(True)))
    if row is None or (require_connected and row.status != "CONNECTED"):
        raise ProviderError("AI_NOT_CONFIGURED", 400)
    key = secrets.get(row.secret_ref)
    if not key:
        raise ProviderError("AI_NOT_CONFIGURED", 400)
    return row, ProviderConfig(row.provider, row.model, key)


def generate_for_task(session, secrets, registry, task, prompt, schema, *, consent=False):
    """Shared entrypoint for Topic Analyst/SEO Critic; caller supplies its validated schema."""
    if task not in ("topic_analyst", "seo_critic"):
        raise ValueError("Nhiệm vụ AI không được hỗ trợ.")
    _, config = selected_config(session, secrets)
    return registry.generate_structured_output(config, prompt, schema, consent=consent)


def register_settings(app, session_dependency, secrets=None, registry=None):
    app.state.ai_secrets = secrets if secrets is not None else OSSecretStore()
    app.state.ai_registry = registry if registry is not None else AIProviderRegistry()

    @app.get("/api/v1/settings/ai", response_model=SettingsResponse)
    def get_settings(request: Request):
        with app.state.sessions() as session:
            return read_settings(session)

    @app.put("/api/v1/settings/ai", response_model=SettingsResponse)
    def put_settings(body: SettingsInput):
        with app.state.sessions() as session:
            return save_settings(session, body, app.state.ai_secrets)

    @app.post("/api/v1/settings/ai/test", response_model=SettingsResponse)
    def test_settings(body: TestInput):
        if not body.consent:
            raise ProviderError("CONSENT_REQUIRED", 400)
        with LOCK, app.state.sessions() as session:
            row = session.scalar(select(AISetting).where(AISetting.active.is_(True)))
            if row is None:
                raise ProviderError("AI_NOT_CONFIGURED", 400)
            try:
                _, config = selected_config(session, app.state.ai_secrets, require_connected=False)
                result = app.state.ai_registry.test_connection(config, consent=True)
                row.status = "CONNECTED"
                row.latency_ms = result["latency_ms"]
                row.error_code = None
            except ProviderError as exc:
                row.status = "ERROR"
                row.latency_ms = None
                row.error_code = exc.code
                row.tested_at = datetime.now(UTC).isoformat()
                session.commit()
                raise
            row.tested_at = datetime.now(UTC).isoformat()
            session.commit()
            return read_settings(session)

    @app.delete("/api/v1/settings/ai/{provider}", response_model=SettingsResponse)
    def delete_settings(provider: Literal["openai", "gemini", "claude"]):
        with LOCK, app.state.sessions() as session:
            row = session.get(AISetting, provider)
            if row:
                app.state.ai_secrets.delete(row.secret_ref)
                session.delete(row)
                session.commit()
            return read_settings(session)
