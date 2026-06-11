from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader


ANSWER_LABELS = {"①": 1, "②": 2, "③": 3, "④": 4, "⑤": 5}
ANSWER_LABEL_BY_INDEX = {value: key for key, value in ANSWER_LABELS.items()}


@dataclass(frozen=True)
class SourceSet:
    year: int
    area: str
    problem_pdf: Path
    answer_pdf: Path
    expected_count: int


def extract_pdf_text(path: Path) -> tuple[str, int]:
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages), len(reader.pages)


def compact_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_answer_variant_section(answer_text: str, variant: str = "홀수형") -> str:
    start = answer_text.find(variant)
    if start == -1:
        return answer_text

    other_variants = ["홀수형", "짝수형"]
    end_candidates = [
        answer_text.find(other, start + len(variant))
        for other in other_variants
        if other != variant and answer_text.find(other, start + len(variant)) != -1
    ]
    end = min(end_candidates) if end_candidates else len(answer_text)
    return answer_text[start:end]


def parse_answers(answer_text: str, variant: str = "홀수형") -> dict[int, int]:
    answer_text = extract_answer_variant_section(answer_text, variant)
    squashed = re.sub(r"\s+", "", answer_text)
    answers: dict[int, int] = {}
    for number, label in re.findall(r"(\d{1,2})([①②③④⑤])", squashed):
        answers[int(number)] = ANSWER_LABELS[label]
    return answers


def find_reading_groups(text: str) -> list[tuple[int, int, str]]:
    matches = list(re.finditer(r"\[(\d{1,2})~(\d{1,2})\]\s*다음\s*글을\s*읽고\s*물음에\s*답하시오\.?", text))
    groups: list[tuple[int, int, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        groups.append((int(match.group(1)), int(match.group(2)), text[start:end].strip()))
    return groups


def find_number_span(text: str, number: int, start_at: int = 0) -> int:
    pattern = re.compile(rf"(?<!\d\.){number}\.\s*")
    match = pattern.search(text, start_at)
    return match.start() if match else -1


def split_expected_numbered_blocks(text: str, first: int, last: int) -> dict[int, str]:
    starts: dict[int, int] = {}
    search_from = 0
    for number in range(first, last + 1):
        pos = find_number_span(text, number, search_from)
        if pos == -1:
            continue
        starts[number] = pos
        search_from = pos + len(str(number)) + 1

    blocks: dict[int, str] = {}
    ordered = sorted(starts.items())
    for index, (number, start) in enumerate(ordered):
        end = ordered[index + 1][1] if index + 1 < len(ordered) else len(text)
        blocks[number] = text[start:end].strip()
    return blocks


def split_problem_and_choices(block: str, number: int) -> tuple[str, list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    block = re.sub(rf"^{number}\.\s*", "", block).strip()
    parts = re.split(r"([①②③④⑤])", block)
    if len(parts) < 3:
        warnings.append("choice_markers_not_found")
        return block, [], warnings

    question_text = parts[0].strip()
    choices: list[dict[str, Any]] = []
    for index in range(1, len(parts), 2):
        label = parts[index]
        content = parts[index + 1].strip() if index + 1 < len(parts) else ""
        choices.append(
            {
                "idx": ANSWER_LABELS[label],
                "label": label,
                "content": content,
            }
        )

    if len(choices) != 5:
        warnings.append(f"expected_5_choices_found_{len(choices)}")
    return question_text, choices, warnings


def parse_reading(source: SourceSet, text: str, answers: dict[int, int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    passages: list[dict[str, Any]] = []
    problems: list[dict[str, Any]] = []
    warnings: list[str] = []
    groups = find_reading_groups(text)
    if not groups:
        warnings.append("reading_passage_groups_not_found")

    for group_index, (first, last, group_text) in enumerate(groups, start=1):
        first_question_pos = find_number_span(group_text, first)
        if first_question_pos == -1:
            warnings.append(f"group_{first}_{last}_first_question_not_found")
            passage_text = group_text
            question_zone = ""
        else:
            passage_text = group_text[:first_question_pos].strip()
            question_zone = group_text[first_question_pos:].strip()

        passage_id = f"{source.year}_{source.area}_passage_{group_index:02d}"
        passages.append(
            {
                "id": passage_id,
                "question_numbers": list(range(first, last + 1)),
                "content": passage_text,
            }
        )

        blocks = split_expected_numbered_blocks(question_zone, first, last)
        for number in range(first, last + 1):
            raw_block = blocks.get(number, "")
            question_text, choices, problem_warnings = split_problem_and_choices(raw_block, number) if raw_block else ("", [], ["problem_block_not_found"])
            problems.append(
                {
                    "id": f"{source.year}_{source.area}_{number:02d}",
                    "year": source.year,
                    "area": source.area,
                    "number": number,
                    "passage_id": passage_id,
                    "question_text": question_text,
                    "choices": choices,
                    "answer_index": answers.get(number),
                    "answer_label": ANSWER_LABEL_BY_INDEX.get(answers[number]) if number in answers else None,
                    "raw_block": raw_block,
                    "extraction_warnings": problem_warnings,
                }
            )
    return passages, problems, warnings


def parse_reasoning(source: SourceSet, text: str, answers: dict[int, int]) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[dict[str, Any]] = []
    warnings: list[str] = []
    blocks = split_expected_numbered_blocks(text, 1, source.expected_count)
    if len(blocks) != source.expected_count:
        warnings.append(f"expected_{source.expected_count}_problems_found_{len(blocks)}")

    for number in range(1, source.expected_count + 1):
        raw_block = blocks.get(number, "")
        question_text, choices, problem_warnings = split_problem_and_choices(raw_block, number) if raw_block else ("", [], ["problem_block_not_found"])
        problems.append(
            {
                "id": f"{source.year}_{source.area}_{number:02d}",
                "year": source.year,
                "area": source.area,
                "number": number,
                "passage_id": None,
                "question_text": question_text,
                "choices": choices,
                "answer_index": answers.get(number),
                "answer_label": ANSWER_LABEL_BY_INDEX.get(answers[number]) if number in answers else None,
                "raw_block": raw_block,
                "extraction_warnings": problem_warnings,
            }
        )
    return problems, warnings


def parse_source(source: SourceSet) -> dict[str, Any]:
    problem_text, problem_pages = extract_pdf_text(source.problem_pdf)
    answer_text, answer_pages = extract_pdf_text(source.answer_pdf)
    problem_text = compact_text(problem_text)
    answer_text = compact_text(answer_text)
    answers = parse_answers(answer_text)

    passages: list[dict[str, Any]] = []
    warnings: list[str] = []
    if source.area == "reading_comprehension":
        passages, problems, parse_warnings = parse_reading(source, problem_text, answers)
        warnings.extend(parse_warnings)
    else:
        problems, parse_warnings = parse_reasoning(source, problem_text, answers)
        warnings.extend(parse_warnings)

    if len(answers) != source.expected_count:
        warnings.append(f"expected_{source.expected_count}_answers_found_{len(answers)}")

    return {
        "metadata": {
            "year": source.year,
            "area": source.area,
            "problem_pdf": str(source.problem_pdf),
            "answer_pdf": str(source.answer_pdf),
            "problem_pages": problem_pages,
            "answer_pages": answer_pages,
            "expected_problem_count": source.expected_count,
            "extracted_problem_count": len(problems),
            "extracted_answer_count": len(answers),
            "extraction_warnings": warnings,
        },
        "exam": {
            "year": source.year,
            "round": "LEET",
            "area": source.area,
        },
        "passages": passages,
        "problems": problems,
    }


def discover_sources(data_dir: Path) -> list[SourceSet]:
    return [
        SourceSet(
            year=2025,
            area="reading_comprehension",
            problem_pdf=data_dir / "reading_comprehension" / "2025_reading.pdf",
            answer_pdf=data_dir / "reading_comprehension" / "2025_reading_answers.pdf",
            expected_count=30,
        ),
        SourceSet(
            year=2026,
            area="reading_comprehension",
            problem_pdf=data_dir / "reading_comprehension" / "2026_reading.pdf",
            answer_pdf=data_dir / "reading_comprehension" / "2026_reading_answers.pdf",
            expected_count=30,
        ),
        SourceSet(
            year=2025,
            area="reasoning_argumentation",
            problem_pdf=data_dir / "reasoning_argumentation" / "2025_reasoning.pdf",
            answer_pdf=data_dir / "reasoning_argumentation" / "2025_reasoning_answers.pdf",
            expected_count=40,
        ),
        SourceSet(
            year=2026,
            area="reasoning_argumentation",
            problem_pdf=data_dir / "reasoning_argumentation" / "2026_reasoning.pdf",
            answer_pdf=data_dir / "reasoning_argumentation" / "2026_reasoning_answers.pdf",
            expected_count=40,
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract LEET PDF text into app-friendly JSON.")
    parser.add_argument("--data-dir", default="data", type=Path)
    parser.add_argument("--out-dir", default="data/parsed", type=Path)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for source in discover_sources(args.data_dir):
        parsed = parse_source(source)
        out_path = args.out_dir / f"{source.year}_{source.area}.json"
        out_path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest.append(
            {
                "year": source.year,
                "area": source.area,
                "path": str(out_path),
                **parsed["metadata"],
            }
        )

    manifest_path = args.out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
