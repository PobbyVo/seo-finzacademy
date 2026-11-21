from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select, update

from .errors import AppError
from .fixtures import demo_payload
from .models import AuditEvent, Project, ProjectSnapshot


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def not_found() -> AppError:
    return AppError(
        404, "PROJECT_NOT_FOUND", "Không tìm thấy dự án.", "Chọn lại dự án trong danh sách."
    )


def serialize(project: Project, snapshot_id: str) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "status": project.status,
        "mode": project.mode,
        "version": project.version,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "snapshot_id": snapshot_id,
        **project.data,
    }


def get_project(session, project_id: str) -> dict:
    project = session.get(Project, project_id)
    if project is None:
        raise not_found()
    snapshot = session.scalar(
        select(ProjectSnapshot).where(
            ProjectSnapshot.project_id == project_id, ProjectSnapshot.version == project.version
        )
    )
    return serialize(project, snapshot.id)


def list_projects(session) -> list[dict]:
    projects = session.scalars(
        select(Project).order_by(Project.created_at.desc(), Project.id)
    ).all()
    return [get_project(session, project.id) for project in projects]


def add_snapshot(session, project: Project, event_type: str, source_refs: list[str]) -> str:
    snapshot_id = str(uuid4())
    data = serialize(project, snapshot_id)
    session.add(
        ProjectSnapshot(
            id=snapshot_id,
            project_id=project.id,
            version=project.version,
            data=data,
            created_at=project.updated_at,
        )
    )
    session.flush()
    session.add(
        AuditEvent(
            id=str(uuid4()),
            project_id=project.id,
            snapshot_id=snapshot_id,
            event_type=event_type,
            actor="USER",
            details={"version": project.version},
            source_ref_ids=source_refs,
            created_at=project.updated_at,
        )
    )
    return snapshot_id


def create_project(session, name: str) -> dict:
    timestamp = now()
    project = Project(
        id=str(uuid4()),
        name=name,
        status="DRAFT",
        mode="DEMO",
        version=1,
        created_at=timestamp,
        updated_at=timestamp,
        data={
            "topic": None,
            "content_codes": [],
            "source_keywords": [],
            "business_goal": None,
            "target_audience": None,
        },
    )
    session.add(project)
    session.flush()
    snapshot_id = add_snapshot(session, project, "PROJECT_SAVED", [])
    session.commit()
    return serialize(project, snapshot_id)


def load_demo(session, project_id: str, topic_code: str) -> dict:
    project = session.get(Project, project_id)
    if project is None:
        raise not_found()
    if project.data["topic"] is not None:
        raise AppError(
            409,
            "PROJECT_HAS_SOURCE",
            "Dự án đã có dữ liệu nguồn.",
            "Tạo dự án trống khác để nạp demo; dữ liệu hiện tại được giữ nguyên.",
        )
    try:
        payload = demo_payload(topic_code)
    except KeyError as exc:
        raise AppError(
            404,
            "DEMO_TOPIC_NOT_FOUND",
            "Không tìm thấy topic demo.",
            "Chọn một topic có trong danh sách demo.",
            ["topic_code"],
        ) from exc
    previous_version = project.version
    timestamp = now()
    # Optimistic update prevents two concurrent demo loads from overwriting each other.
    result = session.execute(
        update(Project)
        .where(Project.id == project_id, Project.version == previous_version)
        .values(data=payload, version=previous_version + 1, updated_at=timestamp)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        session.rollback()
        raise AppError(
            409,
            "PROJECT_VERSION_CONFLICT",
            "Dự án đã được cập nhật ở nơi khác.",
            "Tải lại dự án để xem dữ liệu mới nhất.",
        )
    session.refresh(project)
    refs = [payload["topic"]["source_ref"]]
    refs.extend(row["source_ref"] for row in payload["content_codes"])
    refs.extend(row["source_ref"] for row in payload["source_keywords"])
    snapshot_id = add_snapshot(session, project, "DEMO_LOADED", refs)
    session.commit()
    return serialize(project, snapshot_id)
