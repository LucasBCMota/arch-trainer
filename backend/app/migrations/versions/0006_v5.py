"""v5: queue study notes, structured exercises, diagrams

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-26

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

jobstatus = postgresql.ENUM(
    "pending", "running", "ready", "error", name="jobstatus", create_type=False
)
exercisetype = postgresql.ENUM("free_form", "structured", name="exercisetype", create_type=False)


def upgrade() -> None:
    exercisetype.create(op.get_bind(), checkfirst=True)

    # Part 1: study notes become async jobs
    op.add_column(
        "study_notes", sa.Column("status", jobstatus, nullable=False, server_default="ready")
    )
    op.add_column("study_notes", sa.Column("error", sa.Text(), nullable=True))
    op.create_index("ix_study_notes_status", "study_notes", ["status"])

    # Part 3: structured exercises
    op.add_column(
        "scenarios",
        sa.Column("exercise_type", exercisetype, nullable=False, server_default="free_form"),
    )
    op.add_column(
        "scenarios",
        sa.Column("response_template", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column("scenarios", sa.Column("context_diagram", sa.Text(), nullable=True))

    # Part 2: freehand drawing stored on the session (never judged)
    op.add_column("sessions", sa.Column("answer_freehand", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "answer_freehand")
    op.drop_column("scenarios", "context_diagram")
    op.drop_column("scenarios", "response_template")
    op.drop_column("scenarios", "exercise_type")
    op.drop_index("ix_study_notes_status", table_name="study_notes")
    op.drop_column("study_notes", "error")
    op.drop_column("study_notes", "status")
    exercisetype.drop(op.get_bind(), checkfirst=True)
