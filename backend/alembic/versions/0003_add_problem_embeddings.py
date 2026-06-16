"""add problem embeddings

Revision ID: 0003_add_problem_embeddings
Revises: 0002_create_board_comments
Create Date: 2026-06-15
"""

from typing import Sequence, Union

from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa


revision: str = "0003_add_problem_embeddings"
down_revision: Union[str, None] = "0002_create_board_comments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "problem_embeddings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("embedding_model", sa.String(length=100), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], name="fk_problem_embeddings_problem_id_problems", ondelete="CASCADE"),
        sa.UniqueConstraint("problem_id", name="uq_problem_embeddings_problem_id"),
    )
    op.create_index("ix_problem_embeddings_problem_id", "problem_embeddings", ["problem_id"])


def downgrade() -> None:
    op.drop_index("ix_problem_embeddings_problem_id", table_name="problem_embeddings")
    op.drop_table("problem_embeddings")
    op.execute("DROP EXTENSION IF EXISTS vector")
