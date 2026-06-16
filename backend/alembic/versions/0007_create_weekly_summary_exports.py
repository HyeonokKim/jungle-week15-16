"""create weekly summary exports

Revision ID: 0007_create_weekly_summary_exports
Revises: 0006_add_attempt_solve_duration
Create Date: 2026-06-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0007_create_weekly_summary_exports"
down_revision: Union[str, None] = "0006_add_attempt_solve_duration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "weekly_summary_exports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("week_end", sa.Date(), nullable=False),
        sa.Column("destination", sa.String(length=30), nullable=False),
        sa.Column("external_page_id", sa.String(length=100), nullable=False),
        sa.Column("external_url", sa.String(length=500), nullable=True),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "week_start", "destination", name="uq_weekly_summary_exports_user_week_destination"),
    )
    op.create_index(op.f("ix_weekly_summary_exports_user_id"), "weekly_summary_exports", ["user_id"], unique=False)
    op.create_index(op.f("ix_weekly_summary_exports_week_start"), "weekly_summary_exports", ["week_start"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_weekly_summary_exports_week_start"), table_name="weekly_summary_exports")
    op.drop_index(op.f("ix_weekly_summary_exports_user_id"), table_name="weekly_summary_exports")
    op.drop_table("weekly_summary_exports")
