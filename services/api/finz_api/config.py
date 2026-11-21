"""Local configuration. No credentials or external clients are used in M0."""

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env", override=False)


def database_url() -> str:
    value = os.getenv("DATABASE_URL", "sqlite:///./data/finz_m0.sqlite3")
    if not value.startswith("sqlite:///"):
        raise ValueError("M0 chỉ hỗ trợ cơ sở dữ liệu SQLite local.")
    path = value.removeprefix("sqlite:///")
    if path != ":memory:" and not Path(path).is_absolute():
        path = str(REPO_ROOT / path)
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    return "sqlite:///" + path


def cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    return [part.strip() for part in raw.split(",") if part.strip()]


def validate_mock_mode() -> None:
    if os.getenv("LLM_PROVIDER", "mock") != "mock":
        raise ValueError("M0 chỉ hỗ trợ LLM_PROVIDER=mock, không có API AI thực.")
