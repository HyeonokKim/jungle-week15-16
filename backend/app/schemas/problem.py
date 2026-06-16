from pydantic import BaseModel


class ChoiceResponse(BaseModel):
    id: int
    idx: int
    content: str


class ProblemStatsResponse(BaseModel):
    total_attempts: int
    correct_attempts: int
    accuracy_rate: int
    average_solve_duration_sec: int | None


class ProblemResponse(BaseModel):
    id: int
    year: int
    round: str
    area: str
    number: int
    question_text: str
    passage: str | None
    choices: list[ChoiceResponse]
    similarity_score: int | None = None
    stats: ProblemStatsResponse


class DailyProblemResponse(BaseModel):
    assigned_date: str
    completed: bool
    problem: ProblemResponse
