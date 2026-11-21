from pathlib import Path

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select, text

from finz_api.db import make_engine
from finz_api.main import create_app
from finz_api.models import AuditEvent, ProjectSnapshot

from .conftest import migrate


def create(client, name="Dự án thử"):
    result = client.post("/api/v1/projects", json={"name": name})
    assert result.status_code == 201
    return result.json()


@pytest.mark.parametrize("route", ["/health", "/api/v1/health"])
def test_health_checks_database(client, route):
    response = client.get(route)
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "mode": "DEMO",
        "database": "ok",
        "api_version": "v1",
    }
    assert response.headers["x-request-id"]


def test_unmigrated_database_is_not_healthy(db_url):
    app = create_app(db_url)
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATABASE_NOT_MIGRATED"
    assert "alembic upgrade head" in response.json()["error"]["next_action_vi"]
    assert inspect(app.state.engine).get_table_names() == []
    app.state.engine.dispose()


def test_reading_demo_list_does_not_create_projects(client):
    assert client.get("/api/v1/projects").json() == {"projects": []}
    topics = client.get("/api/v1/demo/topics").json()["topics"]
    assert {row["topic_code"] for row in topics} == {"P01", "P02", "P08", "P25"}
    assert all(row["source_ref"].startswith("fixtures/") for row in topics)
    assert client.get("/api/v1/projects").json() == {"projects": []}


def test_create_empty_project_does_not_assign_demo(client):
    project = create(client, "  Nghiên cứu riêng  ")
    assert project["name"] == "Nghiên cứu riêng"
    assert project["topic"] is None
    assert project["content_codes"] == []
    assert project["source_keywords"] == []
    assert project["status"] == "DRAFT"
    assert project["mode"] == "DEMO"
    assert project["version"] == 1
    assert project["snapshot_id"]
    assert project["created_at"].endswith("Z")
    assert project["business_goal"] is None
    assert project["target_audience"] is None
    assert client.get(f"/api/v1/projects/{project['id']}").json() == project
    assert client.get("/api/v1/projects").json() == {"projects": [project]}


def test_explicit_demo_preserves_all_codes_and_null_metrics(client):
    project = create(client)
    response = client.post(f"/api/v1/projects/{project['id']}/demo", json={"topic_code": "P01"})
    assert response.status_code == 200
    demo = response.json()
    assert demo["topic"]["topic_code"] == "P01"
    assert len(demo["content_codes"]) == 2
    assert len(demo["source_keywords"]) == 3
    assert {row["content_code"] for row in demo["content_codes"]} == {"P01.1-①", "P01.2-②"}
    assert demo["version"] == 2
    assert demo["snapshot_id"] != project["snapshot_id"]
    for keyword in demo["source_keywords"]:
        assert keyword["funnel"] in {"TOFU", "MOFU", "BOFU"}
        assert all(keyword[field] is None for field in ("volume", "kd", "intent", "serp"))
        assert keyword["source_ref"].startswith("fixtures/")
    assert demo["status"] == "DRAFT"
    assert demo["business_goal"] is None
    assert demo["target_audience"] is None


def test_projects_persist_independently_after_app_restart(client, db_url):
    first = create(client, "Dự án A")
    second = create(client, "Dự án B")
    first = client.post(f"/api/v1/projects/{first['id']}/demo", json={"topic_code": "P01"}).json()
    second = client.post(f"/api/v1/projects/{second['id']}/demo", json={"topic_code": "P08"}).json()
    restarted = create_app(db_url)
    with TestClient(restarted) as other:
        assert other.get(f"/api/v1/projects/{first['id']}").json() == first
        assert other.get(f"/api/v1/projects/{second['id']}").json() == second
        assert len(other.get("/api/v1/projects").json()["projects"]) == 2
    restarted.state.engine.dispose()
    assert second["source_keywords"] == []  # Missing fixture rows are not invented.
    assert second["content_codes"] == []


def test_demo_cannot_overwrite_existing_project(client):
    project = create(client)
    url = f"/api/v1/projects/{project['id']}/demo"
    saved = client.post(url, json={"topic_code": "P01"}).json()
    response = client.post(url, json={"topic_code": "P08"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PROJECT_HAS_SOURCE"
    assert client.get(f"/api/v1/projects/{project['id']}").json() == saved


def test_demo_unknown_topic_does_not_mutate(client):
    project = create(client)
    response = client.post(f"/api/v1/projects/{project['id']}/demo", json={"topic_code": "Z42"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DEMO_TOPIC_NOT_FOUND"
    assert client.get(f"/api/v1/projects/{project['id']}").json() == project


@pytest.mark.parametrize(
    "body,field",
    [
        ({}, "name"),
        ({"name": " "}, "name"),
        ({"name": "x" * 121}, "name"),
        ({"name": 12}, "name"),
        ({"name": "Test", "status": "APPROVED"}, "status"),
    ],
)
def test_validation_is_structured_vietnamese(client, body, field):
    response = client.post("/api/v1/projects", json=body)
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "Dữ liệu không hợp lệ" in error["message_vi"]
    assert field in error["fields"]
    assert error["request_id"] == response.headers["x-request-id"]
    assert client.get("/api/v1/projects").json() == {"projects": []}


def test_malformed_json_has_structured_error(client):
    response = client.post(
        "/api/v1/projects", content="{", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_missing_project_and_route_errors(client):
    for path in ("/api/v1/projects/missing", "/api/v1/missing"):
        response = client.get(path)
        assert response.status_code == 404
        assert response.json()["error"]["request_id"]


def test_database_errors_return_actionable_response(client, app):
    with app.state.engine.connect() as connection:
        connection.execute(text("DROP TABLE audit_events"))
        connection.execute(text("DROP TABLE project_snapshots"))
        connection.execute(text("DROP TABLE projects"))
        connection.commit()
    response = client.get("/api/v1/projects")
    assert response.status_code == 503
    error = response.json()["error"]
    assert error["code"] == "DATABASE_UNAVAILABLE"
    assert "alembic upgrade head" in error["next_action_vi"]
    assert "SELECT" not in str(error)


def test_audit_and_snapshots_preserve_original_state(client, app):
    project = create(client)
    client.post(f"/api/v1/projects/{project['id']}/demo", json={"topic_code": "P01"})
    with app.state.sessions() as session:
        snapshots = session.scalars(select(ProjectSnapshot).order_by(ProjectSnapshot.version)).all()
        events = session.scalars(select(AuditEvent).order_by(AuditEvent.created_at)).all()
        assert len(snapshots) == 2
        assert snapshots[0].data["topic"] is None
        assert snapshots[1].data["topic"]["topic_code"] == "P01"
        assert [row.event_type for row in events] == ["PROJECT_SAVED", "DEMO_LOADED"]
        assert events[0].actor == events[1].actor == "USER"
        assert events[0].source_ref_ids == []
        assert len(events[1].source_ref_ids) == 6


def test_cors_allows_only_configured_web_origin(client):
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    response = client.options("/api/v1/projects", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    headers["Origin"] = "https://outside.example"
    assert client.options("/api/v1/projects", headers=headers).status_code == 400


def test_migrations_upgrade_idempotent_and_downgrade(db_url):
    config = migrate(db_url)
    migrate(db_url)
    engine = make_engine(db_url)
    with engine.connect() as connection:
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version")) == "0001_m0_scaffold"
        )
    assert {"projects", "project_snapshots", "audit_events"} <= set(
        inspect(engine).get_table_names()
    )
    command.downgrade(config, "base")
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}
    engine.dispose()


def test_reject_real_provider(monkeypatch, db_url):
    monkeypatch.setenv("LLM_PROVIDER", "cloud")
    with pytest.raises(ValueError, match="mock"):
        create_app(db_url)


def test_source_strings_are_not_hardcoded_in_domain_or_routes():
    for filename in ("repository.py", "main.py", "models.py", "schemas.py"):
        source = (Path(__file__).resolve().parents[1] / "finz_api" / filename).read_text()
        for forbidden in ("P01", "Lương", "Gross/Net", "gross net"):
            assert forbidden not in source
