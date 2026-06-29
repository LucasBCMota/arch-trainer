"""track running_since for stale-job reclaim

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-29

"""
import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

_TABLES = ("scenarios", "sessions", "study_notes")


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(table, sa.Column("running_since", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    for table in _TABLES:
        op.drop_column(table, "running_since")
