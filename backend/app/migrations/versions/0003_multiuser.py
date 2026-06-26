"""multi-user: users table + owner_id/visibility on ownable rows

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-25

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

visibility = postgresql.ENUM("private", "public", name="visibility", create_type=False)

_OWNABLE = ("scenarios", "sessions", "study_notes")


def upgrade() -> None:
    visibility.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("sub", sa.String(255), nullable=False, unique=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("picture", sa.Text(), nullable=True),
    )
    op.create_index("ix_users_sub", "users", ["sub"])
    op.create_index("ix_users_email", "users", ["email"])

    for table in _OWNABLE:
        op.add_column(
            table,
            sa.Column(
                "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
            ),
        )
        op.add_column(
            table,
            sa.Column("visibility", visibility, nullable=False, server_default="private"),
        )
        op.create_index(f"ix_{table}_user_id", table, ["user_id"])


def downgrade() -> None:
    for table in _OWNABLE:
        op.drop_index(f"ix_{table}_user_id", table_name=table)
        op.drop_column(table, "visibility")
        op.drop_column(table, "user_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_sub", table_name="users")
    op.drop_table("users")
    visibility.drop(op.get_bind(), checkfirst=True)
