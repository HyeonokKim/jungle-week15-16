"""create initial schema

Revision ID: 0001_create_initial_schema
Revises: None
Create Date: 2026-06-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_create_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


problem_area = postgresql.ENUM(
    "reading_comprehension",
    "reasoning_argumentation",
    name="problem_area",
    create_type=False,
)
problem_scope = postgresql.ENUM(
    "all_random",
    "recent_3y",
    "recent_5y",
    name="problem_scope",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    problem_area.create(bind, checkfirst=True)
    problem_scope.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("nickname", sa.String(length=50), nullable=False),
        sa.Column("auth_provider", sa.String(length=50), nullable=False),
        sa.Column("provider_id", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("current_streak", sa.Integer(), nullable=False),
        sa.Column("longest_streak", sa.Integer(), nullable=False),
        sa.Column("last_completed_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("auth_provider", "provider_id", name="uq_users_auth_provider_provider_id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("nickname", name="uq_users_nickname"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_nickname", "users", ["nickname"])

    op.create_table(
        "exams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("round", sa.String(length=50), nullable=False),
        sa.Column("area", problem_area, nullable=False),
        sa.UniqueConstraint("year", "round", "area", name="uq_exams_year_round_area"),
    )
    op.create_index("ix_exams_area", "exams", ["area"])
    op.create_index("ix_exams_year", "exams", ["year"])

    op.create_table(
        "passages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_ref", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], name="fk_passages_exam_id_exams", ondelete="CASCADE"),
    )
    op.create_index("ix_passages_exam_id", "passages", ["exam_id"])

    op.create_table(
        "problems",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("passage_id", sa.Integer(), nullable=True),
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("answer_index", sa.Integer(), nullable=True),
        sa.Column("area", problem_area, nullable=False),
        sa.CheckConstraint("answer_index BETWEEN 1 AND 5", name="ck_problems_answer_index_between_1_and_5"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], name="fk_problems_exam_id_exams", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["passage_id"], ["passages.id"], name="fk_problems_passage_id_passages", ondelete="SET NULL"),
        sa.UniqueConstraint("exam_id", "number", name="uq_problems_exam_id_number"),
    )
    op.create_index("ix_problems_area", "problems", ["area"])
    op.create_index("ix_problems_exam_id", "problems", ["exam_id"])
    op.create_index("ix_problems_passage_id", "problems", ["passage_id"])

    op.create_table(
        "choices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], name="fk_choices_problem_id_problems", ondelete="CASCADE"),
        sa.UniqueConstraint("problem_id", "idx", name="uq_choices_problem_id_idx"),
    )
    op.create_index("ix_choices_problem_id", "choices", ["problem_id"])

    op.create_table(
        "attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("selected_index", sa.Integer(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("is_daily", sa.Boolean(), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("selected_index BETWEEN 1 AND 5", name="ck_attempts_selected_index_between_1_and_5"),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], name="fk_attempts_problem_id_problems", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_attempts_user_id_users", ondelete="CASCADE"),
    )
    op.create_index("ix_attempts_problem_id", "attempts", ["problem_id"])
    op.create_index("ix_attempts_user_id", "attempts", ["user_id"])

    op.create_table(
        "user_daily",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("assigned_date", sa.Date(), nullable=False),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], name="fk_user_daily_problem_id_problems", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_daily_user_id_users", ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "assigned_date", name="uq_user_daily_user_id_assigned_date"),
    )
    op.create_index("ix_user_daily_assigned_date", "user_daily", ["assigned_date"])
    op.create_index("ix_user_daily_problem_id", "user_daily", ["problem_id"])
    op.create_index("ix_user_daily_user_id", "user_daily", ["user_id"])

    op.create_table(
        "board_posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("selected_index", sa.Integer(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("selected_index BETWEEN 1 AND 5", name="ck_board_posts_selected_index_between_1_and_5"),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], name="fk_board_posts_problem_id_problems", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_board_posts_user_id_users", ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "problem_id", name="uq_board_posts_user_id_problem_id"),
    )
    op.create_index("ix_board_posts_problem_id", "board_posts", ["problem_id"])
    op.create_index("ix_board_posts_user_id", "board_posts", ["user_id"])

    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("problem_scope", problem_scope, nullable=False),
        sa.Column("timer_limit_sec", sa.Integer(), nullable=False),
        sa.Column("review_interval_days", sa.Integer(), nullable=True),
        sa.Column("weak_type", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("timer_limit_sec IN (120, 180, 240)", name="ck_user_settings_timer_limit_sec_allowed_values"),
        sa.CheckConstraint(
            "review_interval_days IS NULL OR review_interval_days IN (3, 5, 7)",
            name="ck_user_settings_review_interval_days_allowed_values",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_settings_user_id_users", ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_user_settings_user_id"),
    )
    op.create_index("ix_user_settings_user_id", "user_settings", ["user_id"])

    op.create_table(
        "review_queue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], name="fk_review_queue_problem_id_problems", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_review_queue_user_id_users", ondelete="CASCADE"),
    )
    op.create_index("ix_review_queue_due_date", "review_queue", ["due_date"])
    op.create_index("ix_review_queue_problem_id", "review_queue", ["problem_id"])
    op.create_index("ix_review_queue_user_id", "review_queue", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_review_queue_user_id", table_name="review_queue")
    op.drop_index("ix_review_queue_problem_id", table_name="review_queue")
    op.drop_index("ix_review_queue_due_date", table_name="review_queue")
    op.drop_table("review_queue")

    op.drop_index("ix_user_settings_user_id", table_name="user_settings")
    op.drop_table("user_settings")

    op.drop_index("ix_board_posts_user_id", table_name="board_posts")
    op.drop_index("ix_board_posts_problem_id", table_name="board_posts")
    op.drop_table("board_posts")

    op.drop_index("ix_user_daily_user_id", table_name="user_daily")
    op.drop_index("ix_user_daily_problem_id", table_name="user_daily")
    op.drop_index("ix_user_daily_assigned_date", table_name="user_daily")
    op.drop_table("user_daily")

    op.drop_index("ix_attempts_user_id", table_name="attempts")
    op.drop_index("ix_attempts_problem_id", table_name="attempts")
    op.drop_table("attempts")

    op.drop_index("ix_choices_problem_id", table_name="choices")
    op.drop_table("choices")

    op.drop_index("ix_problems_passage_id", table_name="problems")
    op.drop_index("ix_problems_exam_id", table_name="problems")
    op.drop_index("ix_problems_area", table_name="problems")
    op.drop_table("problems")

    op.drop_index("ix_passages_exam_id", table_name="passages")
    op.drop_table("passages")

    op.drop_index("ix_exams_year", table_name="exams")
    op.drop_index("ix_exams_area", table_name="exams")
    op.drop_table("exams")

    op.drop_index("ix_users_nickname", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    problem_scope.drop(bind, checkfirst=True)
    problem_area.drop(bind, checkfirst=True)
