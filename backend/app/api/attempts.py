from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.attempt import AttemptCreate, AttemptResultResponse
from backend.app.services.attempts import submit_attempt
from backend.app.services.dev_user import get_or_create_dev_user


router = APIRouter(prefix="/attempts", tags=["attempts"])


@router.post("", response_model=AttemptResultResponse)
def create_attempt(
    payload: AttemptCreate,
    db: Session = Depends(get_db),
) -> AttemptResultResponse:
    user = get_or_create_dev_user(db, payload.user_id)
    try:
        attempt = submit_attempt(
            db=db,
            user=user,
            problem_id=payload.problem_id,
            selected_index=payload.selected_index,
            reasoning=payload.reasoning,
            today=date.today(),
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

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
    )
