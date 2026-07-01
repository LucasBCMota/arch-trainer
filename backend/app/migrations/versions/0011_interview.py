"""interview runs + sessions.run_id

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-01

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "interview_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("config", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
    )
    op.create_index("ix_interview_runs_user_id", "interview_runs", ["user_id"])
    op.add_column(
        "sessions",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interview_runs.id"), nullable=True),
    )
    op.create_index("ix_sessions_run_id", "sessions", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_sessions_run_id", table_name="sessions")
    op.drop_column("sessions", "run_id")
    op.drop_index("ix_interview_runs_user_id", table_name="interview_runs")
    op.drop_table("interview_runs")
