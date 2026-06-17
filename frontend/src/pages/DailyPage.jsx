import { useEffect, useState } from "react";

import {
  deleteMyProblemActivity,
  fetchDailyProblem,
  fetchMyAttemptHistory,
  fetchMySettings,
  fetchMyStats,
  fetchPracticeProblem,
  generateAIExplanation,
  submitAttempt,
} from "../api/client";
import ActivityGrid from "../components/ActivityGrid";
import Avatar from "../components/Avatar";
import Card from "../components/Card";
import Shell from "../components/Shell";
import Stat from "../components/Stat";

const areaLabels = {
  reading_comprehension: "언어이해",
  reasoning_argumentation: "추리논증",
};

const confidenceLabels = {
  high: "신뢰도 높음",
  medium: "신뢰도 보통",
  low: "신뢰도 낮음",
};

function formatTimer(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function formatNullableTimer(totalSeconds) {
  return typeof totalSeconds === "number" ? formatTimer(totalSeconds) : "-";
}

function formatAttemptLabel(attempt) {
  const status = attempt.is_correct ? "정답" : "오답";
  const mode = attempt.is_daily ? "데일리" : "연습";
  return `[${status}] ${attempt.title} [${mode}]`;
}

export default function DailyPage({ page, setPage, onOpenBoardProblem }) {
  const [daily, setDaily] = useState(null);
  const [mode, setMode] = useState("daily");
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [reasoning, setReasoning] = useState("");
  const [result, setResult] = useState(null);
  const [stats, setStats] = useState(null);
  const [aiExplanation, setAiExplanation] = useState(null);
  const [aiExplanationLoading, setAiExplanationLoading] = useState(false);
  const [aiExplanationError, setAiExplanationError] = useState("");
  const [completedToday, setCompletedToday] = useState(false);
  const [attemptHistory, setAttemptHistory] = useState([]);
  const [attemptHistoryLoading, setAttemptHistoryLoading] = useState(true);
  const [deletingAttemptProblemId, setDeletingAttemptProblemId] = useState(null);
  const [attemptHistoryMessage, setAttemptHistoryMessage] = useState("");
  const [timerLimitSec, setTimerLimitSec] = useState(180);
  const [remainingSec, setRemainingSec] = useState(180);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;
    async function loadDailyProblem() {
      try {
        setLoading(true);
        const data = await fetchDailyProblem();
        if (!ignore) {
          setDaily(data);
          setCompletedToday(data.completed);
          setSelectedIndex(null);
          setReasoning("");
          setResult(null);
          setAiExplanation(null);
          setAiExplanationError("");
          setError("");
        }
      } catch (err) {
        if (!ignore) {
          setError(err.message);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    async function loadMyStats() {
      try {
        const data = await fetchMyStats();
        if (!ignore) {
          setStats(data);
        }
      } catch {
        if (!ignore) {
          setStats(null);
        }
      }
    }

    async function loadAttemptHistory() {
      try {
        const data = await fetchMyAttemptHistory();
        if (!ignore) {
          setAttemptHistory(data);
        }
      } catch {
        if (!ignore) {
          setAttemptHistory([]);
        }
      } finally {
        if (!ignore) {
          setAttemptHistoryLoading(false);
        }
      }
    }

    async function loadMySettings() {
      try {
        const data = await fetchMySettings();
        if (!ignore) {
          setTimerLimitSec(data.timer_limit_sec);
          setRemainingSec(data.timer_limit_sec);
        }
      } catch {
        if (!ignore) {
          setTimerLimitSec(180);
          setRemainingSec(180);
        }
      }
    }

    loadDailyProblem();
    loadMyStats();
    loadAttemptHistory();
    loadMySettings();
    return () => {
      ignore = true;
    };
  }, []);

  async function handleSubmit() {
    if (mode === "daily" && completedToday && !result) {
      setError("오늘의 문제는 이미 제출했어요. 내일 새 문제를 풀어주세요.");
      return;
    }
    if (!daily || !selectedIndex) {
      setError("선택지를 먼저 골라주세요.");
      return;
    }
    if (!reasoning.trim()) {
      setError("정답을 보기 전에 추론 코멘트를 작성해주세요.");
      return;
    }

    try {
      setSubmitting(true);
      const data = await submitAttempt({
        problemId: daily.problem.id,
        selectedIndex,
        reasoning,
        solveDurationSec: Math.max(0, timerLimitSec - remainingSec),
      });
      setResult(data);
      setDaily((current) =>
        current
          ? {
              ...current,
              problem: {
                ...current.problem,
                stats: data.problem_stats,
              },
            }
          : current
      );
      setAiExplanation(null);
      setAiExplanationError("");
      if (mode === "daily") {
        setCompletedToday(true);
        setDaily((current) => current ? { ...current, completed: true } : current);
        fetchMyStats().then(setStats).catch(() => {});
      }
      fetchMyAttemptHistory().then(setAttemptHistory).catch(() => {});
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  const problem = daily?.problem;
  const areaLabel = problem ? areaLabels[problem.area] : "";
  const timerPercent = timerLimitSec > 0 ? (remainingSec / timerLimitSec) * 100 : 0;
  const timerExpired = remainingSec === 0;
  const similarityTag =
    mode === "practice" && typeof problem?.similarity_score === "number"
      ? `오늘 문제와 관련도 ${problem.similarity_score}%`
      : null;
  const aiExplanationCompleted = aiExplanation?.status === "completed";
  const aiExplanationButtonLabel = aiExplanationLoading
    ? "생성 중..."
    : aiExplanation?.status === "failed"
      ? "다시 시도"
      : aiExplanationCompleted
        ? "AI 해설 생성됨"
        : "AI 해설 생성";
  const dailySubmissionLocked = mode === "daily" && completedToday && !result;
  const problemTags = problem
    ? [areaLabel, `${problem.year}학년도`, `${problem.number}번`, similarityTag, `${Math.round(timerLimitSec / 60)}분 제한`].filter(Boolean)
    : [];

  useEffect(() => {
    if (!problem || result || dailySubmissionLocked || remainingSec <= 0) {
      return undefined;
    }

    const timerId = window.setInterval(() => {
      setRemainingSec((current) => Math.max(0, current - 1));
    }, 1000);

    return () => window.clearInterval(timerId);
  }, [dailySubmissionLocked, problem, remainingSec, result]);

  async function loadPracticeProblem() {
    try {
      setLoading(true);
      const problemData = await fetchPracticeProblem();
      setDaily({ assigned_date: null, completed: false, problem: problemData });
      setMode("practice");
      setRemainingSec(timerLimitSec);
      setSelectedIndex(null);
      setReasoning("");
      setResult(null);
      setAiExplanation(null);
      setAiExplanationError("");
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteAttemptHistory(attempt) {
    if (!window.confirm("이 문제의 풀이 기록과 추론 게시글을 삭제할까요?")) {
      return;
    }

    try {
      setDeletingAttemptProblemId(attempt.problem_id);
      setAttemptHistoryMessage("");
      await deleteMyProblemActivity(attempt.problem_id);
      const [historyData, statData, dailyData] = await Promise.all([
        fetchMyAttemptHistory(),
        fetchMyStats(),
        fetchDailyProblem(),
      ]);
      setAttemptHistory(historyData);
      setStats(statData);
      setCompletedToday(dailyData.completed);
      if (mode === "daily" && daily?.problem?.id === attempt.problem_id) {
        setDaily(dailyData);
      }
      if (daily?.problem?.id === attempt.problem_id) {
        setSelectedIndex(null);
        setReasoning("");
        setResult(null);
        setAiExplanation(null);
        setAiExplanationError("");
      }
      setAttemptHistoryMessage("풀이 기록과 추론 게시글을 삭제했어요.");
    } catch (err) {
      setAttemptHistoryMessage(err.message);
    } finally {
      setDeletingAttemptProblemId(null);
    }
  }

  async function handleGenerateAIExplanation() {
    if (!result?.attempt_id) {
      return;
    }

    try {
      setAiExplanationLoading(true);
      setAiExplanationError("");
      const data = await generateAIExplanation(result.attempt_id);
      setAiExplanation(data);
    } catch (err) {
      setAiExplanationError(err.message);
    } finally {
      setAiExplanationLoading(false);
    }
  }

  return (
    <Shell page={page} setPage={setPage}>
      <div className="mx-auto grid w-full max-w-[1360px] min-w-0 gap-7 px-3 py-6 lg:grid-cols-[320px_minmax(0,1fr)] lg:px-7 lg:py-8">
        <aside className="space-y-5">
          <Card className="p-7">
            <div className="mb-8 flex items-center gap-5">
              <Avatar />
              <div className="flex min-h-20 items-center">
                <p className="text-xl font-black">{stats?.nickname ?? "ifuril"}</p>
              </div>
            </div>
            <div className="mb-7 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between lg:flex-col lg:items-start">
              <h2 className="text-lg font-black">나의 잔디밭</h2>
              <span className="rounded-md bg-ash px-3 py-2 text-xs font-black">
                현재 {stats?.current_streak ?? 0}일 연속 문제 풀이 중!
              </span>
            </div>
            <ActivityGrid currentStreak={stats?.current_streak ?? 0} completedToday={completedToday} />
          </Card>

          <Card className="p-7">
            <h2 className="mb-7 text-lg font-black">날짜별 푼 문제</h2>
            {attemptHistoryMessage && (
              <p className="mb-4 rounded-md border border-smoke bg-paper px-3 py-2 text-xs font-black text-[#666]">
                {attemptHistoryMessage}
              </p>
            )}
            {attemptHistoryLoading ? (
              <p className="rounded-md border border-smoke p-4 text-sm font-black text-[#666]">풀이 기록을 불러오는 중...</p>
            ) : attemptHistory.length === 0 ? (
              <p className="rounded-md border border-smoke p-4 text-sm font-black text-[#666]">아직 제출한 문제가 없어요.</p>
            ) : (
              attemptHistory.map((day, index) => (
                <div key={day.date} className="mb-7 grid grid-cols-[18px_1fr] gap-3 last:mb-0">
                  <span className={`mt-1 h-3 w-3 rounded-full ${index === 0 ? "bg-pepper" : "border border-smoke bg-white"}`} />
                  <div className="min-w-0">
                    <p className="mb-3 text-xl font-black">{day.date}</p>
                    <div className="space-y-2">
                      {day.attempts.map((attempt) => (
                        <div key={attempt.id} className="flex items-start justify-between gap-2">
                          <button
                            type="button"
                            onClick={() => onOpenBoardProblem(attempt.problem_id)}
                            className="min-w-0 text-left text-xs font-black leading-5 hover:underline hover:underline-offset-4"
                          >
                            {formatAttemptLabel(attempt)}
                          </button>
                          <button
                            type="button"
                            disabled={deletingAttemptProblemId === attempt.problem_id}
                            onClick={() => handleDeleteAttemptHistory(attempt)}
                            className="grid h-7 w-7 shrink-0 place-items-center rounded-md border border-smoke text-xs hover:bg-paper disabled:cursor-not-allowed disabled:opacity-60"
                            aria-label="풀이 기록 삭제"
                            title="풀이 기록 삭제"
                          >
                            🗑️
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))
            )}
          </Card>
        </aside>

        <Card className="min-w-0 border-pepper p-4 sm:p-7">
          {loading ? (
            <div className="grid min-h-[520px] place-items-center text-lg font-black">오늘의 문제를 불러오는 중...</div>
          ) : !problem ? (
            <div className="grid min-h-[520px] place-items-center rounded-md border border-pepper p-6 text-center">
              <div>
                <h2 className="text-2xl font-black">문제를 불러오지 못했어요.</h2>
                <p className="mt-3 text-sm text-[#666]">{error || "FastAPI 서버가 실행 중인지 확인해주세요."}</p>
              </div>
            </div>
          ) : (
            <>
              <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <p className="mb-3 text-sm font-black">오늘 풀어야 할 문제</p>
                  <h2 className="text-3xl font-black">
                    {mode === "daily" ? "오늘의 LEET 도전을 시작하세요!" : "추가 연습 문제를 풀어보세요!"}
                  </h2>
                </div>
                <button
                  type="button"
                  onClick={loadPracticeProblem}
                  className="h-11 rounded-md border border-smoke px-5 text-sm font-black hover:bg-paper"
                >
                  추가 연습
                </button>
              </div>

              <div className="mb-5 flex flex-wrap gap-3">
                {problemTags.map((tag) => (
                  <span key={tag} className="rounded-md bg-ash px-4 py-2 text-xs font-black">
                    {tag}
                  </span>
                ))}
              </div>
              {dailySubmissionLocked && (
                <p className="mb-5 rounded-md border border-smoke bg-paper px-4 py-3 text-sm font-black">
                  오늘의 문제는 이미 제출했어요. 추가 연습은 계속 풀 수 있습니다.
                </p>
              )}

              <div className="grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(320px,380px)] xl:items-start">
                <div className="order-2 min-w-0 xl:order-1">
                  <div
                    className="grid w-full min-w-0 max-w-3xl gap-5"
                  >
                    {problem.passage && (
                      <div className="min-w-0 rounded-md border border-pepper p-4 sm:p-5">
                        <p className="mb-3 text-sm font-black">[자료] 다음 글을 읽고 물음에 답하시오.</p>
                        <p className="leet-text text-base leading-7">{problem.passage}</p>
                      </div>
                    )}

                    <div
                      className="min-w-0 rounded-md border border-pepper p-4 sm:p-5"
                    >
                      <p className="leet-text text-base leading-7">{problem.question_text}</p>
                    </div>

                    <div
                      className="grid w-full min-w-0 gap-3"
                    >
                      {problem.choices.map((choice) => {
                        const isSelected = selectedIndex === choice.idx;
                        const isAnswer = result?.answer_index === choice.idx;
                        return (
                          <button
                            key={choice.id}
                            disabled={Boolean(result) || dailySubmissionLocked}
                            onClick={() => setSelectedIndex(choice.idx)}
                            className={`leet-text w-full rounded-md border px-5 py-3 text-left text-base ${
                              isAnswer
                                ? "border-pepper bg-pepper font-black text-white"
                                : isSelected
                                  ? "border-pepper bg-ash font-black"
                                  : "border-smoke bg-white hover:bg-paper"
                            }`}
                          >
                            {choice.idx}. {choice.content}
                          </button>
                        );
                      })}
                    </div>

                    <div className="grid w-full gap-3 sm:grid-cols-3">
                      <Stat label="정답률" value={`${problem.stats?.accuracy_rate ?? 0}%`} />
                      <Stat label="평균 풀이" value={formatNullableTimer(problem.stats?.average_solve_duration_sec)} />
                      <Stat label="누적 풀이" value={`${(problem.stats?.total_attempts ?? 0).toLocaleString("ko-KR")}명`} />
                    </div>

                    {result && (
                      <div className="rounded-md border border-pepper p-5">
                        <p className="text-xl font-black">{result.is_correct ? "정답입니다." : "오답입니다."}</p>
                        <p className="mt-2 text-sm">
                          선택한 답 {result.selected_index}번 / 정답 {result.answer_index}번
                        </p>
                        {result.explanation && (
                          <p className="leet-text mt-3 text-base leading-7">{result.explanation}</p>
                        )}
                      </div>
                    )}

                    {result && (
                      <div className="rounded-md border border-pepper p-5">
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                          <div>
                            <p className="text-xl font-black">AI 해설</p>
                            <p className="mt-1 text-sm text-[#666]">
                              여러 풀이 후보를 검증한 뒤 생성합니다.
                            </p>
                          </div>
                          <button
                            type="button"
                            disabled={aiExplanationLoading || aiExplanationCompleted}
                            onClick={handleGenerateAIExplanation}
                            className="min-h-10 rounded-md border border-smoke px-4 text-sm font-black hover:bg-paper disabled:cursor-not-allowed disabled:bg-ash"
                          >
                            {aiExplanationButtonLabel}
                          </button>
                        </div>

                        {aiExplanationError && (
                          <p className="mt-4 rounded-md border border-pepper bg-paper px-4 py-3 text-sm font-black">
                            {aiExplanationError}
                          </p>
                        )}

                        {aiExplanation?.status === "completed" && (
                          <div className="mt-5 space-y-4">
                            <div className="flex flex-wrap gap-2">
                              {aiExplanation.confidence_level && (
                                <span className="rounded-md bg-ash px-3 py-2 text-xs font-black">
                                  {confidenceLabels[aiExplanation.confidence_level] ?? aiExplanation.confidence_level}
                                </span>
                              )}
                              <span className="rounded-md bg-ash px-3 py-2 text-xs font-black">
                                정답 도달 {aiExplanation.accepted_count}/{aiExplanation.candidate_count}
                              </span>
                              <span className="rounded-md bg-ash px-3 py-2 text-xs font-black">
                                폐기 {aiExplanation.discarded_count}
                              </span>
                            </div>

                            {aiExplanation.final_explanation && (
                              <p className="leet-text text-base leading-7">{aiExplanation.final_explanation}</p>
                            )}
                            {aiExplanation.solution_summary && (
                              <div>
                                <p className="mb-2 text-sm font-black">핵심 논리</p>
                                <p className="leet-text text-base leading-7">{aiExplanation.solution_summary}</p>
                              </div>
                            )}
                            {aiExplanation.user_reasoning_review && (
                              <div>
                                <p className="mb-2 text-sm font-black">내 추론 진단</p>
                                <p className="leet-text text-base leading-7">{aiExplanation.user_reasoning_review}</p>
                              </div>
                            )}
                            {aiExplanation.wrong_choice_explanation && (
                              <div>
                                <p className="mb-2 text-sm font-black">선택지 점검</p>
                                <p className="leet-text text-base leading-7">{aiExplanation.wrong_choice_explanation}</p>
                              </div>
                            )}
                          </div>
                        )}

                        {aiExplanation?.status === "failed" && (
                          <p className="mt-4 rounded-md border border-pepper bg-paper px-4 py-3 text-sm font-black">
                            {aiExplanation.error_message || "AI 해설 생성에 실패했습니다."}
                          </p>
                        )}
                      </div>
                    )}

                    <label className="block w-full">
                      <span className="mb-2 block text-sm font-black">나의 추론 코멘트</span>
                      <textarea
                        value={reasoning}
                        disabled={Boolean(result) || dailySubmissionLocked}
                        onChange={(event) => setReasoning(event.target.value)}
                        className="min-h-36 w-full rounded-md border border-smoke p-4 text-base leading-7"
                        placeholder="왜 이 답을 골랐는지 먼저 적어보세요."
                      />
                    </label>

                    {error && (
                      <p className="rounded-md border border-pepper bg-paper px-4 py-3 text-sm font-black">
                        {error}
                      </p>
                    )}

                    <button
                      disabled={submitting || Boolean(result) || dailySubmissionLocked}
                      onClick={handleSubmit}
                      className="min-h-12 w-full rounded-md bg-pepper px-5 py-3 text-sm font-black text-white hover:bg-[#444] disabled:cursor-not-allowed disabled:bg-smoke"
                    >
                      {submitting ? "제출 중..." : result ? "제출 완료" : dailySubmissionLocked ? "오늘의 문제 풀이 완료" : "정답 제출하기"}
                    </button>
                  </div>
                </div>

                <div className="order-1 min-w-0 space-y-5 xl:sticky xl:top-8 xl:order-2">
                  <div className="rounded-md border border-pepper p-5">
                    <div className="mb-4 flex items-center justify-between gap-3">
                      <p className="text-sm font-black">타이머</p>
                      <button
                        type="button"
                        onClick={() => setRemainingSec(timerLimitSec)}
                        className="h-9 rounded-md border border-smoke px-3 text-xs font-black hover:bg-paper"
                      >
                        다시 시작
                      </button>
                    </div>
                    <p className={`text-4xl font-black ${timerExpired ? "text-[#9b3d2e]" : "text-pepper"}`}>
                      {formatTimer(remainingSec)}
                    </p>
                    <div className="mt-4 h-2 rounded-full bg-ash">
                      <div className="h-2 rounded-full bg-pepper" style={{ width: `${timerPercent}%` }} />
                    </div>
                    {timerExpired && <p className="mt-3 text-xs font-black text-[#9b3d2e]">제한 시간이 끝났어요.</p>}
                  </div>
                </div>
              </div>
            </>
          )}
        </Card>
      </div>
    </Shell>
  );
}
