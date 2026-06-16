from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.daily import build_problem_response
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas.problem import ProblemResponse
from backend.app.services.daily import select_next_practice_problem_selection


router = APIRouter(prefix="/practice", tags=["practice"])


@router.get("/next", response_model=ProblemResponse)
def get_next_practice_problem(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProblemResponse:
    try:
        selection = select_next_practice_problem_selection(db, user, date.today())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return build_problem_response(db, selection.problem, similarity_score=selection.similarity_score)
