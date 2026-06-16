from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.models.attempt import Attempt
from backend.app.models.board_post import BoardPost
from backend.app.models.problem import Problem
from backend.app.models.user import User
from backend.app.services.weakness import calculate_weak_type


AREA_LABELS = {
    "reading_comprehension": "언어이해",
    "reasoning_argumentation": "추리논증",
}

PROBLEM_TYPE_LABELS = {
    "main_claim": "핵심 주장",
    "detail_matching": "세부 일치",
    "inference": "추론",
    "structure_analysis": "구조 파악",
    "conditional_reasoning": "조건 추론",
    "strengthen_weaken": "강화/약화",
    "error_identification": "오류 찾기",
    "principle_application": "원리 적용",
    "data_interpretation": "자료 해석",
}


@dataclass(frozen=True)
class WeeklySummary:
    week_start: date
    week_end: date
    total_attempts: int
    correct_attempts: int
    accuracy_rate: int
    daily_attempts: int
    practice_attempts: int
    average_solve_duration_sec: int | None
    weak_type: str | None
    area_accuracy: list[dict[str, int | str]]
    summary_text: str


def get_my_posts(db: Session, user: User) -> list[BoardPost]:
    return list(
        db.execute(
            select(BoardPost)
            .where(BoardPost.user_id == user.id)
            .options(selectinload(BoardPost.problem).selectinload(Problem.exam))
            .order_by(BoardPost.created_at.desc(), BoardPost.id.desc())
        )
        .scalars()
        .all()
    )


def get_my_attempts(db: Session, user: User) -> list[Attempt]:
    return list(
        db.execute(
            select(Attempt)
            .where(Attempt.user_id == user.id)
            .options(selectinload(Attempt.problem).selectinload(Problem.exam))
            .order_by(Attempt.attempted_at.desc(), Attempt.id.desc())
        )
        .scalars()
        .all()
    )


def get_recent_attempt_history(db: Session, user: User, limit: int = 20) -> list[Attempt]:
    return list(
        db.execute(
            select(Attempt)
            .where(Attempt.user_id == user.id)
            .options(selectinload(Attempt.problem).selectinload(Problem.exam))
            .order_by(Attempt.attempted_at.desc(), Attempt.id.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )


def get_week_start(today: date) -> date:
    return today - timedelta(days=today.weekday())


def get_weekly_attempts(db: Session, user: User, today: date) -> list[Attempt]:
    week_start = get_week_start(today)
    week_end_exclusive = today + timedelta(days=1)

    return list(
        db.execute(
            select(Attempt)
            .where(
                Attempt.user_id == user.id,
                Attempt.attempted_at >= datetime.combine(week_start, time.min),
                Attempt.attempted_at < datetime.combine(week_end_exclusive, time.min),
            )
            .options(selectinload(Attempt.problem).selectinload(Problem.exam))
            .order_by(Attempt.attempted_at.desc(), Attempt.id.desc())
        )
        .scalars()
        .all()
    )


def calculate_accuracy(correct_count: int, total_count: int) -> int:
    if total_count == 0:
        return 0
    return round((correct_count / total_count) * 100)


def summarize_area_accuracy(attempts: list[Attempt]) -> list[dict[str, int | str]]:
    totals: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "correct": 0})
    for attempt in attempts:
        area = attempt.problem.area.value
        totals[area]["total"] += 1
        if attempt.is_correct:
            totals[area]["correct"] += 1

    return [
        {
            "area": area,
            "total_attempts": values["total"],
            "correct_attempts": values["correct"],
            "accuracy_rate": calculate_accuracy(values["correct"], values["total"]),
        }
        for area, values in sorted(totals.items())
    ]


def summarize_weekly_attempts(attempts: Iterable[Attempt], today: date) -> WeeklySummary:
    attempt_list = list(attempts)
    total_attempts = len(attempt_list)
    correct_attempts = sum(1 for attempt in attempt_list if attempt.is_correct)
    daily_attempts = sum(1 for attempt in attempt_list if attempt.is_daily)
    practice_attempts = total_attempts - daily_attempts
    solve_durations = [
        attempt.solve_duration_sec
        for attempt in attempt_list
        if getattr(attempt, "solve_duration_sec", None) is not None
    ]
    accuracy_rate = calculate_accuracy(correct_attempts, total_attempts)
    weak_type = calculate_weak_type(attempt_list)
    area_accuracy = summarize_area_accuracy(attempt_list)

    return WeeklySummary(
        week_start=get_week_start(today),
        week_end=today,
        total_attempts=total_attempts,
        correct_attempts=correct_attempts,
        accuracy_rate=accuracy_rate,
        daily_attempts=daily_attempts,
        practice_attempts=practice_attempts,
        average_solve_duration_sec=round(sum(solve_durations) / len(solve_durations)) if solve_durations else None,
        weak_type=weak_type,
        area_accuracy=area_accuracy,
        summary_text=build_weekly_summary_text(
            total_attempts=total_attempts,
            correct_attempts=correct_attempts,
            daily_attempts=daily_attempts,
            practice_attempts=practice_attempts,
            accuracy_rate=accuracy_rate,
            weak_type=weak_type,
            area_accuracy=area_accuracy,
        ),
    )


def build_weekly_summary_text(
    *,
    total_attempts: int,
    correct_attempts: int,
    daily_attempts: int,
    practice_attempts: int,
    accuracy_rate: int,
    weak_type: str | None,
    area_accuracy: list[dict[str, int | str]],
) -> str:
    if total_attempts == 0:
        return "이번 주 풀이 기록이 아직 없어요. 오늘의 문제부터 가볍게 시작해 보세요."

    parts = [
        f"이번 주에는 총 {total_attempts}문제를 풀고 {correct_attempts}문제를 맞혔어요.",
        f"정답률은 {accuracy_rate}%이고, 데일리 {daily_attempts}문제와 추가 연습 {practice_attempts}문제를 진행했어요.",
    ]

    strongest_area = find_strongest_area(area_accuracy)
    if strongest_area:
        area = str(strongest_area["area"])
        parts.append(f"{AREA_LABELS.get(area, area)} 정답률이 가장 안정적이에요.")

    if weak_type:
        parts.append(f"이번 주에는 {PROBLEM_TYPE_LABELS.get(weak_type, weak_type)} 유형을 우선 복습하면 좋아요.")
    else:
        parts.append("이번 주 오답 유형이 뚜렷하지 않아 현재 흐름을 유지해도 좋아요.")

    return " ".join(parts)


def find_strongest_area(area_accuracy: list[dict[str, int | str]]) -> dict[str, int | str] | None:
    if not area_accuracy:
        return None
    return sorted(
        area_accuracy,
        key=lambda item: (int(item["accuracy_rate"]), int(item["total_attempts"]), str(item["area"])),
        reverse=True,
    )[0]
