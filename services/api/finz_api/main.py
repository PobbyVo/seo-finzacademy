from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from .config import cors_origins, database_url, validate_mock_mode
from .db import make_engine, make_sessions
from .errors import AppError, register_handlers
from .fixtures import demo_topics
from .repository import create_project, get_project, list_projects, load_demo
from .schemas import DemoLoad, ProjectCreate, ProjectList, ProjectResponse, TopicList


def create_app(url=None) -> FastAPI:
    validate_mock_mode()
    app = FastAPI(title="FINZ SEO Assistant — M0 DEMO", version="0.1.0")
    engine = make_engine(url or database_url())
    sessions = make_sessions(engine)
    app.state.engine = engine
    app.state.sessions = sessions
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        expose_headers=["X-Request-ID"],
    )

    @app.middleware("http")
    async def request_id(request: Request, call_next):
        request.state.request_id = str(uuid4())
        result = await call_next(request)
        result.headers["X-Request-ID"] = request.state.request_id
        return result

    register_handlers(app)

    def session_dependency():
        with sessions() as session:
            yield session

    @app.get("/health")
    @app.get("/api/v1/health")
    def health():
        required_tables = {"projects", "project_snapshots", "audit_events", "alembic_version"}
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            if not required_tables.issubset(inspect(connection).get_table_names()):
                raise AppError(
                    503,
                    "DATABASE_NOT_MIGRATED",
                    "Cơ sở dữ liệu chưa được khởi tạo.",
                    "Chạy alembic upgrade head trong services/api rồi thử lại.",
                )
        return {"status": "ok", "mode": "DEMO", "database": "ok", "api_version": "v1"}

    @app.get("/api/v1/projects", response_model=ProjectList)
    def projects(session=Depends(session_dependency)):
        return {"projects": list_projects(session)}

    @app.post("/api/v1/projects", response_model=ProjectResponse, status_code=201)
    def project_create(body: ProjectCreate, session=Depends(session_dependency)):
        return create_project(session, body.name)

    @app.get("/api/v1/projects/{project_id}", response_model=ProjectResponse)
    def project_detail(project_id: str, session=Depends(session_dependency)):
        return get_project(session, project_id)

    @app.get("/api/v1/demo/topics", response_model=TopicList)
    def topics():
        return {"topics": demo_topics()}

    @app.post("/api/v1/projects/{project_id}/demo", response_model=ProjectResponse)
    def project_demo(project_id: str, body: DemoLoad, session=Depends(session_dependency)):
        return load_demo(session, project_id, body.topic_code)

    return app


app = create_app()
