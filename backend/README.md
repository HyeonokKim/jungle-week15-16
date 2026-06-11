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

`data/parsed/*.json`을 읽어서 `exams`, `passages`, `problems`, `choices`에 적재하는 seed/import 스크립트를 작성한다.
