from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.models.attempt import Attempt
from backend.app.models.board_comment import BoardComment
from backend.app.models.board_post import BoardPost
from backend.app.models.problem import Problem
from backend.app.models.review_queue import ReviewQueue
from backend.app.models.user import User
from backend.app.models.user_daily import UserDaily
from backend.app.services.weakness import refresh_user_weak_type


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
        .options(selectinload(BoardPost.user), selectinload(BoardPost.comments).selectinload(BoardComment.user))
        .order_by(BoardPost.created_at.asc(), BoardPost.id.asc())
    ).scalars().all()
    return problem, list(posts)


def create_board_comment(
    db: Session,
    user: User,
    problem_id: int,
    post_id: int,
    content: str,
) -> BoardComment:
    normalized_content = content.strip()
    if not normalized_content:
        raise ValueError("Comment content is required")

    post = db.execute(
        select(BoardPost)
        .where(BoardPost.id == post_id, BoardPost.problem_id == problem_id)
        .options(selectinload(BoardPost.user))
    ).scalar_one_or_none()
    if not post:
        raise LookupError("Board post not found")

    has_attempt = db.execute(
        select(Attempt.id).where(Attempt.user_id == user.id, Attempt.problem_id == problem_id).limit(1)
    ).scalar_one_or_none()
    if not has_attempt:
        raise PermissionError("Submit this problem before commenting on the board")

    comment = BoardComment(post_id=post.id, user_id=user.id, content=normalized_content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    comment.user = user
    return comment


def update_board_post(
    db: Session,
    user: User,
    problem_id: int,
    post_id: int,
    content: str,
) -> BoardPost:
    normalized_content = content.strip()
    if not normalized_content:
        raise ValueError("Post content is required")

    post = db.execute(
        select(BoardPost)
        .where(BoardPost.id == post_id, BoardPost.problem_id == problem_id)
        .options(selectinload(BoardPost.user), selectinload(BoardPost.comments).selectinload(BoardComment.user))
    ).scalar_one_or_none()
    if not post:
        raise LookupError("Board post not found")
    if post.user_id != user.id:
        raise PermissionError("You can edit only your own board post")

    post.content = normalized_content
    db.commit()
    db.refresh(post)
    post.user = user
    return post


def delete_user_problem_activity(db: Session, user: User, problem_id: int, post_id: int | None = None) -> None:
    post_statement = select(BoardPost).where(BoardPost.user_id == user.id, BoardPost.problem_id == problem_id)
    if post_id is not None:
        post_statement = post_statement.where(BoardPost.id == post_id)

    post = db.execute(post_statement).scalar_one_or_none()
    attempts = list(
        db.execute(
            select(Attempt).where(Attempt.user_id == user.id, Attempt.problem_id == problem_id)
        )
        .scalars()
        .all()
    )

    if post_id is not None and not post:
        existing_post = db.execute(
            select(BoardPost).where(BoardPost.id == post_id, BoardPost.problem_id == problem_id)
        ).scalar_one_or_none()
        if existing_post and existing_post.user_id != user.id:
            raise PermissionError("You can delete only your own board post")
        raise LookupError("Board post not found")
    if not post and not attempts:
        raise LookupError("Learning activity not found")

    daily_dates = {attempt.attempted_at.date() for attempt in attempts if attempt.is_daily}

    if post:
        db.delete(post)
    for attempt in attempts:
        db.delete(attempt)

    if daily_dates:
        daily_assignments = db.execute(
            select(UserDaily).where(
                UserDaily.user_id == user.id,
                UserDaily.problem_id == problem_id,
                UserDaily.assigned_date.in_(daily_dates),
            )
        ).scalars()
        for daily_assignment in daily_assignments:
            daily_assignment.completed = False

    review_items = db.execute(
        select(ReviewQueue).where(ReviewQueue.user_id == user.id, ReviewQueue.problem_id == problem_id)
    ).scalars()
    for review_item in review_items:
        db.delete(review_item)

    db.flush()
    recalculate_user_streak(db, user)
    refresh_user_weak_type(db, user)
    db.commit()


def recalculate_user_streak(db: Session, user: User) -> None:
    completed_dates = [
        completed_date
        for completed_date in db.execute(
            select(UserDaily.assigned_date)
            .where(UserDaily.user_id == user.id, UserDaily.completed.is_(True))
            .order_by(UserDaily.assigned_date.asc())
        ).scalars()
    ]

    if not completed_dates:
        user.current_streak = 0
        user.longest_streak = 0
        user.last_completed_date = None
        return

    completed_date_set = set(completed_dates)
    last_completed_date = max(completed_date_set)
    current_streak = 0
    cursor = last_completed_date
    while cursor in completed_date_set:
        current_streak += 1
        cursor -= timedelta(days=1)

    longest_streak = 0
    running_streak = 0
    previous_date: date | None = None
    for completed_date in sorted(completed_date_set):
        if previous_date is not None and completed_date == previous_date + timedelta(days=1):
            running_streak += 1
        else:
            running_streak = 1
        longest_streak = max(longest_streak, running_streak)
        previous_date = completed_date

    user.current_streak = current_streak
    user.longest_streak = longest_streak
    user.last_completed_date = last_completed_date


def delete_board_post(db: Session, user: User, problem_id: int, post_id: int) -> None:
    post = db.execute(
        select(BoardPost).where(BoardPost.id == post_id, BoardPost.problem_id == problem_id)
    ).scalar_one_or_none()
    if not post:
        raise LookupError("Board post not found")
    if post.user_id != user.id:
        raise PermissionError("You can delete only your own board post")

    delete_user_problem_activity(db, user, problem_id, post_id)
