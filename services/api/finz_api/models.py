from sqlalchemy import JSON, Column, ForeignKey, Integer, String, UniqueConstraint

from .db import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True)
    name = Column(String(120), nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT")
    mode = Column(String(20), nullable=False, default="DEMO")
    version = Column(Integer, nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(String(40), nullable=False)
    updated_at = Column(String(40), nullable=False)


class ProjectSnapshot(Base):
    __tablename__ = "project_snapshots"
    __table_args__ = (UniqueConstraint("project_id", "version"),)

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(String(40), nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    snapshot_id = Column(String(36), ForeignKey("project_snapshots.id"), nullable=False)
    event_type = Column(String(40), nullable=False)
    actor = Column(String(20), nullable=False)
    details = Column(JSON, nullable=False)
    source_ref_ids = Column(JSON, nullable=False)
    created_at = Column(String(40), nullable=False)
