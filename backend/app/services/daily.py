from datetime import date

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from backend.app.models.attempt import Attempt
from backend.app.models.enums import ProblemArea, ProblemScope
from backend.app.models.exam import Exam
from backend.app.models.problem import Problem
from backend.app.models.user import User
from backend.app.models.user_daily import UserDaily
from backend.app.services.review import get_due_review_item
from backend.app.services.settings import get_or_create_user_settings


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

    due_review_item = get_due_review_item(db, user, today)
    if due_review_item:
        problem = due_review_item.problem
    else:
        setting = get_or_create_user_settings(db, user)
        problem = select_next_problem(db, user, setting.problem_scope)
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


def select_next_problem(db: Session, user: User, problem_scope: ProblemScope) -> Problem:
    target_area = get_next_area(db, user)
    problem = find_unattempted_problem(db, user, target_area, problem_scope)
    if problem:
        return problem

    fallback_area = (
        ProblemArea.reasoning_argumentation
        if target_area == ProblemArea.reading_comprehension
        else ProblemArea.reading_comprehension
    )
    problem = find_unattempted_problem(db, user, fallback_area, problem_scope)
    if problem:
        return problem

    fallback_statement = apply_problem_scope(
        select(Problem)
        .join(Exam)
        .where(Problem.answer_index.is_not(None))
        .order_by(Exam.year.desc(), Problem.number.asc())
        .limit(1),
        db,
        problem_scope,
    )
    problem = db.execute(fallback_statement).scalar_one_or_none()
    if not problem:
        raise LookupError("No importable problems found")
    return problem


def select_next_practice_problem(db: Session, user: User, today: date) -> Problem:
    setting = get_or_create_user_settings(db, user)
    target_area = get_next_area(db, user)
    problem = find_unattempted_problem(db, user, target_area, setting.problem_scope, exclude_daily_date=today)
    if problem:
        return problem

    fallback_area = (
        ProblemArea.reasoning_argumentation
        if target_area == ProblemArea.reading_comprehension
        else ProblemArea.reading_comprehension
    )
    problem = find_unattempted_problem(db, user, fallback_area, setting.problem_scope, exclude_daily_date=today)
    if problem:
        return problem

    raise LookupError("No practice problems found")


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


def find_unattempted_problem(
    db: Session,
    user: User,
    area: ProblemArea,
    problem_scope: ProblemScope,
    exclude_daily_date: date | None = None,
) -> Problem | None:
    statement: Select[tuple[Problem]] = (
        select(Problem)
        .join(Exam)
        .where(
            Problem.area == area,
            Problem.answer_index.is_not(None),
            ~select(Attempt.id)
            .where(Attempt.user_id == user.id, Attempt.problem_id == Problem.id)
            .exists(),
        )
        .order_by(Exam.year.desc(), Problem.number.asc())
        .limit(1)
    )
    statement = apply_problem_scope(statement, db, problem_scope)
    if exclude_daily_date:
        statement = statement.where(
            ~select(UserDaily.id)
            .where(
                UserDaily.user_id == user.id,
                UserDaily.problem_id == Problem.id,
                UserDaily.assigned_date == exclude_daily_date,
            )
            .exists()
        )
    return db.execute(statement).scalar_one_or_none()


def apply_problem_scope(
    statement: Select[tuple[Problem]],
    db: Session,
    problem_scope: ProblemScope,
) -> Select[tuple[Problem]]:
    if problem_scope == ProblemScope.all_random:
        return statement

    latest_year = db.execute(select(func.max(Exam.year))).scalar_one_or_none()
    if latest_year is None:
        return statement

    year_window = 3 if problem_scope == ProblemScope.recent_3y else 5
    return statement.where(Exam.year >= latest_year - year_window + 1)
