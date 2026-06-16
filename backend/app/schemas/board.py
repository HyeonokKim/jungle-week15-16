from pydantic import BaseModel, Field


class BoardCommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class BoardPostUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class BoardCommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    nickname: str
    content: str
    created_at: str


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
    is_mine: bool
    created_at: str
    comments: list[BoardCommentResponse]


class ProblemBoardResponse(BaseModel):
    problem: BoardProblemResponse
    posts: list[BoardPostResponse]
