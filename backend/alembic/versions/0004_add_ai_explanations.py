"""add ai explanations

Revision ID: 0004_add_ai_explanations
Revises: 0003_add_problem_embeddings
Create Date: 2026-06-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0004_add_ai_explanations"
down_revision: Union[str, None] = "0003_add_problem_embeddings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_explanations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("final_explanation", sa.Text(), nullable=True),
        sa.Column("solution_summary", sa.Text(), nullable=True),
        sa.Column("user_reasoning_review", sa.Text(), nullable=True),
        sa.Column("wrong_choice_explanation", sa.Text(), nullable=True),
        sa.Column("confidence_level", sa.String(length=20), nullable=True),
        sa.Column("confidence_score", sa.Integer(), nullable=True),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("accepted_count", sa.Integer(), nullable=False),
        sa.Column("discarded_count", sa.Integer(), nullable=False),
        sa.Column("critic_passed", sa.Boolean(), nullable=True),
        sa.Column("critic_notes", sa.Text(), nullable=True),
        sa.Column("references_used", postgresql.JSONB(), nullable=False),
        sa.Column("candidate_summaries", postgresql.JSONB(), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"], name="fk_ai_explanations_attempt_id_attempts", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], name="fk_ai_explanations_problem_id_problems", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_ai_explanations_user_id_users", ondelete="CASCADE"),
        sa.UniqueConstraint("attempt_id", name="uq_ai_explanations_attempt_id"),
    )
    op.create_index("ix_ai_explanations_attempt_id", "ai_explanations", ["attempt_id"])
    op.create_index("ix_ai_explanations_problem_id", "ai_explanations", ["problem_id"])
    op.create_index("ix_ai_explanations_user_id", "ai_explanations", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_explanations_user_id", table_name="ai_explanations")
    op.drop_index("ix_ai_explanations_problem_id", table_name="ai_explanations")
    op.drop_index("ix_ai_explanations_attempt_id", table_name="ai_explanations")
    op.drop_table("ai_explanations")
