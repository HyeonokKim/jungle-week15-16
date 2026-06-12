from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.me import AreaAccuracyResponse, MyPostResponse, MyStatsResponse
from backend.app.services.dev_user import get_or_create_dev_user
from backend.app.services.me import calculate_accuracy, get_my_attempts, get_my_posts, summarize_area_accuracy


router = APIRouter(tags=["me"])

AREA_LABELS = {
    "reading_comprehension": "언어이해",
    "reasoning_argumentation": "추리논증",
}


@router.get("/me/posts", response_model=list[MyPostResponse])
def read_my_posts(
    user_id: int = Query(default=1, gt=0),
    db: Session = Depends(get_db),
) -> list[MyPostResponse]:
    user = get_or_create_dev_user(db, user_id)
    posts = get_my_posts(db, user)
    return [
        MyPostResponse(
            id=post.id,
            problem_id=post.problem_id,
            title=f"{post.problem.exam.year}학년도 {AREA_LABELS[post.problem.area.value]} {post.problem.number}번",
            area=post.problem.area.value,
            selected_index=post.selected_index,
            is_correct=post.is_correct,
            created_at=post.created_at.isoformat(),
        )
        for post in posts
    ]


@router.get("/stats/me", response_model=MyStatsResponse)
def read_my_stats(
    user_id: int = Query(default=1, gt=0),
    db: Session = Depends(get_db),
) -> MyStatsResponse:
    user = get_or_create_dev_user(db, user_id)
    attempts = get_my_attempts(db, user)
    total_attempts = len(attempts)
    correct_attempts = sum(1 for attempt in attempts if attempt.is_correct)

    return MyStatsResponse(
        user_id=user.id,
        nickname=user.nickname,
        created_at=user.created_at.isoformat(),
        current_streak=user.current_streak,
        longest_streak=user.longest_streak,
        total_attempts=total_attempts,
        correct_attempts=correct_attempts,
        accuracy_rate=calculate_accuracy(correct_attempts, total_attempts),
        area_accuracy=[AreaAccuracyResponse(**item) for item in summarize_area_accuracy(attempts)],
    )
