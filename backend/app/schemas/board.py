from pydantic import BaseModel


class BoardProblemResponse(BaseModel):
    id: int
    year: int
    area: str
    number: int
    question_text: str


class BoardPostResponse(BaseModel):
    id: int
    user_id: int
    nickname: str
    content: str
    selected_index: int
    is_correct: bool
    created_at: str


class ProblemBoardResponse(BaseModel):
    problem: BoardProblemResponse
    posts: list[BoardPostResponse]
