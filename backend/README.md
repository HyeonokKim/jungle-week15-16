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
