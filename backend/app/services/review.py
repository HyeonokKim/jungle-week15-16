from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.review_queue import ReviewQueue
from backend.app.models.user import User
from backend.app.models.user_setting import UserSetting


def get_due_review_item(db: Session, user: User, today: date) -> ReviewQueue | None:
    return db.execute(
        select(ReviewQueue)
        .where(
            ReviewQueue.user_id == user.id,
            ReviewQueue.due_date <= today,
            ReviewQueue.resolved.is_(False),
        )
        .order_by(ReviewQueue.due_date.asc(), ReviewQueue.id.asc())
        .limit(1)
    ).scalar_one_or_none()


def schedule_review_if_needed(
    db: Session,
    user: User,
    setting: UserSetting,
    problem_id: int,
    today: date,
) -> ReviewQueue | None:
    if setting.review_interval_days is None:
        return None

    due_date = today + timedelta(days=setting.review_interval_days)
    existing_item = db.execute(
        select(ReviewQueue).where(
            ReviewQueue.user_id == user.id,
            ReviewQueue.problem_id == problem_id,
            ReviewQueue.resolved.is_(False),
        )
    ).scalar_one_or_none()
    if existing_item:
        existing_item.due_date = due_date
        return existing_item

    review_item = ReviewQueue(
        user_id=user.id,
        problem_id=problem_id,
        due_date=due_date,
        resolved=False,
    )
    db.add(review_item)
    return review_item


def resolve_due_review_if_present(db: Session, user: User, problem_id: int, today: date) -> None:
    due_items = db.execute(
        select(ReviewQueue).where(
            ReviewQueue.user_id == user.id,
            ReviewQueue.problem_id == problem_id,
            ReviewQueue.due_date <= today,
            ReviewQueue.resolved.is_(False),
        )
    ).scalars()
    for due_item in due_items:
        due_item.resolved = True
