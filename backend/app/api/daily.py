from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.attempt import Attempt
from backend.app.models.problem import Problem
from backend.app.models.user import User
from backend.app.models.user_daily import UserDaily
from backend.app.schemas.problem import ChoiceResponse, DailyProblemResponse, ProblemResponse, ProblemStatsResponse
from backend.app.services.daily import get_or_assign_daily_problem


router = APIRouter(prefix="/daily", tags=["daily"])


@router.get("", response_model=DailyProblemResponse)
def get_daily_problem(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DailyProblemResponse:
    try:
        daily = get_or_assign_daily_problem(db, user, date.today())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return build_daily_response(db, daily)


def build_daily_response(db: Session, daily: UserDaily) -> DailyProblemResponse:
    problem = daily.problem
    return DailyProblemResponse(
        assigned_date=daily.assigned_date.isoformat(),
        completed=daily.completed,
        problem=build_problem_response(db, problem),
    )


def get_problem_stats(db: Session, problem_id: int) -> ProblemStatsResponse:
    total_attempts, correct_attempts, average_solve_duration_sec = db.execute(
        select(
            func.count(Attempt.id),
            func.count(Attempt.id).filter(Attempt.is_correct.is_(True)),
            func.avg(Attempt.solve_duration_sec),
        ).where(Attempt.problem_id == problem_id)
    ).one()
    total_attempts = int(total_attempts or 0)
    correct_attempts = int(correct_attempts or 0)
    return ProblemStatsResponse(
        total_attempts=total_attempts,
        correct_attempts=correct_attempts,
        accuracy_rate=round((correct_attempts / total_attempts) * 100) if total_attempts else 0,
        average_solve_duration_sec=round(average_solve_duration_sec) if average_solve_duration_sec is not None else None,
    )


def build_problem_response(db: Session, problem: Problem, similarity_score: int | None = None) -> ProblemResponse:
    return ProblemResponse(
        id=problem.id,
        year=problem.exam.year,
        round=problem.exam.round,
        area=problem.area.value,
        number=problem.number,
        question_text=problem.question_text,
        passage=problem.passage.content if problem.passage else None,
        choices=[ChoiceResponse(id=choice.id, idx=choice.idx, content=choice.content) for choice in problem.choices],
        similarity_score=similarity_score,
        stats=get_problem_stats(db, problem.id),
    )
