"""v6: language + algorithms exercise types

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-29

"""
import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # New enum values must be added outside a transaction on some PG versions.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE exercisetype ADD VALUE IF NOT EXISTS 'language'")
        op.execute("ALTER TYPE exercisetype ADD VALUE IF NOT EXISTS 'algorithms'")
    op.add_column("scenarios", sa.Column("language", sa.String(40), nullable=True))


def downgrade() -> None:
    # Postgres can't drop a single enum value; just drop the column.
    op.drop_column("scenarios", "language")
