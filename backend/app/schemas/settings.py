from typing import Literal

from pydantic import BaseModel

from backend.app.models.enums import ProblemScope


class UserSettingsResponse(BaseModel):
    user_id: int
    problem_scope: ProblemScope
    timer_limit_sec: Literal[120, 180, 240]
    review_interval_days: Literal[3, 5, 7] | None
    weak_type: str | None
    created_at: str
    updated_at: str


class UserSettingsUpdate(BaseModel):
    problem_scope: ProblemScope | None = None
    timer_limit_sec: Literal[120, 180, 240] | None = None
    review_interval_days: Literal[3, 5, 7] | None = None
