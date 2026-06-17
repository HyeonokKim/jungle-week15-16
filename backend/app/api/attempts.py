from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas.attempt import AttemptCreate, AttemptResultResponse
from backend.app.api.daily import get_problem_stats
from backend.app.services.attempts import submit_attempt


router = APIRouter(prefix="/attempts", tags=["attempts"])


@router.post("", response_model=AttemptResultResponse)
def create_attempt(
    payload: AttemptCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AttemptResultResponse:
    try:
        attempt = submit_attempt(
            db=db,
            user=user,
            problem_id=payload.problem_id,
            selected_index=payload.selected_index,
            reasoning=payload.reasoning,
            today=date.today(),
            solve_duration_sec=payload.solve_duration_sec,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    answer_index = attempt.problem.answer_index
    if answer_index is None:
        raise HTTPException(status_code=404, detail="Problem answer is not available")

    return AttemptResultResponse(
        attempt_id=attempt.id,
        problem_id=attempt.problem_id,
        selected_index=attempt.selected_index,
        answer_index=answer_index,
        is_correct=attempt.is_correct,
        explanation=attempt.problem.explanation,
        problem_stats=get_problem_stats(db, attempt.problem_id),
    )
