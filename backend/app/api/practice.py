from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.api.daily import build_problem_response
from backend.app.core.database import get_db
from backend.app.schemas.problem import ProblemResponse
from backend.app.services.daily import select_next_practice_problem
from backend.app.services.dev_user import get_or_create_dev_user


router = APIRouter(prefix="/practice", tags=["practice"])


@router.get("/next", response_model=ProblemResponse)
def get_next_practice_problem(
    user_id: int = Query(default=1, gt=0),
    db: Session = Depends(get_db),
) -> ProblemResponse:
    user = get_or_create_dev_user(db, user_id)
    try:
        problem = select_next_practice_problem(db, user, date.today())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return build_problem_response(problem)
