"""study notes + scenario pinning

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-19

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

studynotekind = postgresql.ENUM(
    "deep_dive", "cheat_sheet", name="studynotekind", create_type=False
)


def upgrade() -> None:
    studynotekind.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "study_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("kind", studynotekind, nullable=False),
        sa.Column("topic", sa.Text(), nullable=False),
        sa.Column("content_md", sa.Text(), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default="false"),
    )

    op.add_column(
        "scenarios",
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("scenarios", "pinned")
    op.drop_table("study_notes")
    studynotekind.drop(op.get_bind(), checkfirst=True)
