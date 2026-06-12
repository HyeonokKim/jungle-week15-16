from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas.board import BoardPostResponse, BoardProblemResponse, ProblemBoardResponse
from backend.app.services.board import get_problem_board


router = APIRouter(prefix="/problems", tags=["board"])


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
            )
            for post in posts
        ],
    )
