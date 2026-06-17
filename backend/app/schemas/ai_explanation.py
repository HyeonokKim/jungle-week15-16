from pydantic import BaseModel


class AIExplanationResponse(BaseModel):
    id: int
    attempt_id: int
    problem_id: int
    status: str
    final_explanation: str | None
    solution_summary: str | None
    user_reasoning_review: str | None
    wrong_choice_explanation: str | None
    confidence_level: str | None
    confidence_score: int | None
    candidate_count: int
    accepted_count: int
    discarded_count: int
    critic_passed: bool | None
    critic_notes: str | None
    references_used: list[dict]
    model_name: str | None
    error_message: str | None
    created_at: str
    updated_at: str
