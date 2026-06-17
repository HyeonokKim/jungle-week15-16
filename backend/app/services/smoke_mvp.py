from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select

from backend.app.core.database import SessionLocal
from backend.app.models.review_queue import ReviewQueue
from backend.app.models.user import User
from backend.app.services.attempts import submit_attempt
from backend.app.services.board import get_problem_board
from backend.app.services.daily import get_or_assign_daily_problem, select_next_practice_problem
from backend.app.services.dev_user import get_or_create_dev_user
from backend.app.services.me import get_my_attempts, get_my_posts
from backend.app.services.settings import get_or_create_user_settings


SMOKE_USER_ID = 9201


def run_smoke() -> dict[str, int | str | bool]:
    with SessionLocal() as db:
        existing_user = db.get(User, SMOKE_USER_ID)
        if existing_user:
            db.delete(existing_user)
            db.commit()

        user = get_or_create_dev_user(db, SMOKE_USER_ID)
        try:
            setting = get_or_create_user_settings(db, user)
            setting.review_interval_days = 3
            db.commit()

            today = date.today()
            daily = get_or_assign_daily_problem(db, user, today)
            answer_index = daily.problem.answer_index
            if answer_index is None:
                raise AssertionError("daily problem must have answer_index")

            wrong_index = 1 if answer_index != 1 else 2
            attempt = submit_attempt(
                db=db,
                user=user,
                problem_id=daily.problem_id,
                selected_index=wrong_index,
                reasoning="MVP smoke: 오답 복습 큐 생성 확인",
                today=today,
            )
            assert attempt.is_daily is True
            assert attempt.is_correct is False

            _, posts = get_problem_board(db, user, daily.problem_id)
            assert any(post.user_id == user.id for post in posts)
            assert len(get_my_posts(db, user)) == 1
            assert len(get_my_attempts(db, user)) == 1

            practice_problem = select_next_practice_problem(db, user, today)
            assert practice_problem.id != daily.problem_id

            due_date = today + timedelta(days=3)
            review_item = db.execute(
                select(ReviewQueue).where(
                    ReviewQueue.user_id == user.id,
                    ReviewQueue.problem_id == daily.problem_id,
                    ReviewQueue.resolved.is_(False),
                )
            ).scalar_one()
            assert review_item.due_date == due_date

            review_daily = get_or_assign_daily_problem(db, user, due_date)
            assert review_daily.problem_id == daily.problem_id

            review_attempt = submit_attempt(
                db=db,
                user=user,
                problem_id=review_daily.problem_id,
                selected_index=answer_index,
                reasoning="MVP smoke: 복습 문제 해결 확인",
                today=due_date,
            )
            assert review_attempt.is_correct is True

            unresolved_review_count = len(
                db.execute(
                    select(ReviewQueue).where(
                        ReviewQueue.user_id == user.id,
                        ReviewQueue.resolved.is_(False),
                    )
                )
                .scalars()
                .all()
            )
            assert unresolved_review_count == 0

            result = {
                "user_id": user.id,
                "daily_problem_id": daily.problem_id,
                "practice_problem_id": practice_problem.id,
                "review_due_date": due_date.isoformat(),
                "review_resolved": True,
            }

            return result
        finally:
            db.delete(user)
            db.commit()


if __name__ == "__main__":
    print(run_smoke())
