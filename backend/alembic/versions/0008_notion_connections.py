"""create user notion connections

Revision ID: 0008_notion_connections
Revises: 0007_weekly_summary_exports
Create Date: 2026-06-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0008_notion_connections"
down_revision: Union[str, None] = "0007_weekly_summary_exports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_notion_connections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.String(length=100), nullable=False),
        sa.Column("workspace_name", sa.String(length=255), nullable=True),
        sa.Column("workspace_icon", sa.String(length=500), nullable=True),
        sa.Column("bot_id", sa.String(length=100), nullable=False),
        sa.Column("duplicated_template_id", sa.String(length=100), nullable=True),
        sa.Column("default_page_id", sa.String(length=100), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_notion_connections_user_id"),
    )
    op.create_index(op.f("ix_user_notion_connections_user_id"), "user_notion_connections", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_notion_connections_user_id"), table_name="user_notion_connections")
    op.drop_table("user_notion_connections")
