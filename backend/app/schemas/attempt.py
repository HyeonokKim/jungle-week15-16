from pydantic import BaseModel, Field, field_validator


class AttemptCreate(BaseModel):
    user_id: int = Field(gt=0)
    problem_id: int = Field(gt=0)
    selected_index: int = Field(ge=1, le=5)
    reasoning: str

    @field_validator("reasoning")
    @classmethod
    def reasoning_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("reasoning is required")
        return stripped


class AttemptResultResponse(BaseModel):
    attempt_id: int
    problem_id: int
    selected_index: int
    answer_index: int
    is_correct: bool
    explanation: str | None
