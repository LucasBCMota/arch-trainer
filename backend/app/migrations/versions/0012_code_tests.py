"""runnable algorithm exercises: code_entry + code_tests

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-01

"""
import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scenarios", sa.Column("code_entry", sa.Text(), nullable=True))
    op.add_column("scenarios", sa.Column("code_tests", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("scenarios", "code_tests")
    op.drop_column("scenarios", "code_entry")
