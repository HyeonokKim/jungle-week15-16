from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.models.attempt import Attempt
from backend.app.models.enums import ProblemType
from backend.app.models.user import User
from backend.app.models.user_setting import UserSetting
from backend.app.services.settings import get_or_create_user_settings


@dataclass(frozen=True)
class WeakTypeCandidate:
    problem_type: ProblemType
    total_attempts: int
    incorrect_attempts: int
    accuracy_rate: int


def calculate_weak_type(attempts: Iterable[Attempt]) -> str | None:
    candidates = summarize_weak_type_candidates(attempts)
    if not candidates:
        return None

    weakest = sorted(
        candidates,
        key=lambda item: (item.accuracy_rate, -item.incorrect_attempts, -item.total_attempts, item.problem_type.value),
    )[0]
    return weakest.problem_type.value


def summarize_weak_type_candidates(attempts: Iterable[Attempt]) -> list[WeakTypeCandidate]:
    totals: dict[ProblemType, dict[str, int]] = defaultdict(lambda: {"total": 0, "incorrect": 0})
    for attempt in attempts:
        if not attempt.problem or not attempt.problem.problem_type:
            continue

        problem_type = attempt.problem.problem_type
        totals[problem_type]["total"] += 1
        if not attempt.is_correct:
            totals[problem_type]["incorrect"] += 1

    candidates: list[WeakTypeCandidate] = []
    for problem_type, values in totals.items():
        incorrect = values["incorrect"]
        if incorrect == 0:
            continue

        total = values["total"]
        accuracy_rate = round(((total - incorrect) / total) * 100)
        candidates.append(
            WeakTypeCandidate(
                problem_type=problem_type,
                total_attempts=total,
                incorrect_attempts=incorrect,
                accuracy_rate=accuracy_rate,
            )
        )

    return candidates


def refresh_user_weak_type(db: Session, user: User, *, commit: bool = False) -> UserSetting:
    attempts = list(
        db.execute(
            select(Attempt)
            .where(Attempt.user_id == user.id)
            .options(selectinload(Attempt.problem))
        )
        .scalars()
        .all()
    )
    weak_type = calculate_weak_type(attempts)
    setting = get_or_create_user_settings(db, user)

    if setting.weak_type != weak_type:
        setting.weak_type = weak_type
        db.add(setting)
        if commit:
            db.commit()
            db.refresh(setting)

    return setting
