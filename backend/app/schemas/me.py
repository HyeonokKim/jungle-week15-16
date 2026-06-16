from pydantic import BaseModel


class MyPostResponse(BaseModel):
    id: int
    problem_id: int
    title: str
    area: str
    selected_index: int
    is_correct: bool
    created_at: str


class AreaAccuracyResponse(BaseModel):
    area: str
    total_attempts: int
    correct_attempts: int
    accuracy_rate: int


class MyAttemptHistoryItemResponse(BaseModel):
    id: int
    problem_id: int
    title: str
    area: str
    selected_index: int
    is_correct: bool
    is_daily: bool
    attempted_at: str


class MyAttemptHistoryDayResponse(BaseModel):
    date: str
    attempts: list[MyAttemptHistoryItemResponse]


class MyStatsResponse(BaseModel):
    user_id: int
    nickname: str
    created_at: str
    current_streak: int
    longest_streak: int
    total_attempts: int
    correct_attempts: int
    accuracy_rate: int
    area_accuracy: list[AreaAccuracyResponse]
