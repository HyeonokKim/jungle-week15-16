from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas.board import (
    BoardCommentCreate,
    BoardCommentResponse,
    BoardPostResponse,
    BoardProblemResponse,
    ProblemBoardResponse,
)
from backend.app.services.board import create_board_comment, get_problem_board


router = APIRouter(prefix="/problems", tags=["board"])


def serialize_comment(comment) -> BoardCommentResponse:
    return BoardCommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        nickname=comment.user.nickname,
        content=comment.content,
        created_at=comment.created_at.isoformat(),
    )


@router.get("/{problem_id}/board", response_model=ProblemBoardResponse)
def read_problem_board(
    problem_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProblemBoardResponse:
    try:
        problem, posts = get_problem_board(db, user, problem_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    return ProblemBoardResponse(
        problem=BoardProblemResponse(
            id=problem.id,
            year=problem.exam.year,
            area=problem.area.value,
            number=problem.number,
            question_text=problem.question_text,
        ),
        posts=[
            BoardPostResponse(
                id=post.id,
                user_id=post.user_id,
                nickname=post.user.nickname,
                content=post.content,
                selected_index=post.selected_index,
                is_correct=post.is_correct,
                created_at=post.created_at.isoformat(),
                comments=[serialize_comment(comment) for comment in post.comments],
            )
            for post in posts
        ],
    )


@router.post("/{problem_id}/board/posts/{post_id}/comments", response_model=BoardCommentResponse)
def create_problem_board_comment(
    problem_id: int,
    post_id: int,
    payload: BoardCommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BoardCommentResponse:
    try:
        comment = create_board_comment(db, user, problem_id, post_id, payload.content)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return serialize_comment(comment)
