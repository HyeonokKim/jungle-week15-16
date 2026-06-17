from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from datetime import date

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from backend.app.core.config import get_settings
from backend.app.core.database import SessionLocal
from backend.app.models.attempt import Attempt
from backend.app.models.enums import ProblemScope
from backend.app.models.exam import Exam
from backend.app.models.problem import Problem
from backend.app.models.problem_embedding import ProblemEmbedding
from backend.app.models.user import User
from backend.app.models.user_daily import UserDaily


EMBEDDING_DIMENSIONS = 1536


class EmbeddingConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class BackfillSummary:
    scanned: int
    created: int
    updated: int
    skipped: int
    dry_run: bool


@dataclass(frozen=True)
class SimilarProblemRecommendation:
    problem: Problem
    similarity_score: int


def build_problem_embedding_text(problem: Problem) -> str:
    parts = [
        f"영역: {problem.area.value}",
        f"연도: {problem.exam.year}",
        f"문항 번호: {problem.number}",
    ]
    if problem.passage:
        parts.append(f"지문:\n{problem.passage.content}")
    parts.append(f"문제:\n{problem.question_text}")
    choices = "\n".join(f"{choice.idx}. {choice.content}" for choice in sorted(problem.choices, key=lambda choice: choice.idx))
    parts.append(f"선택지:\n{choices}")
    return "\n\n".join(parts)


def calculate_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def create_openai_embedding(text: str, model: str) -> list[float]:
    settings = get_settings()
    if not settings.openai_api_key:
        raise EmbeddingConfigurationError("OPENAI_API_KEY is required to backfill problem embeddings.")

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(model=model, input=text)
    embedding = response.data[0].embedding
    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise ValueError(f"{model} returned {len(embedding)} dimensions; expected {EMBEDDING_DIMENSIONS}.")
    return embedding


def backfill_problem_embeddings(
    db: Session,
    *,
    force: bool = False,
    limit: int | None = None,
    dry_run: bool = False,
) -> BackfillSummary:
    model = get_settings().openai_embedding_model
    statement = (
        select(Problem)
        .where(Problem.answer_index.is_not(None))
        .options(
            selectinload(Problem.choices),
            selectinload(Problem.passage),
            selectinload(Problem.exam),
        )
        .order_by(Problem.id.asc())
    )
    if limit is not None:
        statement = statement.limit(limit)
    problems = list(db.execute(statement).scalars().all())

    existing_by_problem_id = {
        embedding.problem_id: embedding
        for embedding in db.execute(
            select(ProblemEmbedding).where(ProblemEmbedding.problem_id.in_([problem.id for problem in problems]))
        )
        .scalars()
        .all()
    } if problems else {}

    created = 0
    updated = 0
    skipped = 0
    for problem in problems:
        text = build_problem_embedding_text(problem)
        content_hash = calculate_content_hash(text)
        existing = existing_by_problem_id.get(problem.id)
        should_refresh = (
            force
            or existing is None
            or existing.embedding_model != model
            or existing.content_hash != content_hash
        )
        if not should_refresh:
            skipped += 1
            continue

        if dry_run:
            if existing:
                updated += 1
            else:
                created += 1
            continue

        embedding = create_openai_embedding(text, model)
        if existing:
            existing.embedding = embedding
            existing.embedding_model = model
            existing.content_hash = content_hash
            updated += 1
        else:
            db.add(
                ProblemEmbedding(
                    problem_id=problem.id,
                    embedding=embedding,
                    embedding_model=model,
                    content_hash=content_hash,
                )
            )
            created += 1

    if not dry_run:
        db.commit()

    return BackfillSummary(
        scanned=len(problems),
        created=created,
        updated=updated,
        skipped=skipped,
        dry_run=dry_run,
    )


def select_similar_practice_problem(
    db: Session,
    user: User,
    reference_problem: Problem,
    problem_scope: ProblemScope,
    today: date,
) -> SimilarProblemRecommendation | None:
    model = get_settings().openai_embedding_model
    reference_embedding = db.execute(
        select(ProblemEmbedding).where(
            ProblemEmbedding.problem_id == reference_problem.id,
            ProblemEmbedding.embedding_model == model,
        )
    ).scalar_one_or_none()
    if not reference_embedding:
        return None

    if reference_problem.passage_id is not None:
        problem = find_similar_candidate(
            db,
            user,
            reference_problem,
            reference_embedding,
            problem_scope,
            today,
            exclude_same_passage=True,
        )
        if problem:
            return problem

    return find_similar_candidate(
        db,
        user,
        reference_problem,
        reference_embedding,
        problem_scope,
        today,
        exclude_same_passage=False,
    )


def find_similar_candidate(
    db: Session,
    user: User,
    reference_problem: Problem,
    reference_embedding: ProblemEmbedding,
    problem_scope: ProblemScope,
    today: date,
    *,
    exclude_same_passage: bool,
) -> SimilarProblemRecommendation | None:
    distance = ProblemEmbedding.embedding.cosine_distance(reference_embedding.embedding).label("distance")
    statement = (
        select(Problem, distance)
        .join(ProblemEmbedding, ProblemEmbedding.problem_id == Problem.id)
        .join(Exam)
        .where(
            ProblemEmbedding.embedding_model == reference_embedding.embedding_model,
            Problem.id != reference_problem.id,
            Problem.area == reference_problem.area,
            Problem.answer_index.is_not(None),
            ~select(Attempt.id)
            .where(Attempt.user_id == user.id, Attempt.problem_id == Problem.id)
            .exists(),
            ~select(UserDaily.id)
            .where(
                UserDaily.user_id == user.id,
                UserDaily.problem_id == Problem.id,
                UserDaily.assigned_date == today,
            )
            .exists(),
        )
        .options(
            selectinload(Problem.choices),
            selectinload(Problem.passage),
            selectinload(Problem.exam),
        )
    )
    if exclude_same_passage:
        statement = statement.where(Problem.passage_id.is_distinct_from(reference_problem.passage_id))
    statement = apply_problem_scope(statement, db, problem_scope).order_by(distance.asc(), Problem.id.asc()).limit(1)
    row = db.execute(statement).one_or_none()
    if not row:
        return None

    problem, cosine_distance = row
    return SimilarProblemRecommendation(
        problem=problem,
        similarity_score=cosine_distance_to_percent(float(cosine_distance)),
    )


def cosine_distance_to_percent(cosine_distance: float) -> int:
    similarity = 1 - cosine_distance
    clamped = max(0.0, min(1.0, similarity))
    return round(clamped * 100)


def apply_problem_scope(
    statement: Select[tuple[Problem]],
    db: Session,
    problem_scope: ProblemScope,
) -> Select[tuple[Problem]]:
    if problem_scope == ProblemScope.all_random:
        return statement

    latest_year = db.execute(select(func.max(Exam.year))).scalar_one_or_none()
    if latest_year is None:
        return statement

    year_window = 3 if problem_scope == ProblemScope.recent_3y else 5
    return statement.where(Exam.year >= latest_year - year_window + 1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill OpenAI embeddings for imported LEET problems.")
    parser.add_argument("--force", action="store_true", help="Refresh embeddings even when content hashes match.")
    parser.add_argument("--limit", type=int, default=None, help="Only scan the first N answerable problems.")
    parser.add_argument("--dry-run", action="store_true", help="Report rows that need refresh without calling OpenAI.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with SessionLocal() as db:
        try:
            summary = backfill_problem_embeddings(db, force=args.force, limit=args.limit, dry_run=args.dry_run)
        except EmbeddingConfigurationError as exc:
            raise SystemExit(str(exc)) from exc

    action = "Would backfill" if summary.dry_run else "Backfilled"
    print(f"{action} problem embeddings:")
    print(f"- scanned: {summary.scanned}")
    print(f"- created: {summary.created}")
    print(f"- updated: {summary.updated}")
    print(f"- skipped: {summary.skipped}")


if __name__ == "__main__":
    main()
