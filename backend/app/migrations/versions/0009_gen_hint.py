"""scenario gen_hint (harder-variation / focus-pattern seeding)

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-01

"""
import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scenarios", sa.Column("gen_hint", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("scenarios", "gen_hint")
