from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.ai_explanation import AIExplanation
from backend.app.models.user import User
from backend.app.schemas.ai_explanation import AIExplanationResponse
from backend.app.services.ai_explanations import (
    AIExplanationConfigurationError,
    generate_ai_explanation,
    get_user_ai_explanation,
)


router = APIRouter(prefix="/attempts", tags=["ai-explanations"])


@router.post("/{attempt_id}/ai-explanation", response_model=AIExplanationResponse)
def create_ai_explanation(
    attempt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIExplanationResponse:
    try:
        explanation = generate_ai_explanation(db, user, attempt_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIExplanationConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return build_ai_explanation_response(explanation)


@router.get("/{attempt_id}/ai-explanation", response_model=AIExplanationResponse)
def read_ai_explanation(
    attempt_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIExplanationResponse:
    try:
        explanation = get_user_ai_explanation(db, user, attempt_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return build_ai_explanation_response(explanation)


def build_ai_explanation_response(explanation: AIExplanation) -> AIExplanationResponse:
    return AIExplanationResponse(
        id=explanation.id,
        attempt_id=explanation.attempt_id,
        problem_id=explanation.problem_id,
        status=explanation.status,
        final_explanation=explanation.final_explanation,
        solution_summary=explanation.solution_summary,
        user_reasoning_review=explanation.user_reasoning_review,
        wrong_choice_explanation=explanation.wrong_choice_explanation,
        confidence_level=explanation.confidence_level,
        confidence_score=explanation.confidence_score,
        candidate_count=explanation.candidate_count,
        accepted_count=explanation.accepted_count,
        discarded_count=explanation.discarded_count,
        critic_passed=explanation.critic_passed,
        critic_notes=explanation.critic_notes,
        references_used=explanation.references_used,
        model_name=explanation.model_name,
        error_message=explanation.error_message,
        created_at=explanation.created_at.isoformat(),
        updated_at=explanation.updated_at.isoformat(),
    )
