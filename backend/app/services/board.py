from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.models.attempt import Attempt
from backend.app.models.board_post import BoardPost
from backend.app.models.problem import Problem
from backend.app.models.user import User


def get_problem_board(db: Session, user: User, problem_id: int) -> tuple[Problem, list[BoardPost]]:
    problem = db.execute(
        select(Problem)
        .where(Problem.id == problem_id)
        .options(selectinload(Problem.exam))
    ).scalar_one_or_none()
    if not problem:
        raise LookupError("Problem not found")

    has_attempt = db.execute(
        select(Attempt.id).where(Attempt.user_id == user.id, Attempt.problem_id == problem_id).limit(1)
    ).scalar_one_or_none()
    if not has_attempt:
        raise PermissionError("Submit this problem before reading the board")

    posts = db.execute(
        select(BoardPost)
        .where(BoardPost.problem_id == problem_id)
        .options(selectinload(BoardPost.user))
        .order_by(BoardPost.created_at.asc(), BoardPost.id.asc())
    ).scalars().all()
    return problem, list(posts)
