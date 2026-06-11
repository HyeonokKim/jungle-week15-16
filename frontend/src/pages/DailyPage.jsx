import { useEffect, useState } from "react";

import { fetchDailyProblem, submitAttempt } from "../api/client";
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

export default function DailyPage({ page, setPage }) {
  const [daily, setDaily] = useState(null);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [reasoning, setReasoning] = useState("");
  const [result, setResult] = useState(null);
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

    loadDailyProblem();
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
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  const problem = daily?.problem;
  const areaLabel = problem ? areaLabels[problem.area] : "";

  return (
    <Shell page={page} setPage={setPage} label="02 오늘 문제">
      <div className="grid gap-7 px-5 py-8 lg:grid-cols-[320px_minmax(0,1fr)] lg:px-7">
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
                현재 15일 연속 문제 풀이 중!
              </span>
            </div>
            <ActivityGrid />
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

        <Card className="border-pepper p-7">
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
                  <h2 className="text-3xl font-black">오늘의 LEET 도전을 시작하세요!</h2>
                </div>
                <button className="h-11 rounded-md border border-smoke px-5 text-sm font-black hover:bg-paper">
                  기출문제 자료실
                </button>
              </div>

              <div className="mb-5 flex flex-wrap gap-3">
                {[areaLabel, `${problem.year}학년도`, `${problem.number}번`, "예상 3분"].map((tag) => (
                  <span key={tag} className="rounded-md bg-ash px-4 py-2 text-xs font-black">
                    {tag}
                  </span>
                ))}
              </div>

              {problem.passage && (
                <div className="mb-5 max-h-72 overflow-y-auto rounded-md border border-pepper p-5">
                  <p className="mb-3 text-sm font-black">[자료] 다음 글을 읽고 물음에 답하시오.</p>
                  <p className="whitespace-pre-line leading-7">{problem.passage}</p>
                </div>
              )}

              <div className="mb-5 rounded-md border border-pepper p-5">
                <p className="mb-3 text-sm font-black">[문제] {problem.number}번</p>
                <p className="whitespace-pre-line leading-7">{problem.question_text}</p>
              </div>

              <div className="mb-6 space-y-3">
                {problem.choices.map((choice) => {
                  const isSelected = selectedIndex === choice.idx;
                  const isAnswer = result?.answer_index === choice.idx;
                  return (
                    <button
                      key={choice.id}
                      disabled={Boolean(result)}
                      onClick={() => setSelectedIndex(choice.idx)}
                      className={`w-full rounded-md border px-5 py-3 text-left text-sm ${
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

              <label className="mb-6 block">
                <span className="mb-2 block text-sm font-black">나의 추론 코멘트</span>
                <textarea
                  value={reasoning}
                  disabled={Boolean(result)}
                  onChange={(event) => setReasoning(event.target.value)}
                  className="min-h-28 w-full rounded-md border border-smoke p-4 leading-7"
                  placeholder="왜 이 답을 골랐는지 먼저 적어보세요."
                />
              </label>

              {error && <p className="mb-4 rounded-md border border-pepper bg-paper px-4 py-3 text-sm font-black">{error}</p>}

              {result && (
                <div className="mb-6 rounded-md border border-pepper p-5">
                  <p className="text-xl font-black">{result.is_correct ? "정답입니다." : "오답입니다."}</p>
                  <p className="mt-2 text-sm">
                    선택한 답 {result.selected_index}번 / 정답 {result.answer_index}번
                  </p>
                  <p className="mt-3 whitespace-pre-line text-sm leading-7">
                    {result.explanation || "해설 데이터는 아직 준비 중입니다."}
                  </p>
                </div>
              )}

              <div className="grid gap-3 md:grid-cols-[repeat(3,minmax(0,1fr))_minmax(160px,1fr)]">
                <Stat label="정답률" value="42%" />
                <Stat label="평균 풀이" value="4:18" />
                <Stat label="누적 풀이" value="1,284명" />
                <button
                  disabled={submitting || Boolean(result)}
                  onClick={handleSubmit}
                  className="h-full min-h-12 rounded-md bg-pepper text-sm font-black text-white hover:bg-[#444] disabled:cursor-not-allowed disabled:bg-smoke"
                >
                  {submitting ? "제출 중..." : result ? "제출 완료" : "정답 제출하기"}
                </button>
              </div>
            </>
          )}
        </Card>
      </div>
    </Shell>
  );
}
