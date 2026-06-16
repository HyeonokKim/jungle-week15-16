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
AUTH_DEV_MODE=true
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/auth/google/callback
JWT_SECRET_KEY=change-me-in-env
OPENAI_API_KEY=
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_AI_EXPLANATION_MODEL=gpt-4o-mini
AI_EXPLANATION_CANDIDATE_COUNT=3
NOTION_TOKEN=
NOTION_VERSION=2026-03-11
NOTION_PAGE_ID=
```

`AUTH_DEV_MODE=true`일 때는 토큰이 없어도 개발 사용자(`id=1`)로 API를 사용할 수 있다. 실제 인증 흐름을 강제하려면 `AUTH_DEV_MODE=false`로 바꾼다.

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

현재 인증 전 개발 단계에서는 서버의 `get_current_user()` 의존성이 기본 개발 사용자(`id=1`)를 반환한다.
Google OAuth 설정을 넣으면 `/auth/google/login`에서 로그인 플로우를 시작하고, 콜백에서 발급한 JWT를 프론트로 전달한다.
Google 로그인으로 새 사용자가 들어오면 `users.auth_provider='google'`, `users.provider_id=<Google sub>`, `password_hash=null`로 저장하고, `user_settings` 기본 행을 함께 만든다. JWT 자체는 DB에 저장하지 않는다.

```bash
curl 'http://127.0.0.1:8000/auth/google/login'
curl 'http://127.0.0.1:8000/auth/me'
curl 'http://127.0.0.1:8000/daily'
curl 'http://127.0.0.1:8000/practice/next'
curl -X POST 'http://127.0.0.1:8000/attempts' \
  -H 'Content-Type: application/json' \
  -d '{"problem_id":1,"selected_index":4,"reasoning":"선택 근거"}'
curl 'http://127.0.0.1:8000/problems/1/board'
curl 'http://127.0.0.1:8000/me/posts'
curl 'http://127.0.0.1:8000/stats/me'
curl 'http://127.0.0.1:8000/settings/me'
curl -X PUT 'http://127.0.0.1:8000/settings/me' \
  -H 'Content-Type: application/json' \
  -d '{"problem_scope":"all_random","timer_limit_sec":180,"review_interval_days":3}'
curl -X POST 'http://127.0.0.1:8000/me/weekly-summary/notion'
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

추가 연습 문제를 오늘의 문제와 유사한 문제로 추천하려면 문제 적재 후 임베딩을 생성한다. `--dry-run`은 OpenAI API를 호출하지 않고 생성/갱신 대상만 확인한다.

```bash
python3 -m backend.app.services.problem_embeddings --dry-run
python3 -m backend.app.services.problem_embeddings
```

## 현재 작성된 스키마

- `users`
- `exams`
- `passages`
- `problems`
- `problem_embeddings`
- `ai_explanations`
- `choices`
- `attempts`
- `user_daily`
- `board_posts`
- `board_comments`
- `user_settings`
- `review_queue`

## MVP smoke 검증

인증 값이 없어서 Google OAuth 실제 연결 검증을 못 하는 경우에도, 핵심 학습 플로우는 임시 사용자로 검증할 수 있다.

```bash
python3 -m backend.app.services.smoke_mvp
```

이 검증은 데일리 문제 배정, 제출/채점, 게시판 자동 등록, 내 게시글/시도 기록, 추가 연습, 오답 복습 큐 생성과 해결까지 확인한다.

## 다음 단계

Google OAuth Client ID/Secret을 `.env`에 넣은 뒤 브라우저에서 실제 로그인 콜백을 검증한다.
