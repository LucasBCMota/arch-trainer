"""pattern_reviews for smart review

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-01

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pattern_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("pattern_name", sa.Text(), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("user_id", "pattern_name", name="uq_pattern_review"),
    )
    op.create_index("ix_pattern_reviews_user_id", "pattern_reviews", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_pattern_reviews_user_id", table_name="pattern_reviews")
    op.drop_table("pattern_reviews")
