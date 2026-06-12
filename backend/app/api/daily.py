from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user_daily import UserDaily
from backend.app.models.problem import Problem
from backend.app.schemas.problem import ChoiceResponse, DailyProblemResponse, ProblemResponse
from backend.app.services.daily import get_or_assign_daily_problem
from backend.app.services.dev_user import get_or_create_dev_user


router = APIRouter(prefix="/daily", tags=["daily"])


@router.get("", response_model=DailyProblemResponse)
def get_daily_problem(
    user_id: int = Query(default=1, gt=0),
    db: Session = Depends(get_db),
) -> DailyProblemResponse:
    user = get_or_create_dev_user(db, user_id)
    try:
        daily = get_or_assign_daily_problem(db, user, date.today())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return build_daily_response(daily)


def build_daily_response(daily: UserDaily) -> DailyProblemResponse:
    problem = daily.problem
    return DailyProblemResponse(
        assigned_date=daily.assigned_date.isoformat(),
        completed=daily.completed,
        problem=build_problem_response(problem),
    )


def build_problem_response(problem: Problem) -> ProblemResponse:
    return ProblemResponse(
        id=problem.id,
        year=problem.exam.year,
        round=problem.exam.round,
        area=problem.area.value,
        number=problem.number,
        question_text=problem.question_text,
        passage=problem.passage.content if problem.passage else None,
        choices=[ChoiceResponse(id=choice.id, idx=choice.idx, content=choice.content) for choice in problem.choices],
    )
