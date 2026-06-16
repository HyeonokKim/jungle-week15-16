import { useEffect, useRef, useState } from "react";

import { fetchDailyProblem, fetchMySettings, fetchMyStats, fetchPracticeProblem, submitAttempt } from "../api/client";
import ActivityGrid from "../components/ActivityGrid";
import Avatar from "../components/Avatar";
import Card from "../components/Card";
import Shell from "../components/Shell";
import Stat from "../components/Stat";
import { recentSolved } from "../data/mockData";

const areaLabels = {
  reading_comprehension: "언어이해",
  reasoning_argumentation: "추리논증",
};

function formatTimer(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export default function DailyPage({ page, setPage }) {
  const problemContentRef = useRef(null);
  const [daily, setDaily] = useState(null);
  const [mode, setMode] = useState("daily");
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [reasoning, setReasoning] = useState("");
  const [result, setResult] = useState(null);
  const [stats, setStats] = useState(null);
  const [completedToday, setCompletedToday] = useState(false);
  const [timerLimitSec, setTimerLimitSec] = useState(180);
  const [remainingSec, setRemainingSec] = useState(180);
  const [problemContentWidth, setProblemContentWidth] = useState(null);
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
    loadMySettings();
    return () => {
      ignore = true;
    };
  }, []);

  async function handleSubmit() {
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
      });
      setResult(data);
      if (mode === "daily") {
        setCompletedToday(true);
        setDaily((current) => current ? { ...current, completed: true } : current);
        fetchMyStats().then(setStats).catch(() => {});
      }
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
  const problemContentStyle = problemContentWidth ? { width: `${problemContentWidth}px` } : undefined;
  const similarityTag =
    mode === "practice" && typeof problem?.similarity_score === "number"
      ? `오늘 문제와 관련도 ${problem.similarity_score}%`
      : null;
  const problemTags = problem
    ? [areaLabel, `${problem.year}학년도`, `${problem.number}번`, similarityTag, `${Math.round(timerLimitSec / 60)}분 제한`].filter(Boolean)
    : [];

  useEffect(() => {
    if (!problem || result || remainingSec <= 0) {
      return undefined;
    }

    const timerId = window.setInterval(() => {
      setRemainingSec((current) => Math.max(0, current - 1));
    }, 1000);

    return () => window.clearInterval(timerId);
  }, [problem, remainingSec, result]);

  useEffect(() => {
    if (!problemContentRef.current || !problem) {
      setProblemContentWidth(null);
      return undefined;
    }

    const measureProblemContent = () => {
      const blocks = problemContentRef.current?.querySelectorAll("[data-problem-content-block]") ?? [];
      const nextWidth = Math.max(
        ...Array.from(blocks).map((block) => block.getBoundingClientRect().width),
        0,
      );
      setProblemContentWidth(nextWidth > 0 ? Math.ceil(nextWidth) : null);
    };

    measureProblemContent();

    const resizeObserver = new ResizeObserver(measureProblemContent);
    const blocks = problemContentRef.current.querySelectorAll("[data-problem-content-block]");
    blocks.forEach((block) => resizeObserver.observe(block));
    window.addEventListener("resize", measureProblemContent);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener("resize", measureProblemContent);
    };
  }, [problem]);

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
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Shell page={page} setPage={setPage}>
      <div className="mx-auto grid w-full max-w-[1360px] min-w-0 gap-7 px-3 py-6 lg:grid-cols-[320px_minmax(0,1fr)] lg:px-7 lg:py-8">
        <aside className="space-y-5">
          <Card className="p-7">
            <div className="mb-8 flex items-center gap-5">
              <Avatar />
              <div>
                <p className="text-xl font-black">ifuril</p>
                <p className="text-sm text-[#666]">level 4</p>
                <div className="mt-4 h-2 w-32 rounded-full bg-ash">
                  <div className="h-2 w-24 rounded-full bg-pepper" />
                </div>
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
            {recentSolved.map(([date, first, second], index) => (
              <div key={date} className="mb-7 grid grid-cols-[18px_1fr] gap-3 last:mb-0">
                <span className={`mt-1 h-3 w-3 rounded-full ${index === 0 ? "bg-pepper" : "border border-smoke bg-white"}`} />
                <div>
                  <p className="mb-3 text-xl font-black">{date}</p>
                  <p className="mb-2 text-xs font-black">{first}</p>
                  <p className="text-xs font-black">{second}</p>
                </div>
              </div>
            ))}
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

              <div className="grid min-w-0 gap-6 xl:grid-cols-[minmax(0,auto)_minmax(320px,380px)] xl:items-start">
                <div className="order-2 min-w-0 xl:order-1">
                  <div
                    ref={problemContentRef}
                    className="inline-grid w-fit max-w-full min-w-0 grid-cols-[minmax(0,auto)] justify-items-start gap-5"
                  >
                    {problem.passage && (
                      <div data-problem-content-block className="w-fit max-w-full rounded-md border border-pepper p-4 sm:p-5">
                        <p className="mb-3 text-sm font-black">[자료] 다음 글을 읽고 물음에 답하시오.</p>
                        <p className="whitespace-pre-line break-keep text-base leading-7">{problem.passage}</p>
                      </div>
                    )}

                    <div data-problem-content-block className="w-fit max-w-full rounded-md border border-pepper p-4 sm:p-5">
                      <p className="whitespace-pre-line break-keep text-base leading-7">{problem.question_text}</p>
                    </div>

                    <div
                      className="grid w-full max-w-full gap-3"
                      style={problemContentStyle}
                    >
                      {problem.choices.map((choice) => {
                        const isSelected = selectedIndex === choice.idx;
                        const isAnswer = result?.answer_index === choice.idx;
                        return (
                          <button
                            key={choice.id}
                            disabled={Boolean(result)}
                            onClick={() => setSelectedIndex(choice.idx)}
                            className={`w-full rounded-md border px-5 py-3 text-left text-base ${
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

                    <div className="grid w-full gap-3 sm:grid-cols-3" style={problemContentStyle}>
                      <Stat label="정답률" value="42%" />
                      <Stat label="평균 풀이" value="4:18" />
                      <Stat label="누적 풀이" value="1,284명" />
                    </div>

                    {result && (
                      <div className="rounded-md border border-pepper p-5" style={problemContentStyle}>
                        <p className="text-xl font-black">{result.is_correct ? "정답입니다." : "오답입니다."}</p>
                        <p className="mt-2 text-sm">
                          선택한 답 {result.selected_index}번 / 정답 {result.answer_index}번
                        </p>
                        <p className="mt-3 whitespace-pre-line text-base leading-7">
                          {result.explanation || "해설 데이터는 아직 준비 중입니다."}
                        </p>
                      </div>
                    )}

                    <label className="block w-full" style={problemContentStyle}>
                      <span className="mb-2 block text-sm font-black">나의 추론 코멘트</span>
                      <textarea
                        value={reasoning}
                        disabled={Boolean(result)}
                        onChange={(event) => setReasoning(event.target.value)}
                        className="min-h-36 w-full rounded-md border border-smoke p-4 text-base leading-7"
                        placeholder="왜 이 답을 골랐는지 먼저 적어보세요."
                      />
                    </label>

                    {error && (
                      <p className="rounded-md border border-pepper bg-paper px-4 py-3 text-sm font-black" style={problemContentStyle}>
                        {error}
                      </p>
                    )}

                    <button
                      disabled={submitting || Boolean(result)}
                      onClick={handleSubmit}
                      className="min-h-12 w-full rounded-md bg-pepper px-5 py-3 text-sm font-black text-white hover:bg-[#444] disabled:cursor-not-allowed disabled:bg-smoke"
                      style={problemContentStyle}
                    >
                      {submitting ? "제출 중..." : result ? "제출 완료" : "정답 제출하기"}
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
