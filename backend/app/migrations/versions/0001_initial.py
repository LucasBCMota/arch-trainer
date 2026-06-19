"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-19

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

difficulty = postgresql.ENUM(
    "feature", "platform", "principal", name="difficulty", create_type=False
)


def upgrade() -> None:
    difficulty.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "scenarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("difficulty", difficulty, nullable=False),
        sa.Column("focus_area", sa.String(64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("context", sa.Text(), nullable=False),
        sa.Column("problem", sa.Text(), nullable=False),
        sa.Column("constraints", postgresql.JSONB(), nullable=False),
        sa.Column("reference_solution", postgresql.JSONB(), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
    )

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("user_answer", sa.Text(), nullable=False),
        sa.Column("judgment", postgresql.JSONB(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
    )

    op.create_table(
        "pattern_gaps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("pattern_name", sa.Text(), nullable=False),
        sa.Column("what_they_described", sa.Text(), nullable=False),
    )
    op.create_index("ix_pattern_gaps_pattern_name", "pattern_gaps", ["pattern_name"])


def downgrade() -> None:
    op.drop_index("ix_pattern_gaps_pattern_name", table_name="pattern_gaps")
    op.drop_table("pattern_gaps")
    op.drop_table("sessions")
    op.drop_table("scenarios")
    difficulty.drop(op.get_bind(), checkfirst=True)
