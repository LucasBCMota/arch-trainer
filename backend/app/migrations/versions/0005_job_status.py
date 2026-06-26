"""async job status on scenarios + sessions

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-26

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

jobstatus = postgresql.ENUM(
    "pending", "running", "ready", "error", name="jobstatus", create_type=False
)

_TABLES = ("scenarios", "sessions")


def upgrade() -> None:
    jobstatus.create(op.get_bind(), checkfirst=True)
    for table in _TABLES:
        # existing rows are complete -> default 'ready'
        op.add_column(
            table, sa.Column("status", jobstatus, nullable=False, server_default="ready")
        )
        op.add_column(table, sa.Column("error", sa.Text(), nullable=True))
        op.create_index(f"ix_{table}_status", table, ["status"])


def downgrade() -> None:
    for table in _TABLES:
        op.drop_index(f"ix_{table}_status", table_name=table)
        op.drop_column(table, "error")
        op.drop_column(table, "status")
    jobstatus.drop(op.get_bind(), checkfirst=True)
