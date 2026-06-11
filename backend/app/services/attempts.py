from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.attempt import Attempt
from backend.app.models.board_post import BoardPost
from backend.app.models.problem import Problem
from backend.app.models.user import User
from backend.app.models.user_daily import UserDaily


def submit_attempt(
    db: Session,
    user: User,
    problem_id: int,
    selected_index: int,
    reasoning: str,
    today: date,
) -> Attempt:
    problem = db.get(Problem, problem_id)
    if not problem or problem.answer_index is None:
        raise LookupError("Problem not found or not answerable")

    daily = db.execute(
        select(UserDaily).where(
            UserDaily.user_id == user.id,
            UserDaily.problem_id == problem_id,
            UserDaily.assigned_date == today,
        )
    ).scalar_one_or_none()
    is_daily = daily is not None
    is_correct = selected_index == problem.answer_index

    attempt = Attempt(
        user_id=user.id,
        problem_id=problem.id,
        selected_index=selected_index,
        is_correct=is_correct,
        reasoning=reasoning,
        is_daily=is_daily,
    )
    db.add(attempt)

    if is_daily and daily:
        daily.completed = True
        update_streak(user, today)

    existing_post = db.execute(
        select(BoardPost).where(BoardPost.user_id == user.id, BoardPost.problem_id == problem.id)
    ).scalar_one_or_none()
    if not existing_post:
        db.add(
            BoardPost(
                user_id=user.id,
                problem_id=problem.id,
                content=reasoning,
                selected_index=selected_index,
                is_correct=is_correct,
            )
        )

    db.commit()
    db.refresh(attempt)
    return attempt


def update_streak(user: User, today: date) -> None:
    yesterday = today - timedelta(days=1)
    if user.last_completed_date == today:
        return
    if user.last_completed_date == yesterday:
        user.current_streak += 1
    else:
        user.current_streak = 1
    user.longest_streak = max(user.longest_streak, user.current_streak)
    user.last_completed_date = today
