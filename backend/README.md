# Backend Setup

이 백엔드는 PostgreSQL 전용으로 구성한다. 개발 DB 이름은 `haripool`을 기준으로 한다.

## 1. 의존성 설치

```bash
python3 -m pip install -r requirements.txt
```

## 2. PostgreSQL DB 생성

```bash
createdb haripool
```

## 3. 환경 변수 설정

```bash
cp .env.example .env
```

필요하면 `.env`의 접속 정보를 로컬 PostgreSQL 계정에 맞게 바꾼다.

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/haripool
```

## 4. 마이그레이션 적용

```bash
alembic upgrade head
```

현재 초기 마이그레이션은 `backend/alembic/versions/0001_create_initial_schema.py`에 있다.

## 5. API 서버 실행

```bash
uvicorn backend.app.main:app --reload
```

기본 헬스 체크 엔드포인트는 `GET /health`다.

현재 인증 전 개발 단계에서는 `user_id=1`을 기본 개발 사용자로 사용한다.

```bash
curl 'http://127.0.0.1:8000/daily?user_id=1'
curl -X POST 'http://127.0.0.1:8000/attempts' \
  -H 'Content-Type: application/json' \
  -d '{"user_id":1,"problem_id":1,"selected_index":4,"reasoning":"선택 근거"}'
```

## 6. 2026년 문제 데이터 적재

2025년 정답표는 이미지 기반 PDF라 자동 정답 추출을 보류한다. 개발 초기 DB에는 정답 검증이 끝난 2026년 언어이해/추리논증만 적재한다.

먼저 JSON 품질을 검증한다.

```bash
python3 -m backend.app.services.import_leet_data --dry-run
```

문제가 없으면 DB에 적재한다.

```bash
python3 -m backend.app.services.import_leet_data
```

이미 적재된 2026년 시험 데이터를 다시 넣어야 할 때만 `--replace`를 붙인다.

```bash
python3 -m backend.app.services.import_leet_data --replace
```

## 현재 작성된 스키마

- `users`
- `exams`
- `passages`
- `problems`
- `choices`
- `attempts`
- `user_daily`
- `board_posts`
- `user_settings`
- `review_queue`

## 다음 단계

`/daily`, `/practice/next`, `/attempts` API를 작성해서 2026년 문제를 실제 풀이 플로우로 연결한다.
