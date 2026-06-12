from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.models.choice import Choice
from backend.app.models.enums import ProblemArea
from backend.app.models.exam import Exam
from backend.app.models.passage import Passage
from backend.app.models.problem import Problem


EXPECTED_PROBLEM_COUNTS = {
    ProblemArea.reading_comprehension: 30,
    ProblemArea.reasoning_argumentation: 40,
}


@dataclass(frozen=True)
class ImportSummary:
    path: Path
    year: int
    area: ProblemArea
    problem_count: int
    passage_count: int
    choice_count: int


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_paths(parsed_dir: Path, years: list[int], areas: list[ProblemArea]) -> list[Path]:
    paths: list[Path] = []
    for year in years:
        for area in areas:
            path = parsed_dir / f"{year}_{area.value}.json"
            if not path.exists():
                raise FileNotFoundError(f"parsed data not found: {path}")
            paths.append(path)
    return paths


def validate_payload(path: Path, payload: dict[str, Any]) -> ImportSummary:
    exam_data = payload["exam"]
    metadata = payload["metadata"]
    area = ProblemArea(exam_data["area"])
    expected_count = EXPECTED_PROBLEM_COUNTS[area]
    problems = payload["problems"]
    passages = payload.get("passages", [])

    errors: list[str] = []
    if metadata.get("expected_problem_count") != expected_count:
        errors.append(f"expected_problem_count must be {expected_count}")
    if len(problems) != expected_count:
        errors.append(f"problem count must be {expected_count}, got {len(problems)}")
    if metadata.get("extracted_answer_count") != expected_count:
        errors.append(f"answer count must be {expected_count}, got {metadata.get('extracted_answer_count')}")

    seen_numbers: set[int] = set()
    choice_count = 0
    for problem in problems:
        number = problem.get("number")
        answer_index = problem.get("answer_index")
        choices = problem.get("choices", [])

        if number in seen_numbers:
            errors.append(f"duplicate problem number: {number}")
        seen_numbers.add(number)

        if not isinstance(answer_index, int) or not 1 <= answer_index <= 5:
            errors.append(f"problem {number} has invalid answer_index: {answer_index}")
        if len(choices) != 5:
            errors.append(f"problem {number} must have 5 choices, got {len(choices)}")
        for choice in choices:
            idx = choice.get("idx")
            if not isinstance(idx, int) or not 1 <= idx <= 5:
                errors.append(f"problem {number} has invalid choice idx: {idx}")
        choice_count += len(choices)

    if errors:
        formatted = "\n".join(f"- {error}" for error in errors)
        raise ValueError(f"{path} is not importable:\n{formatted}")

    return ImportSummary(
        path=path,
        year=int(exam_data["year"]),
        area=area,
        problem_count=len(problems),
        passage_count=len(passages),
        choice_count=choice_count,
    )


def import_payload(db: Session, path: Path, payload: dict[str, Any], replace: bool) -> ImportSummary:
    summary = validate_payload(path, payload)
    exam_data = payload["exam"]
    area = ProblemArea(exam_data["area"])

    existing = db.execute(
        select(Exam).where(
            Exam.year == int(exam_data["year"]),
            Exam.round == exam_data["round"],
            Exam.area == area,
        )
    ).scalar_one_or_none()

    if existing and not replace:
        return summary
    if existing:
        db.delete(existing)
        db.flush()

    exam = Exam(year=int(exam_data["year"]), round=exam_data["round"], area=area)
    db.add(exam)
    db.flush()

    passages_by_source_ref: dict[str, Passage] = {}
    for passage_data in payload.get("passages", []):
        passage = Passage(
            exam_id=exam.id,
            content=passage_data["content"],
            source_ref=passage_data["id"],
        )
        db.add(passage)
        passages_by_source_ref[passage_data["id"]] = passage
    db.flush()

    for problem_data in payload["problems"]:
        source_passage_id = problem_data.get("passage_id")
        passage = passages_by_source_ref.get(source_passage_id) if source_passage_id else None
        problem = Problem(
            exam_id=exam.id,
            passage_id=passage.id if passage else None,
            number=int(problem_data["number"]),
            question_text=problem_data["question_text"],
            explanation=problem_data.get("explanation"),
            answer_index=int(problem_data["answer_index"]),
            area=area,
        )
        db.add(problem)
        db.flush()

        for choice_data in problem_data["choices"]:
            db.add(
                Choice(
                    problem_id=problem.id,
                    idx=int(choice_data["idx"]),
                    content=choice_data["content"],
                )
            )

    return summary


def update_existing_text(db: Session, path: Path, payload: dict[str, Any]) -> ImportSummary:
    summary = validate_payload(path, payload)
    exam_data = payload["exam"]
    area = ProblemArea(exam_data["area"])

    exam = db.execute(
        select(Exam).where(
            Exam.year == int(exam_data["year"]),
            Exam.round == exam_data["round"],
            Exam.area == area,
        )
    ).scalar_one_or_none()
    if not exam:
        raise ValueError(f"exam not found for text update: {summary.year} {summary.area.value}")

    passages_by_source_ref = {passage.source_ref: passage for passage in exam.passages}
    for passage_data in payload.get("passages", []):
        passage = passages_by_source_ref.get(passage_data["id"])
        if passage:
            passage.content = passage_data["content"]

    problems_by_number = {problem.number: problem for problem in exam.problems}
    for problem_data in payload["problems"]:
        problem = problems_by_number.get(int(problem_data["number"]))
        if not problem:
            raise ValueError(f"problem not found for text update: {summary.year} {summary.area.value} #{problem_data['number']}")

        problem.question_text = problem_data["question_text"]
        problem.explanation = problem_data.get("explanation")
        problem.answer_index = int(problem_data["answer_index"])

        choices_by_idx = {choice.idx: choice for choice in problem.choices}
        for choice_data in problem_data["choices"]:
            choice = choices_by_idx.get(int(choice_data["idx"]))
            if not choice:
                raise ValueError(
                    f"choice not found for text update: "
                    f"{summary.year} {summary.area.value} #{problem.number}-{choice_data['idx']}"
                )
            choice.content = choice_data["content"]

    return summary


def print_summary(prefix: str, summaries: list[ImportSummary]) -> None:
    print(prefix)
    for summary in summaries:
        print(
            f"- {summary.year} {summary.area.value}: "
            f"{summary.problem_count} problems, "
            f"{summary.passage_count} passages, "
            f"{summary.choice_count} choices"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import parsed LEET JSON data into PostgreSQL.")
    parser.add_argument("--parsed-dir", default=Path("data/parsed"), type=Path)
    parser.add_argument("--year", dest="years", action="append", type=int, default=None)
    parser.add_argument(
        "--area",
        dest="areas",
        action="append",
        choices=[area.value for area in ProblemArea],
        default=None,
    )
    parser.add_argument("--replace", action="store_true", help="Replace existing exam rows for the selected files.")
    parser.add_argument("--update-text-only", action="store_true", help="Update existing passage, problem, and choice text without replacing rows.")
    parser.add_argument("--dry-run", action="store_true", help="Validate files without writing to the database.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    years = args.years or [2026]
    areas = [ProblemArea(area) for area in (args.areas or [area.value for area in ProblemArea])]
    paths = collect_paths(args.parsed_dir, years, areas)
    payloads = [load_json(path) for path in paths]
    summaries = [validate_payload(path, payload) for path, payload in zip(paths, payloads)]

    if args.dry_run:
        print_summary("Validated parsed data:", summaries)
        return

    if args.replace and args.update_text_only:
        raise ValueError("--replace and --update-text-only cannot be used together")

    with SessionLocal() as db:
        if args.update_text_only:
            imported = [update_existing_text(db, path, payload) for path, payload in zip(paths, payloads)]
        else:
            imported = [import_payload(db, path, payload, replace=args.replace) for path, payload in zip(paths, payloads)]
        db.commit()

    prefix = "Updated parsed text:" if args.update_text_only else "Imported parsed data:"
    print_summary(prefix, imported)


if __name__ == "__main__":
    main()
