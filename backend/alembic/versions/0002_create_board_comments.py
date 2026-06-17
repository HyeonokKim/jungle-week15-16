"""create board comments

Revision ID: 0002_create_board_comments
Revises: 0001_create_initial_schema
Create Date: 2026-06-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_create_board_comments"
down_revision: Union[str, None] = "0001_create_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "board_comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["board_posts.id"], name="fk_board_comments_post_id_board_posts", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_board_comments_user_id_users", ondelete="CASCADE"),
    )
    op.create_index("ix_board_comments_post_id", "board_comments", ["post_id"])
    op.create_index("ix_board_comments_user_id", "board_comments", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_board_comments_user_id", table_name="board_comments")
    op.drop_index("ix_board_comments_post_id", table_name="board_comments")
    op.drop_table("board_comments")
