from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.core.config import get_settings
from backend.app.models.ai_explanation import AIExplanation
from backend.app.models.attempt import Attempt
from backend.app.models.enums import ProblemArea
from backend.app.models.exam import Exam
from backend.app.models.problem import Problem
from backend.app.models.problem_embedding import ProblemEmbedding
from backend.app.models.user import User


class AIExplanationConfigurationError(RuntimeError):
    pass


class AIExplanationState(TypedDict, total=False):
    attempt_id: int
    user_id: int
    problem_id: int
    area: str
    year: int
    number: int
    passage: str | None
    question_text: str
    choices: list[dict[str, Any]]
    selected_index: int
    answer_index: int
    is_correct: bool
    user_reasoning: str
    target_candidate_count: int
    candidate_count: int
    accepted_candidates: list[dict[str, Any]]
    discarded_candidates: list[dict[str, Any]]
    latest_candidate: dict[str, Any]
    critic_passed: bool
    critic_notes: str
    references_needed: bool
    references: list[dict[str, Any]]
    final_explanation: str
    solution_summary: str
    user_reasoning_review: str
    wrong_choice_explanation: str | None
    confidence_score: int
    confidence_level: str
    model_name: str


@dataclass(frozen=True)
class AgentRunResult:
    state: AIExplanationState


def get_user_ai_explanation(db: Session, user: User, attempt_id: int) -> AIExplanation:
    explanation = db.execute(
        select(AIExplanation).where(
            AIExplanation.user_id == user.id,
            AIExplanation.attempt_id == attempt_id,
        )
    ).scalar_one_or_none()
    if not explanation:
        raise LookupError("AI explanation not found")
    return explanation


def generate_ai_explanation(db: Session, user: User, attempt_id: int) -> AIExplanation:
    attempt = load_user_attempt(db, user, attempt_id)
    existing = db.execute(
        select(AIExplanation).where(AIExplanation.attempt_id == attempt.id)
    ).scalar_one_or_none()
    if existing and existing.status == "completed":
        return existing

    explanation = existing or AIExplanation(
        attempt_id=attempt.id,
        user_id=user.id,
        problem_id=attempt.problem_id,
        status="pending",
        references_used=[],
        candidate_summaries=[],
    )
    explanation.status = "running"
    explanation.error_message = None
    explanation.final_explanation = None
    explanation.solution_summary = None
    explanation.user_reasoning_review = None
    explanation.wrong_choice_explanation = None
    explanation.confidence_level = None
    explanation.confidence_score = None
    explanation.candidate_count = 0
    explanation.accepted_count = 0
    explanation.discarded_count = 0
    explanation.critic_passed = None
    explanation.critic_notes = None
    explanation.references_used = []
    explanation.candidate_summaries = []
    db.add(explanation)
    db.commit()

    try:
        state = build_initial_state(attempt)
        result = run_ai_explanation_agent(db, state)
        save_success(explanation, result.state)
    except AIExplanationConfigurationError as exc:
        save_failure(explanation, str(exc))
        db.add(explanation)
        db.commit()
        raise
    except Exception as exc:
        save_failure(explanation, str(exc))

    db.add(explanation)
    db.commit()
    db.refresh(explanation)
    return explanation


def load_user_attempt(db: Session, user: User, attempt_id: int) -> Attempt:
    attempt = db.execute(
        select(Attempt)
        .where(Attempt.id == attempt_id, Attempt.user_id == user.id)
        .options(
            selectinload(Attempt.problem).selectinload(Problem.exam),
            selectinload(Attempt.problem).selectinload(Problem.passage),
            selectinload(Attempt.problem).selectinload(Problem.choices),
        )
    ).scalar_one_or_none()
    if not attempt:
        raise LookupError("Attempt not found")
    if attempt.problem.answer_index is None:
        raise LookupError("Problem answer is not available")
    return attempt


def build_initial_state(attempt: Attempt) -> AIExplanationState:
    settings = get_settings()
    return {
        "attempt_id": attempt.id,
        "user_id": attempt.user_id,
        "problem_id": attempt.problem_id,
        "area": attempt.problem.area.value,
        "year": attempt.problem.exam.year,
        "number": attempt.problem.number,
        "passage": attempt.problem.passage.content if attempt.problem.passage else None,
        "question_text": attempt.problem.question_text,
        "choices": [
            {"idx": choice.idx, "content": choice.content}
            for choice in sorted(attempt.problem.choices, key=lambda choice: choice.idx)
        ],
        "selected_index": attempt.selected_index,
        "answer_index": attempt.problem.answer_index,
        "is_correct": attempt.is_correct,
        "user_reasoning": attempt.reasoning,
        "target_candidate_count": settings.ai_explanation_candidate_count,
        "candidate_count": 0,
        "accepted_candidates": [],
        "discarded_candidates": [],
        "references": [],
        "references_needed": False,
        "model_name": settings.openai_ai_explanation_model,
    }


def run_ai_explanation_agent(db: Session, state: AIExplanationState) -> AgentRunResult:
    graph = build_graph(db)
    recursion_limit = max(12, state["target_candidate_count"] * 2 + 8)
    final_state = graph.invoke(state, {"recursion_limit": recursion_limit})
    return AgentRunResult(state=final_state)


def build_graph(db: Session):
    builder = StateGraph(AIExplanationState)
    builder.add_node("generate_candidate", generate_candidate)
    builder.add_node("verify_candidate", verify_candidate)
    builder.add_node("critic_verify", critic_verify)
    builder.add_node("decide_reference_need", decide_reference_need)
    builder.add_node("retrieve_references", lambda state: retrieve_references(db, state))
    builder.add_node("generate_final_explanation", generate_final_explanation)

    builder.add_edge(START, "generate_candidate")
    builder.add_edge("generate_candidate", "verify_candidate")
    builder.add_conditional_edges(
        "verify_candidate",
        route_after_candidate,
        {
            "generate_candidate": "generate_candidate",
            "critic_verify": "critic_verify",
        },
    )
    builder.add_edge("critic_verify", "decide_reference_need")
    builder.add_conditional_edges(
        "decide_reference_need",
        route_after_reference_decision,
        {
            "retrieve_references": "retrieve_references",
            "generate_final_explanation": "generate_final_explanation",
        },
    )
    builder.add_edge("retrieve_references", "generate_final_explanation")
    builder.add_edge("generate_final_explanation", END)
    return builder.compile()


def route_after_candidate(state: AIExplanationState) -> str:
    if state["candidate_count"] < state["target_candidate_count"]:
        return "generate_candidate"
    return "critic_verify"


def route_after_reference_decision(state: AIExplanationState) -> str:
    if state.get("references_needed"):
        return "retrieve_references"
    return "generate_final_explanation"


def generate_candidate(state: AIExplanationState) -> AIExplanationState:
    next_count = state["candidate_count"] + 1
    candidate = call_openai_json(
        [
            {
                "role": "system",
                "content": (
                    "너는 LEET 풀이 후보를 독립적으로 도출하는 에이전트다. "
                    "정답 번호는 제공받지 않는다. 지문, 문제, 선택지 안의 근거만 사용한다. "
                    "외부 지식이나 추측을 쓰지 말고 JSON만 출력한다."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"영역: {state['area']}\n"
                    f"연도/번호: {state['year']}학년도 {state['number']}번\n"
                    f"지문:\n{state.get('passage') or '없음'}\n\n"
                    f"문제:\n{state['question_text']}\n\n"
                    f"선택지:\n{format_choices(state['choices'])}\n\n"
                    "아래 JSON 형식으로 풀이 후보를 작성해라.\n"
                    "{"
                    "\"selected_index\": 1,"
                    "\"solution_path\": \"정답에 도달한 논리 경로\","
                    "\"evidence\": [\"지문 또는 선택지 근거\"],"
                    "\"eliminations\": [{\"idx\": 1, \"reason\": \"오답 배제 근거\"}]"
                    "}"
                ),
            },
        ],
        model=state["model_name"],
        temperature=0.7,
    )
    candidate["candidate_no"] = next_count
    return {
        "candidate_count": next_count,
        "latest_candidate": candidate,
    }


def verify_candidate(state: AIExplanationState) -> AIExplanationState:
    candidate = state.get("latest_candidate", {})
    selected_index = to_int(candidate.get("selected_index"))
    accepted = list(state.get("accepted_candidates", []))
    discarded = list(state.get("discarded_candidates", []))
    if selected_index == state["answer_index"]:
        accepted.append(candidate)
    else:
        discarded.append(
            {
                **candidate,
                "discard_reason": (
                    f"도출 답 {selected_index or '없음'}번이 실제 정답 {state['answer_index']}번에 도달하지 못함"
                ),
            }
        )
    return {
        "accepted_candidates": accepted,
        "discarded_candidates": discarded,
    }


def critic_verify(state: AIExplanationState) -> AIExplanationState:
    accepted = state.get("accepted_candidates", [])
    if not accepted:
        return {
            "critic_passed": False,
            "critic_notes": "정답 번호에 도달한 풀이 후보가 없어 AI 해설 생성을 중단합니다.",
        }

    critic = call_openai_json(
        [
            {
                "role": "system",
                "content": (
                    "너는 LEET AI 해설의 critic 검증자다. "
                    "후보 풀이가 실제 정답 번호와 일치하는지, 지문/문제/선택지 근거만 사용하는지 검사한다. "
                    "외부 지식, 비약, 근거 없는 단정을 발견하면 passed=false로 둔다. JSON만 출력한다."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"정답 번호: {state['answer_index']}\n"
                    f"문제:\n{state['question_text']}\n\n"
                    f"지문:\n{state.get('passage') or '없음'}\n\n"
                    f"선택지:\n{format_choices(state['choices'])}\n\n"
                    f"정답 도달 후보:\n{json.dumps(accepted, ensure_ascii=False)}\n\n"
                    "아래 JSON 형식으로 검증 결과를 작성해라.\n"
                    "{"
                    "\"passed\": true,"
                    "\"notes\": \"검증 요약\","
                    "\"issues\": [\"문제가 있다면 적기\"]"
                    "}"
                ),
            },
        ],
        model=state["model_name"],
        temperature=0.1,
    )
    issues = critic.get("issues") or []
    notes = str(critic.get("notes") or "")
    if issues:
        notes = f"{notes}\n" + "\n".join(f"- {issue}" for issue in issues)
    return {
        "critic_passed": bool(critic.get("passed")),
        "critic_notes": notes.strip(),
    }


def decide_reference_need(state: AIExplanationState) -> AIExplanationState:
    accepted_count = len(state.get("accepted_candidates", []))
    confidence_score = calculate_confidence_score(
        accepted_count=accepted_count,
        candidate_count=state["target_candidate_count"],
        critic_passed=state.get("critic_passed", False),
    )
    references_needed = confidence_score < 67 or len(state["user_reasoning"].strip()) < 30
    return {
        "confidence_score": confidence_score,
        "confidence_level": confidence_level(confidence_score),
        "references_needed": references_needed,
    }


def retrieve_references(db: Session, state: AIExplanationState) -> AIExplanationState:
    references: list[dict[str, Any]] = []
    references.extend(fetch_similar_problem_references(db, state))
    references.extend(fetch_recent_attempt_references(db, state))
    return {"references": references[:5]}


def generate_final_explanation(state: AIExplanationState) -> AIExplanationState:
    accepted = state.get("accepted_candidates", [])
    if not accepted:
        raise RuntimeError("정답에 도달한 AI 도출이 없어 AI 해설을 생성하지 않았습니다.")

    final = call_openai_json(
        [
            {
                "role": "system",
                "content": (
                    "너는 LEET 학습자를 위한 AI 해설 작성자다. "
                    "검증을 통과한 후보 풀이만 근거로 삼고, 공식 해설처럼 말하지 않는다. "
                    "정답 번호와 지문/선택지 근거를 벗어난 내용을 만들지 않는다. JSON만 출력한다."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"사용자 선택: {state['selected_index']}번\n"
                    f"정답: {state['answer_index']}번\n"
                    f"정답 여부: {'정답' if state['is_correct'] else '오답'}\n"
                    f"사용자 추론:\n{state['user_reasoning']}\n\n"
                    f"문제:\n{state['question_text']}\n\n"
                    f"선택지:\n{format_choices(state['choices'])}\n\n"
                    f"검증된 후보:\n{json.dumps(accepted, ensure_ascii=False)}\n\n"
                    f"critic 검증:\npassed={state.get('critic_passed')}\n{state.get('critic_notes') or ''}\n\n"
                    f"보조 참조:\n{json.dumps(state.get('references', []), ensure_ascii=False)}\n\n"
                    "아래 JSON 형식으로 작성해라.\n"
                    "{"
                    "\"final_explanation\": \"학습자에게 보여줄 AI 해설\","
                    "\"solution_summary\": \"정답에 도달하는 핵심 논리\","
                    "\"user_reasoning_review\": \"사용자 추론에서 맞은 지점과 어긋난 지점\","
                    "\"wrong_choice_explanation\": \"오답인 경우 사용자가 고른 답이 틀린 이유, 정답이면 null\""
                    "}"
                ),
            },
        ],
        model=state["model_name"],
        temperature=0.2,
    )
    return {
        "final_explanation": str(final.get("final_explanation") or ""),
        "solution_summary": str(final.get("solution_summary") or ""),
        "user_reasoning_review": str(final.get("user_reasoning_review") or ""),
        "wrong_choice_explanation": final.get("wrong_choice_explanation"),
    }


def call_openai_json(messages: list[dict[str, str]], model: str, temperature: float) -> dict[str, Any]:
    settings = get_settings()
    if not settings.openai_api_key:
        raise AIExplanationConfigurationError("AI 해설 생성을 위해 OPENAI_API_KEY 설정이 필요합니다.")

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)


def fetch_similar_problem_references(db: Session, state: AIExplanationState) -> list[dict[str, Any]]:
    reference_embedding = db.execute(
        select(ProblemEmbedding).where(ProblemEmbedding.problem_id == state["problem_id"])
    ).scalar_one_or_none()
    if not reference_embedding:
        return []

    distance = ProblemEmbedding.embedding.cosine_distance(reference_embedding.embedding).label("distance")
    rows = (
        db.execute(
            select(Problem, distance)
            .join(ProblemEmbedding, ProblemEmbedding.problem_id == Problem.id)
            .join(Exam)
            .where(
                ProblemEmbedding.embedding_model == reference_embedding.embedding_model,
                Problem.id != state["problem_id"],
                Problem.area == ProblemArea(state["area"]),
                Problem.answer_index.is_not(None),
            )
            .order_by(distance.asc(), Problem.id.asc())
            .limit(3)
        )
        .all()
    )
    return [
        {
            "type": "similar_problem",
            "problem_id": problem.id,
            "year": problem.exam.year,
            "area": problem.area.value,
            "number": problem.number,
            "similarity_score": round(max(0.0, min(1.0, 1 - float(cosine_distance))) * 100),
            "question_text": problem.question_text,
        }
        for problem, cosine_distance in rows
    ]


def fetch_recent_attempt_references(db: Session, state: AIExplanationState) -> list[dict[str, Any]]:
    attempts = (
        db.execute(
            select(Attempt)
            .join(Attempt.problem)
            .where(
                Attempt.user_id == state["user_id"],
                Attempt.problem_id != state["problem_id"],
            )
            .options(selectinload(Attempt.problem).selectinload(Problem.exam))
            .order_by(Attempt.attempted_at.desc(), Attempt.id.desc())
            .limit(3)
        )
        .scalars()
        .all()
    )
    return [
        {
            "type": "recent_attempt",
            "problem_id": attempt.problem_id,
            "year": attempt.problem.exam.year,
            "area": attempt.problem.area.value,
            "number": attempt.problem.number,
            "is_correct": attempt.is_correct,
        }
        for attempt in attempts
    ]


def save_success(explanation: AIExplanation, state: AIExplanationState) -> None:
    accepted = state.get("accepted_candidates", [])
    discarded = state.get("discarded_candidates", [])
    explanation.status = "completed"
    explanation.final_explanation = state.get("final_explanation")
    explanation.solution_summary = state.get("solution_summary")
    explanation.user_reasoning_review = state.get("user_reasoning_review")
    explanation.wrong_choice_explanation = state.get("wrong_choice_explanation")
    explanation.confidence_score = state.get("confidence_score")
    explanation.confidence_level = state.get("confidence_level")
    explanation.candidate_count = state.get("candidate_count", 0)
    explanation.accepted_count = len(accepted)
    explanation.discarded_count = len(discarded)
    explanation.critic_passed = state.get("critic_passed")
    explanation.critic_notes = state.get("critic_notes")
    explanation.references_used = state.get("references", [])
    explanation.candidate_summaries = summarize_candidates(accepted, discarded)
    explanation.model_name = state.get("model_name")
    explanation.error_message = None


def save_failure(explanation: AIExplanation, error_message: str) -> None:
    explanation.status = "failed"
    explanation.error_message = error_message
    explanation.final_explanation = None
    explanation.solution_summary = None
    explanation.user_reasoning_review = None
    explanation.wrong_choice_explanation = None


def summarize_candidates(accepted: list[dict[str, Any]], discarded: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for candidate in accepted:
        summaries.append(
            {
                "candidate_no": candidate.get("candidate_no"),
                "accepted": True,
                "selected_index": candidate.get("selected_index"),
                "solution_path": candidate.get("solution_path"),
            }
        )
    for candidate in discarded:
        summaries.append(
            {
                "candidate_no": candidate.get("candidate_no"),
                "accepted": False,
                "selected_index": candidate.get("selected_index"),
                "discard_reason": candidate.get("discard_reason"),
            }
        )
    return sorted(summaries, key=lambda item: item.get("candidate_no") or 0)


def calculate_confidence_score(accepted_count: int, candidate_count: int, critic_passed: bool) -> int:
    if candidate_count <= 0:
        return 0
    score = round((accepted_count / candidate_count) * 100)
    if not critic_passed:
        score = min(score, 50)
    return score


def confidence_level(score: int) -> str:
    if score >= 85:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


def format_choices(choices: list[dict[str, Any]]) -> str:
    return "\n".join(f"{choice['idx']}. {choice['content']}" for choice in choices)


def to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
