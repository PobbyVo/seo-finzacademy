from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from finz_api.main import create_app

API_ROOT = Path(__file__).resolve().parents[1]


def migrate(url: str, revision="head") -> Config:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url)
    config.attributes["url_override"] = True
    command.upgrade(config, revision)
    return config


@pytest.fixture
def db_url(tmp_path):
    return f"sqlite:///{tmp_path / 'test.sqlite3'}"


@pytest.fixture
def app(db_url):
    migrate(db_url)
    application = create_app(db_url)
    yield application
    application.state.engine.dispose()


@pytest.fixture
def client(app):
    with TestClient(app) as result:
        yield result
