# PROJECT.md

LEET 데일리 — 로스쿨 준비생을 위한 "하루 한 문제" LEET 풀이 사이트.

기준 기획 문서: Notion "[WEEK16] 기획". 이 문서는 그 기획을 제품/기술 설계 관점으로 정리한 것이다. 충돌 시 기획 문서가 우선한다.

## 1. 프로젝트 개요

- **목표**: 사용자가 매일 LEET 기출 한 문제를 풀며 학습 습관과 성취감을 형성한다.
- **타겟 사용자**: 국내 로스쿨(법학전문대학원) 준비생.
- **핵심 가치**: "많이 푸는 것"이 아니라 **오늘 한 문제를 풀었다는 완결감** + 답을 보기 전에 자기 추론을 적고 공유하는 **학습 커뮤니티** 경험.
- **다루는 영역**: 언어이해, 추리논증 (둘 다 5지선다 → 자동채점). **논술은 주관식이라 제외.**

## 2. 기술 스택

| 레이어 | 기술 |
|--------|------|
| 프론트엔드 | React, TailwindCSS |
| 백엔드 | FastAPI (Python) |
| ORM | SQLAlchemy (+ Alembic 마이그레이션) |
| DB | PostgreSQL |
| 인증 | 소셜 OAuth (구글) + 자체 JWT |

## 3. 제안 디렉터리 구조

```
/backend
  /app
    /models        # SQLAlchemy 모델
    /schemas       # Pydantic 스키마
    /api           # 라우터 (auth, daily, attempts, board, stats, settings)
    /core          # 설정, 보안(JWT), 의존성
    /services      # 비즈니스 로직 (스트릭, 문제 배정, 오답 복습 스케줄링)
    main.py
  /alembic         # 마이그레이션
/frontend
  /src
    /pages         # Login, Main, Board, MyPage
    /components
    /api           # 백엔드 호출 클라이언트
    /hooks
```

## 4. 페이지 구성 (프론트엔드 4개)

1. **로그인 페이지** — 구글 소셜 로그인, (최초 1회) 닉네임/아이디 생성.
2. **메인 페이지** — 잔디 캘린더/스트릭, 오늘의 문제, 코멘트 작성 → 채점 → 해설 흐름, 추가 연습 진입, 현재 스트릭 표시.
3. **게시판 페이지** — 문제별 추론 게시판(언어이해/추리논증), 제출 전 스포일러 차단 게이팅.
4. **마이 페이지** — 아래 4-1 레이아웃을 따른다.

### 4-1. 마이 페이지 레이아웃 (위→아래 순서)

1. **프로필 영역** — 가입일, 목표, 스트릭, 정답률
2. **내 학습 게시글** — 프로필 바로 아래. 내가 작성한 추론 게시글(`board_posts` where user_id = me) 목록. 각 항목에 문제 제목·영역 태그·정답 여부·작성일 표시, 클릭 시 해당 문제 게시판으로 이동.
3. **환경 설정** — 아래 항목. *(추후 추가)* 표시는 UI에 노출하되 비활성/준비중 처리.
   - **문제 범위**: 전체 회차 랜덤 / 최신 3개년 / 최신 5개년
   - **취약 유형**: *(추후 추가)*
   - **타이머 설정**: 2분 제한 / 3분 제한 / 4분 제한
   - **오답 복습**: 3일 뒤 자동 재노출 / 5일 뒤 자동 재노출 / 7일 뒤 자동 재노출 / 재노출 금지 *(추후 추가)*
   - **이번 주 요약**: *(추후 추가)*

## 5. 핵심 비즈니스 규칙

1. **하루 한 문제(데일리)**: 사용자가 그날 처음 접속하면 아직 안 푼 문제 1개를 오늘의 문제로 배정하고 고정한다. 같은 날 새로고침해도 문제가 바뀌면 안 된다.
2. **문제 배정은 사용자별 개인 진도**다. 전역 공통 배정이 아니다. 영역(언어이해↔추리논증)을 번갈아, 회차는 최신순으로 뽑는 것을 기본으로 한다.
3. **추가 연습 허용**: 데일리와 별개로 추가 문제를 무제한 풀 수 있다. 단, **스트릭은 데일리 한 문제만 카운트**한다 (`attempts.is_daily`로 구분).
4. **코멘트 강제(메타인지 장치)**: 정답·해설을 공개하기 전에 사용자는 "왜 이 답을 골랐는지" 추론 코멘트를 반드시 작성해야 한다. 코멘트가 비어 있으면 제출/채점 불가.
5. **자동 게시판 등록**: 제출 시 작성한 코멘트가 해당 문제의 게시판에 자동 등록된다. 한 사용자는 한 문제당 게시물 1개(첫 제출 기준).
6. **스포일러 차단(중요)**: 특정 문제의 게시판은 **그 사용자가 그 문제를 제출한 이후에만** 열람 가능하다. 제출 전에는 남의 추론·선택지가 보이면 안 된다.
7. **환경 설정 반영**:
   - **문제 범위** → 오늘의 문제·추가 연습 배정 쿼리에서 `exams.year` 기준으로 필터링한다. (전체 랜덤 / 최신 3개년 / 최신 5개년)
   - **타이머 설정** → 클라이언트 카운트다운으로 사용. 채점 정답 여부에는 영향 없음(기록·UX 용도). 만료 시 동작은 추후 정의.
   - **오답 복습** → 데일리 오답이 발생하면 `user_settings.review_interval_days`(3/5/7) 후 날짜로 `review_queue`에 등록한다. `/daily` 호출 시 due된 복습 문제를 우선 노출(또는 별도 슬롯)한다. 값이 null이면 스케줄링하지 않는다("재노출 금지"는 추후 명시적 옵션으로).

## 6. 데이터 모델 (SQLAlchemy 기준)

```
users         : id, email, nickname, auth_provider, provider_id,
                password_hash(nullable), current_streak, longest_streak,
                last_completed_date, created_at
exams         : id, year, round, area            # area ∈ {언어이해, 추리논증}
passages      : id, exam_id(FK), content, source_ref
problems      : id, passage_id(FK,nullable), exam_id(FK),
                question_text, explanation, answer_index, area
choices       : id, problem_id(FK), idx(1..5), content
attempts      : id, user_id(FK), problem_id(FK), selected_index,
                is_correct, reasoning(text), is_daily(bool), attempted_at
user_daily    : id, user_id(FK), assigned_date, problem_id(FK), completed
board_posts   : id, problem_id(FK), user_id(FK), content,
                selected_index, is_correct, created_at
                # UNIQUE(user_id, problem_id) → 1인 1게시물
user_settings : id, user_id(FK, UNIQUE),
                problem_scope ENUM(all_random, recent_3y, recent_5y) DEFAULT all_random,
                timer_limit_sec ENUM(120, 180, 240) DEFAULT 180,
                review_interval_days ENUM(3, 5, 7) NULLABLE,   # null = 재노출 안 함
                weak_type(nullable, 추후), created_at, updated_at
review_queue  : id, user_id(FK), problem_id(FK), due_date, resolved(bool)
```

> 신규 사용자 가입 시 `user_settings` 행을 기본값으로 함께 생성한다.

## 7. API 엔드포인트

- `POST /auth/google/callback` — 구글 소셜 로그인 콜백 → JWT 발급
- `GET  /daily` — 오늘의 문제 (정답·해설 숨김). due된 오답 복습이 있으면 우선/별도 노출.
- `GET  /practice/next` — 추가 연습용 다음 문제 (문제 범위 설정 반영)
- `POST /attempts` — `{problem_id, selected_index, reasoning}` 제출 → 정답·해설 반환 + 게시판 자동 등록. reasoning 비어 있으면 422. 데일리 오답이면 review_queue 등록.
- `GET  /problems/{id}/board` — 문제별 추론 게시판. **제출한 사용자만 접근 (미제출 시 403).**
- `GET  /me/posts` — 내 학습 게시글 (마이 페이지 ②)
- `GET  /stats/me` — 스트릭, 잔디, 누적 통계, 영역별 정답률
- `GET  /settings/me` / `PUT /settings/me` — 환경 설정 조회/수정

## 8. 스트릭 계산 로직

데일리 문제 완료 시:
- `last_completed_date == 어제` → `current_streak += 1`
- `last_completed_date == 오늘` → 변화 없음 (이미 완료)
- 그 외(하루 이상 공백) → `current_streak = 1`
- `current_streak > longest_streak` → `longest_streak` 갱신
- `last_completed_date = 오늘`

## 9. 오늘의 문제 배정 로직

```
GET /daily 호출 시:
1. user_daily에서 (user_id, 오늘 날짜) 조회
2. 있으면 → 그 문제 반환 (고정)
3. 없으면 → (a) review_queue에 due된 오답이 있으면 우선 후보
            (b) 없으면 아직 안 푼 문제 중 1개 선택
                (영역 번갈아 + 회차 최신순, user_settings.problem_scope 필터 적용)
          → user_daily에 기록 후 반환
```

## 10. 개발 로드맵

1. **데이터 1회차분 확보** — 기출 한 회차 수동 파싱 → DB 적재 (검증)
2. **백엔드 코어** — 스키마 + 오늘의 문제 / 채점 / 기록 API
3. **인증** — 구글 소셜 로그인 + JWT
4. **프론트 풀이 플로우** — 문제 → 코멘트 → 채점 → 해설 한 사이클
5. **게시판** — 추론 자동 등록 + 스포일러 차단
6. **성취 요소 & 마이 페이지** — 스트릭, 잔디, 통계, 내 학습 게시글, 환경 설정
7. **확장** — 취약 유형, 이번 주 요약, 오답노트, 게시판 좋아요/답글, 모더레이션

## 11. 데이터 출처 및 운영 주의사항

- **데이터 출처**: LEET 기출은 `leet.uwayapply.com` 자료실에서 가져오는 것을 가정하나, 해당 사이트는 자동 접근(크롤링)을 차단한다. 데이터는 수동 다운로드 → 파싱 → 검수 파이프라인으로 적재한다.
- **저작권**: LEET 기출은 법학전문대학원협의회가 저작권을 보유한다. 외부 공개 서비스화 시 이용 허락 범위 확인이 필요하다. (현재는 학습/포트폴리오 용도 가정.)
- **공개 게시판**: 사용자 생성 콘텐츠이므로 신고/숨김 등 모더레이션은 추후 추가 대상으로 둔다.
