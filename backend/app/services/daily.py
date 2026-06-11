from datetime import date

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from backend.app.models.attempt import Attempt
from backend.app.models.enums import ProblemArea
from backend.app.models.exam import Exam
from backend.app.models.problem import Problem
from backend.app.models.user import User
from backend.app.models.user_daily import UserDaily


def get_or_assign_daily_problem(db: Session, user: User, today: date) -> UserDaily:
    daily = db.execute(
        select(UserDaily)
        .where(UserDaily.user_id == user.id, UserDaily.assigned_date == today)
        .options(
            selectinload(UserDaily.problem).selectinload(Problem.choices),
            selectinload(UserDaily.problem).selectinload(Problem.passage),
            selectinload(UserDaily.problem).selectinload(Problem.exam),
        )
    ).scalar_one_or_none()
    if daily:
        return daily

    problem = select_next_problem(db, user)
    daily = UserDaily(user_id=user.id, assigned_date=today, problem_id=problem.id, completed=False)
    db.add(daily)
    db.commit()
    db.refresh(daily)
    return load_daily(db, daily.id)


def load_daily(db: Session, daily_id: int) -> UserDaily:
    return db.execute(
        select(UserDaily)
        .where(UserDaily.id == daily_id)
        .options(
            selectinload(UserDaily.problem).selectinload(Problem.choices),
            selectinload(UserDaily.problem).selectinload(Problem.passage),
            selectinload(UserDaily.problem).selectinload(Problem.exam),
        )
    ).scalar_one()


def select_next_problem(db: Session, user: User) -> Problem:
    target_area = get_next_area(db, user)
    problem = find_unattempted_problem(db, user, target_area)
    if problem:
        return problem

    fallback_area = (
        ProblemArea.reasoning_argumentation
        if target_area == ProblemArea.reading_comprehension
        else ProblemArea.reading_comprehension
    )
    problem = find_unattempted_problem(db, user, fallback_area)
    if problem:
        return problem

    problem = db.execute(
        select(Problem)
        .join(Exam)
        .where(Exam.year == 2026)
        .order_by(Exam.year.desc(), Problem.number.asc())
        .limit(1)
    ).scalar_one_or_none()
    if not problem:
        raise LookupError("No importable 2026 problems found")
    return problem


def get_next_area(db: Session, user: User) -> ProblemArea:
    last_daily = db.execute(
        select(UserDaily)
        .join(UserDaily.problem)
        .where(UserDaily.user_id == user.id)
        .order_by(UserDaily.assigned_date.desc(), UserDaily.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if not last_daily:
        return ProblemArea.reading_comprehension
    if last_daily.problem.area == ProblemArea.reading_comprehension:
        return ProblemArea.reasoning_argumentation
    return ProblemArea.reading_comprehension


def find_unattempted_problem(db: Session, user: User, area: ProblemArea) -> Problem | None:
    statement: Select[tuple[Problem]] = (
        select(Problem)
        .join(Exam)
        .where(
            Exam.year == 2026,
            Problem.area == area,
            ~select(Attempt.id)
            .where(Attempt.user_id == user.id, Attempt.problem_id == Problem.id)
            .exists(),
        )
        .order_by(Exam.year.desc(), Problem.number.asc())
        .limit(1)
    )
    return db.execute(statement).scalar_one_or_none()
