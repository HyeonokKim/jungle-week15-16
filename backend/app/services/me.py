from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.models.attempt import Attempt
from backend.app.models.board_post import BoardPost
from backend.app.models.problem import Problem
from backend.app.models.user import User


def get_my_posts(db: Session, user: User) -> list[BoardPost]:
    return list(
        db.execute(
            select(BoardPost)
            .where(BoardPost.user_id == user.id)
            .options(selectinload(BoardPost.problem).selectinload(Problem.exam))
            .order_by(BoardPost.created_at.desc(), BoardPost.id.desc())
        )
        .scalars()
        .all()
    )


def get_my_attempts(db: Session, user: User) -> list[Attempt]:
    return list(
        db.execute(
            select(Attempt)
            .where(Attempt.user_id == user.id)
            .options(selectinload(Attempt.problem))
            .order_by(Attempt.attempted_at.desc(), Attempt.id.desc())
        )
        .scalars()
        .all()
    )


def calculate_accuracy(correct_count: int, total_count: int) -> int:
    if total_count == 0:
        return 0
    return round((correct_count / total_count) * 100)


def summarize_area_accuracy(attempts: list[Attempt]) -> list[dict[str, int | str]]:
    totals: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "correct": 0})
    for attempt in attempts:
        area = attempt.problem.area.value
        totals[area]["total"] += 1
        if attempt.is_correct:
            totals[area]["correct"] += 1

    return [
        {
            "area": area,
            "total_attempts": values["total"],
            "correct_attempts": values["correct"],
            "accuracy_rate": calculate_accuracy(values["correct"], values["total"]),
        }
        for area, values in sorted(totals.items())
    ]
