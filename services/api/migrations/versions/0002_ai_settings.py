"""AI provider metadata; credentials live in the OS credential manager."""

import sqlalchemy as sa
from alembic import op

revision = "0002_ai_settings"
down_revision = "0001_m0_scaffold"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_settings",
        sa.Column("provider", sa.String(20), primary_key=True),
        sa.Column("model", sa.String(160), nullable=False),
        sa.Column("secret_ref", sa.String(36), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("tested_at", sa.String(40)),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("error_code", sa.String(40)),
        sa.Column("revision", sa.Integer(), nullable=False),
    )


def downgrade():
    op.drop_table("ai_settings")
