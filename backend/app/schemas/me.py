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


class WeeklySummaryResponse(BaseModel):
    week_start: str
    week_end: str
    total_attempts: int
    correct_attempts: int
    accuracy_rate: int
    daily_attempts: int
    practice_attempts: int
    average_solve_duration_sec: int | None
    weak_type: str | None
    area_accuracy: list[AreaAccuracyResponse]
    summary_text: str


class WeeklySummaryNotionResponse(BaseModel):
    page_id: str
    url: str | None
    already_saved: bool
    message: str


class NotionConnectionResponse(BaseModel):
    connected: bool
    workspace_id: str | None = None
    workspace_name: str | None = None
    workspace_icon: str | None = None
    default_page_id: str | None = None


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
