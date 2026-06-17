# OCR 본문 override

스캔 이미지 PDF라 `pypdf`로 본문 텍스트를 추출할 수 없는 회차를 위한 폴더다.
`extract_leet_pdf.py`는 문제 PDF에서 텍스트가 안 나오면 여기 있는
`<year>_<area>.txt`를 본문으로 사용한다. (`<area>` = `reading_comprehension` | `reasoning_argumentation`)

## 현재 대기 중

- `2022_reading_comprehension.txt` (15p 스캔)
- `2022_reasoning_argumentation.txt` (20p 스캔)
- `2023_reading_comprehension.txt` (15p 스캔)
- `2023_reasoning_argumentation.txt` (20p 스캔)

이 파일들이 채워지기 전까지 2022·2023은 `pending_ocr` 상태이며 `data/parsed`에 기록되지
않아 적재 대상에서 자동 제외된다. (정답표 override는 `data/answers/`에 이미 준비되어 있다.)

## 텍스트 형식

추출기의 파서는 `pypdf` 출력과 동일한 형태를 기대한다. 본문을 PDF에 적힌 순서대로
(2단이면 왼쪽 열 → 오른쪽 열) 옮긴다.

- **언어이해**: 지문 묶음마다 머리글 `[1~3] 다음 글을 읽고 물음에 답하시오.` 를 그대로 적고,
  이어서 지문 본문, 그다음 `1.`, `2.` … 문제와 `① ② ③ ④ ⑤` 선택지를 적는다.
- **추리논증**: 지문 머리글 없이 `1.` … `40.` 문제와 선택지만 순서대로 적는다.

선택지 기호는 반드시 원문자 `①②③④⑤`를 쓴다(파서가 이것으로 선택지를 분리한다).
그래프·도표가 핵심인 일부 문제는 텍스트로 완전히 복원되지 않으니 검수 시 표시해 둔다.

채운 뒤:

```bash
python3 backend/app/services/extract_leet_pdf.py --data-dir data --out-dir data/parsed
python3 -m backend.app.services.import_leet_data
```
