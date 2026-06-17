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

## 표/그림/수식 구조 보존 원칙

현재 JSON 구조는 `question_text`와 `passages[].content`에 본문을 문자열로 저장한다.
이 방식은 일반 문항에는 단순하지만, 표·그림·수식·보기 박스처럼 레이아웃 자체가
풀이 정보인 문항에서는 원문 구조를 잃을 수 있다. 예를 들어 `pdftotext -raw`는
공백 누락을 줄이는 데 유용하지만 표의 셀 경계, 병합 헤더, 선, 열 좌표를
문자열에 보존하지 못한다.

향후 표·그림·수식이 포함된 문항은 다음 네 가지 기준을 함께 적용한다.

1. `pdftotext -bbox-layout` 기반 표 감지
   - `pdftotext -raw`를 기본 추출에 사용하되, 표 후보가 있는 문항은
     `pdftotext -bbox-layout` 좌표 정보를 함께 확인한다.
   - 단어들의 x좌표가 여러 열로 반복 정렬되거나, 같은 y좌표에 숫자 셀이
     여러 개 배치되면 표 후보로 본다.
2. `question_blocks` 구조화
   - 표·그림·수식·보기 박스를 `question_text`에 줄글로 합치지 않고,
     `paragraph`, `table`, `image`, `formula` 같은 블록 타입으로 분리하는
     확장 스키마를 우선 고려한다.
   - 병합 헤더는 하위 헤더와 결합해 사람이 읽을 수 있는 열 이름으로 만든다.
     예: `갑국` + `2023년` → `갑국 2023년`.
3. 프론트엔드 블록 렌더링
   - 프론트는 단일 문자열을 `pre-wrap`으로 출력하는 방식만 사용하지 않고,
     블록 타입에 따라 문단, 표, 이미지, 수식을 각각 렌더링한다.
   - 표 블록은 HTML `<table>` 또는 동등한 접근 가능한 UI로 렌더링한다.
4. 검증 실패 시 `needs_review` 처리
   - 표 후보가 감지되었는데 `table` 블록이 없으면 자동 검증에서 실패시키거나
     `needs_review: true`와 warning을 남긴다.
   - 표 복원이 불확실한 경우 임의로 줄글화하지 않는다.

표 후보 감지 기준:

- 본문에 "표는", "다음 표", "나타낸다" 같은 표현이 있고 이후 숫자 행이 이어지는 경우
- `구분(단위)`, 연도, 국가명, 조건명 등이 헤더처럼 반복되는 경우
- 한 줄에 숫자 값이 3개 이상 반복되는 경우
- 여러 행이 비슷한 개수의 값으로 정렬되는 경우
- `pdftotext -bbox-layout`에서 단어들의 x좌표가 여러 열로 반복 정렬되는 경우

권장 확장 출력 예시:

```json
{
  "question_blocks": [
    { "type": "paragraph", "text": "문제 본문" },
    {
      "type": "table",
      "columns": ["구분(단위)", "갑국 2023년", "갑국 2024년", "을국 2023년", "을국 2024년"],
      "rows": [
        ["GDP(억 달러)", "100", "200", "100", "200"],
        ["수출의존도(%)", "10", "20", "20", "10"],
        ["수입의존도(%)", "30", "20", "5", "15"]
      ]
    },
    { "type": "paragraph", "text": "<보 기>..." }
  ],
  "needs_review": false,
  "warnings": []
}
```

파싱 프롬프트나 수동 OCR override를 작성할 때는 다음 원칙을 포함한다.

- 표를 일반 문장으로 합치지 않는다.
- 병합 헤더는 하위 헤더와 결합해 열 이름으로 만든다.
- 셀 개수가 행마다 일치하는지 검증한다.
- 표 복원이 불확실하면 `needs_review: true`와 warning을 남긴다.
- 페이지 번호, 과목명, `홀수형`, 확인 사항은 본문/선택지에 포함하지 않는다.

## 정답 형식

정답표 PDF에는 `홀수형`과 `짝수형`이 함께 들어 있고, 문제 booklet은 모두 `홀수형`이다.
정답표가 텍스트 PDF면 추출기가 홀수형 구간만 잘라 사용하고(2026), 이미지 스캔이면
`data/answers/<year>_<area>.json`의 홀수형 정답(override)을 사용한다(2022~2025).
