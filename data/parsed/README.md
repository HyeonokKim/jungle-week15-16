# Parsed LEET Data

이 폴더는 `data/` 아래의 LEET PDF를 앱에서 읽기 쉬운 JSON으로 변환한 중간 산출물이다.

## 생성 명령

```bash
python3 backend/app/services/extract_leet_pdf.py --data-dir data --out-dir data/parsed
```

## 파일

- `manifest.json`: 파일별 추출 현황 요약
- `2025_reading_comprehension.json`: 2025 언어이해
- `2026_reading_comprehension.json`: 2026 언어이해
- `2025_reasoning_argumentation.json`: 2025 추리논증
- `2026_reasoning_argumentation.json`: 2026 추리논증

## JSON 구조

```json
{
  "metadata": {
    "year": 2026,
    "area": "reading_comprehension",
    "problem_pdf": "data/reading_comprehension/2026_reading.pdf",
    "answer_pdf": "data/reading_comprehension/2026_reading_answers.pdf",
    "problem_pages": 15,
    "answer_pages": 2,
    "expected_problem_count": 30,
    "extracted_problem_count": 30,
    "extracted_answer_count": 30,
    "extraction_warnings": []
  },
  "exam": {
    "year": 2026,
    "round": "LEET",
    "area": "reading_comprehension"
  },
  "passages": [
    {
      "id": "2026_reading_comprehension_passage_01",
      "question_numbers": [1, 2, 3],
      "content": "지문 본문"
    }
  ],
  "problems": [
    {
      "id": "2026_reading_comprehension_01",
      "year": 2026,
      "area": "reading_comprehension",
      "number": 1,
      "passage_id": "2026_reading_comprehension_passage_01",
      "question_text": "문제 본문",
      "choices": [
        {
          "idx": 1,
          "label": "①",
          "content": "선택지 본문"
        }
      ],
      "answer_index": 4,
      "answer_label": "④",
      "raw_block": "PDF에서 추출한 원문 블록",
      "extraction_warnings": []
    }
  ]
}
```

## 현재 추출 품질

| 파일 | 문제 | 지문 | 정답 | 주의 |
| --- | ---: | ---: | ---: | --- |
| 2025 언어이해 | 30/30 | 10 | 0/30 | 정답표 PDF 텍스트 추출 실패, 본문 공백 손실 있음 |
| 2026 언어이해 | 30/30 | 10 | 30/30 | 양호 |
| 2025 추리논증 | 40/40 | 0 | 0/40 | 정답표 PDF 텍스트 추출 실패, 일부 선택지 분리 경고 있음 |
| 2026 추리논증 | 40/40 | 0 | 40/40 | 양호 |

## DB 매핑 방향

- `exam` -> `exams`
- `passages[]` -> `passages`
- `problems[]` -> `problems`
- `problems[].choices[]` -> `choices`
- `answer_index` -> `problems.answer_index`

`raw_block`과 `extraction_warnings`는 검수용 필드다. 운영 DB에는 넣지 않거나, 임시 적재 테이블에만 보관한다.

## 정답 형식

정답표 PDF에는 `홀수형`과 `짝수형`이 함께 들어 있다. 현재 추출 스크립트는 문제 PDF가 `홀수형`이므로 정답도 `홀수형` 구간만 잘라서 `answer_index`와 `answer_label`에 저장한다.

2025 정답표는 현재 `pypdf` 텍스트 추출 결과가 비어 있어 정답을 자동 추출하지 못했다. 2025 정답은 OCR 또는 수동 입력으로 보강해야 한다.
