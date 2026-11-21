"""M0 project, immutable snapshots and audit trail.

Revision ID: 0001_m0_scaffold
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_m0_scaffold"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.Column("updated_at", sa.String(40), nullable=False),
    )
    op.create_table(
        "project_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.UniqueConstraint("project_id", "version"),
    )
    op.create_index("ix_project_snapshots_project_id", "project_snapshots", ["project_id"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column(
            "snapshot_id", sa.String(36), sa.ForeignKey("project_snapshots.id"), nullable=False
        ),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("actor", sa.String(20), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("source_ref_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
    )
    op.create_index("ix_audit_events_project_id", "audit_events", ["project_id"])


def downgrade():
    op.drop_index("ix_audit_events_project_id", "audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_project_snapshots_project_id", "project_snapshots")
    op.drop_table("project_snapshots")
    op.drop_table("projects")
