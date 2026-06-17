"""add problem type

Revision ID: 0005_add_problem_type
Revises: 0004_add_ai_explanations
Create Date: 2026-06-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0005_add_problem_type"
down_revision: Union[str, None] = "0004_add_ai_explanations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


problem_type = postgresql.ENUM(
    "main_claim",
    "detail_matching",
    "inference",
    "structure_analysis",
    "conditional_reasoning",
    "strengthen_weaken",
    "error_identification",
    "principle_application",
    "data_interpretation",
    name="problem_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    problem_type.create(bind, checkfirst=True)
    op.add_column("problems", sa.Column("problem_type", problem_type, nullable=True))
    op.create_index("ix_problems_problem_type", "problems", ["problem_type"])


def downgrade() -> None:
    op.drop_index("ix_problems_problem_type", table_name="problems")
    op.drop_column("problems", "problem_type")
    bind = op.get_bind()
    problem_type.drop(bind, checkfirst=True)
