# Parsed LEET Data

이 폴더는 `data/` 아래의 LEET PDF를 앱에서 읽기 쉬운 JSON으로 변환한 중간 산출물이다.

## 파이프라인 개요

```
data/<area>/<year>_<stem>.pdf            # 문제 booklet (홀수형)
data/<area>/<year>_<stem>_answers.pdf    # 정답표
data/answers/<year>_<area>.json          # 정답 override (정답표가 이미지 스캔일 때)
data/ocr/<year>_<area>.txt               # 본문 OCR override (문제 PDF가 이미지 스캔일 때)
        │
        ▼  extract_leet_pdf.py
data/parsed/<year>_<area>.json           # 적재용 JSON (검증 통과한 회차만)
        │
        ▼  import_leet_data.py
PostgreSQL (exams / passages / problems / choices)
```

`<area>` ∈ {`reading_comprehension`(30문항), `reasoning_argumentation`(40문항)},
`<stem>` ∈ {`reading`, `reasoning`}.

## 새 회차 추가 방법

1. 문제/정답 PDF를 `data/reading_comprehension/`, `data/reasoning_argumentation/`에
   `<year>_reading.pdf` 형식으로 넣는다. (booklet은 **홀수형** 기준)
2. 정답표 PDF가 이미지 스캔이면 `data/answers/<year>_<area>.json`에 홀수형 정답을 적는다.
   (현재 2022~2025 정답표는 모두 이미지 스캔이라 override가 필요하다.)
3. 문제 PDF가 이미지 스캔이면(예: 2022·2023) `data/ocr/<year>_<area>.txt`에 본문을 채운다.
   채우기 전까지 해당 회차는 `pending_ocr`로 표시되고 `data/parsed`에 기록되지 않는다.
4. 추출 → 적재:

```bash
python3 backend/app/services/extract_leet_pdf.py --data-dir data --out-dir data/parsed
python3 -m backend.app.services.import_leet_data --dry-run   # 검증만
python3 -m backend.app.services.import_leet_data             # 준비된 회차 전부 적재
```

`discover_sources`/`discover_parsed_years`가 연도를 자동 인식하므로 코드 수정은 필요 없다.

## 현재 상태

| 회차 | 본문 | 정답 | 상태 |
| --- | --- | --- | --- |
| 2024 언어이해/추리논증 | PDF 텍스트 | 정답 override | ready (적재됨) |
| 2025 언어이해/추리논증 | PDF 텍스트 | 정답 override | ready (적재됨) |
| 2026 언어이해/추리논증 | PDF 텍스트 | PDF 텍스트 | ready (적재됨) |
| 2022 언어이해/추리논증 | **스캔 이미지 → OCR 필요** | 정답 override 완료 | pending_ocr |
| 2023 언어이해/추리논증 | **스캔 이미지 → OCR 필요** | 정답 override 완료 | pending_ocr |

2022·2023은 문제 PDF가 2단 레이아웃 스캔 이미지라 `pypdf`/tesseract 자동 추출이
불가능하다. `data/ocr/<year>_<area>.txt`만 채우면 위 추출/적재 명령으로 자동 편입된다.
(`data/ocr/README.md` 참고.)

## JSON 구조

```json
{
  "metadata": {
    "year": 2024,
    "area": "reading_comprehension",
    "problem_text_source": "pdf_text",   // 또는 "ocr_text"
    "answer_source": "override",          // 또는 "pdf_text"
    "extracted_problem_count": 30,
    "extracted_answer_count": 30,
    "extraction_warnings": []
  },
  "exam": { "year": 2024, "round": "LEET", "area": "reading_comprehension" },
  "passages": [ { "id": "...", "question_numbers": [1,2,3], "content": "지문" } ],
  "problems": [
    {
      "id": "2024_reading_comprehension_01",
      "number": 1,
      "passage_id": "2024_reading_comprehension_passage_01",
      "question_text": "문제 본문",
      "choices": [ { "idx": 1, "label": "①", "content": "선택지" } ],
      "answer_index": 3,
      "answer_label": "③",
      "raw_block": "원문 블록(검수용)",
      "extraction_warnings": []
    }
  ]
}
```

`raw_block`과 `extraction_warnings`는 검수용 필드다. 운영 DB에는 넣지 않는다.

## 정답 형식

정답표 PDF에는 `홀수형`과 `짝수형`이 함께 들어 있고, 문제 booklet은 모두 `홀수형`이다.
정답표가 텍스트 PDF면 추출기가 홀수형 구간만 잘라 사용하고(2026), 이미지 스캔이면
`data/answers/<year>_<area>.json`의 홀수형 정답(override)을 사용한다(2022~2025).
