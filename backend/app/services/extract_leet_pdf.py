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

# Emitted when a problem booklet is an image-only scan with no OCR override yet.
# Such a source is "staged" (PDF + answer key present) but not parseable, so the
# extractor records it in the manifest without writing a half-empty JSON file.
PENDING_OCR_WARNING = "problem_pdf_text_empty_and_no_ocr_override"

# area dir name -> (problem/answer pdf filename stem, expected problem count)
AREA_SPECS: dict[str, tuple[str, int]] = {
    "reading_comprehension": ("reading", 30),
    "reasoning_argumentation": ("reasoning", 40),
}


@dataclass(frozen=True)
class SourceSet:
    year: int
    area: str
    problem_pdf: Path
    answer_pdf: Path
    expected_count: int
    # Optional manual overrides for scanned (image-only) PDFs that pypdf cannot read.
    answer_override: Path | None = None  # data/answers/{year}_{area}.json
    ocr_text: Path | None = None  # data/ocr/{year}_{area}.txt


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


def load_answer_override(path: Path) -> dict[int, int]:
    """Load a manually transcribed answer key for image-only answer PDFs."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return {int(number): int(index) for number, index in data["answers"].items()}


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


CHOICE_LABELS = ["①", "②", "③", "④", "⑤"]


def locate_trailing_choice_markers(block: str) -> list[int] | None:
    """Return the positions of the final ①②③④⑤ run in ``block``.

    LEET stems often contain stray circled numbers (e.g. references to ㉠㉡ or
    to the options themselves), so a naive split over every ①..⑤ over-counts the
    choices. The real choices are always the trailing run, so we walk backwards
    from the last ⑤ and find each preceding label before it.
    """
    positions: list[int] = []
    search_end = len(block)
    for label in reversed(CHOICE_LABELS):
        index = block.rfind(label, 0, search_end)
        if index == -1:
            return None
        positions.append(index)
        search_end = index
    positions.reverse()
    return positions


def split_problem_and_choices(block: str, number: int) -> tuple[str, list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    block = re.sub(rf"^{number}\.\s*", "", block).strip()

    positions = locate_trailing_choice_markers(block)
    if positions is None:
        found = sum(1 for label in CHOICE_LABELS if label in block)
        warnings.append(f"expected_5_choices_found_{found}")
        return block, [], warnings

    question_text = block[: positions[0]].strip()
    bounds = positions + [len(block)]
    choices: list[dict[str, Any]] = []
    for index, label in enumerate(CHOICE_LABELS):
        start = bounds[index] + len(label)
        content = remove_exam_footer(block[start : bounds[index + 1]].strip())
        choices.append(
            {
                "idx": ANSWER_LABELS[label],
                "label": label,
                "content": content,
            }
        )
    return question_text, choices, warnings


def remove_exam_footer(text: str) -> str:
    # Page footers/headers bleed into the last choice of each page. Spacing in the
    # PDF text layer varies by year (some have no spaces at all), so every marker
    # tolerates optional whitespace. A leading page number glued to the choice is
    # stripped together with the footer it precedes.
    footer_patterns = [
        # Page footer that bleeds in mid-page: "\n420\n홀수형4 추 리 논 증" or
        # "\n3추리논증\n3 20\n홀수형". Anchored on a line-leading page number that is
        # immediately followed by the "20"/area-name footer and a nearby "홀수형".
        r"\n\s*\d+\s*(?:20(?!\d)|추\s*리\s*논\s*증|언\s*어\s*이\s*해)(?=[\s\S]{0,30}홀수형)",
        r"\s*\d*\s*20\d{2}\s*학년도\s*법학적성시험",
        r"\s*법학적성시험",
        r"\s*제\s*[12]\s*교시",
        r"\s*성명\s*수험번호",
        r"\s*홀수형",
        r"\s*\*\s*확인\s*사항",
    ]
    earliest = len(text)
    for pattern in footer_patterns:
        match = re.search(pattern, text)
        if match:
            earliest = min(earliest, match.start())
    return text[:earliest].strip()


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
    warnings: list[str] = []

    problem_text, problem_pages = extract_pdf_text(source.problem_pdf)
    problem_text = compact_text(problem_text)
    problem_text_source = "pdf_text"
    if not problem_text and source.ocr_text and source.ocr_text.exists():
        problem_text = compact_text(source.ocr_text.read_text(encoding="utf-8"))
        problem_text_source = "ocr_text"
    elif not problem_text:
        warnings.append(PENDING_OCR_WARNING)

    answer_text, answer_pages = extract_pdf_text(source.answer_pdf)
    answer_text = compact_text(answer_text)
    answers = parse_answers(answer_text)
    answer_source = "pdf_text"
    if len(answers) < source.expected_count and source.answer_override and source.answer_override.exists():
        answers = load_answer_override(source.answer_override)
        answer_source = "override"

    passages: list[dict[str, Any]] = []
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
            "problem_text_source": problem_text_source,
            "answer_source": answer_source,
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
    """Discover every {year}_{stem}.pdf problem booklet under each area directory.

    New years only need their PDFs dropped into the area folders (plus a manual
    answer override under data/answers when the answer PDF is image-only).
    """
    sources: list[SourceSet] = []
    answers_dir = data_dir / "answers"
    ocr_dir = data_dir / "ocr"
    for area, (stem, expected_count) in AREA_SPECS.items():
        area_dir = data_dir / area
        if not area_dir.is_dir():
            continue
        for problem_pdf in area_dir.glob(f"*_{stem}.pdf"):
            match = re.fullmatch(rf"(\d{{4}})_{stem}\.pdf", problem_pdf.name)
            if not match:
                continue
            year = int(match.group(1))
            sources.append(
                SourceSet(
                    year=year,
                    area=area,
                    problem_pdf=problem_pdf,
                    answer_pdf=area_dir / f"{year}_{stem}_answers.pdf",
                    expected_count=expected_count,
                    answer_override=answers_dir / f"{year}_{area}.json",
                    ocr_text=ocr_dir / f"{year}_{area}.txt",
                )
            )
    return sorted(sources, key=lambda source: (source.year, source.area))


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract LEET PDF text into app-friendly JSON.")
    parser.add_argument("--data-dir", default="data", type=Path)
    parser.add_argument("--out-dir", default="data/parsed", type=Path)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for source in discover_sources(args.data_dir):
        parsed = parse_source(source)
        pending = PENDING_OCR_WARNING in parsed["metadata"]["extraction_warnings"]
        out_path = args.out_dir / f"{source.year}_{source.area}.json"
        if pending:
            # Scanned booklet awaiting an OCR override: keep it out of data/parsed
            # so the importer does not see a half-empty file. Drop any stale output.
            out_path.unlink(missing_ok=True)
        else:
            out_path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest.append(
            {
                "year": source.year,
                "area": source.area,
                "status": "pending_ocr" if pending else "ready",
                "path": None if pending else str(out_path),
                **parsed["metadata"],
            }
        )

    manifest_path = args.out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
