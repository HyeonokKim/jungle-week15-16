"""add attempt solve duration

Revision ID: 0006_add_attempt_solve_duration
Revises: 0005_add_problem_type
Create Date: 2026-06-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_add_attempt_solve_duration"
down_revision: Union[str, None] = "0005_add_problem_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("attempts", sa.Column("solve_duration_sec", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("attempts", "solve_duration_sec")
