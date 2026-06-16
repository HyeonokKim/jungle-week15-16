import { useEffect, useState } from "react";

import {
  fetchNotionLoginUrl,
  fetchMyNotionConnection,
  fetchMyPosts,
  fetchMySettings,
  fetchMyStats,
  fetchMyWeeklySummary,
  saveMyWeeklySummaryToNotion,
  updateMySettings,
} from "../api/client";
import Avatar from "../components/Avatar";
import Card from "../components/Card";
import SettingOptionGroup from "../components/SettingOptionGroup";
import Shell from "../components/Shell";
import Stat from "../components/Stat";

const areaLabels = {
  reading_comprehension: "언어이해",
  reasoning_argumentation: "추리논증",
};

const problemScopeOptions = [
  { label: "전체 회차 랜덤", value: "all_random" },
  { label: "최신 3개년", value: "recent_3y" },
  { label: "최신 5개년", value: "recent_5y" },
];

const timerOptions = [
  { label: "2분 제한", value: 120 },
  { label: "3분 제한", value: 180 },
  { label: "4분 제한", value: 240 },
];

const reviewOptions = [
  { label: "3일 뒤 자동 재노출", value: 3 },
  { label: "5일 뒤 자동 재노출", value: 5 },
  { label: "7일 뒤 자동 재노출", value: 7 },
  { label: "재노출 안 함", value: null },
];

const problemTypeLabels = {
  main_claim: "핵심 주장",
  detail_matching: "세부 일치",
  inference: "추론",
  structure_analysis: "구조 파악",
  conditional_reasoning: "조건 추론",
  strengthen_weaken: "강화/약화",
  error_identification: "오류 찾기",
  principle_application: "원리 적용",
  data_interpretation: "자료 해석",
};

const problemTypeAreaLabels = {
  main_claim: "언어이해",
  detail_matching: "언어이해",
  inference: "언어이해",
  structure_analysis: "언어이해",
  conditional_reasoning: "추리논증",
  strengthen_weaken: "추리논증",
  error_identification: "추리논증",
  principle_application: "추리논증",
  data_interpretation: "추리논증",
};

const POSTS_PER_PAGE = 5;

function formatDate(value) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

function formatDuration(seconds) {
  if (seconds == null) {
    return "-";
  }
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  if (minutes === 0) {
    return `${remainder}초`;
  }
  return `${minutes}분 ${remainder}초`;
}

export default function MyPage({ page, setPage, onOpenBoardProblem, notionCallbackStatus }) {
  const [posts, setPosts] = useState([]);
  const [postPage, setPostPage] = useState(1);
  const [postSearchQuery, setPostSearchQuery] = useState("");
  const [stats, setStats] = useState(null);
  const [settings, setSettings] = useState(null);
  const [weeklySummary, setWeeklySummary] = useState(null);
  const [notionConnection, setNotionConnection] = useState(null);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [settingsMessage, setSettingsMessage] = useState("");
  const [notionConnecting, setNotionConnecting] = useState(false);
  const [notionSaving, setNotionSaving] = useState(false);
  const [notionMessage, setNotionMessage] = useState("");
  const [notionPageUrl, setNotionPageUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;

    async function loadMyPage() {
      try {
        setLoading(true);
        const [postData, statData, settingData, weeklySummaryData, notionConnectionData] = await Promise.all([
          fetchMyPosts(),
          fetchMyStats(),
          fetchMySettings(),
          fetchMyWeeklySummary(),
          fetchMyNotionConnection(),
        ]);
        if (!ignore) {
          setPosts(postData);
          setPostPage(1);
          setStats(statData);
          setSettings(settingData);
          setWeeklySummary(weeklySummaryData);
          setNotionConnection(notionConnectionData);
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

    loadMyPage();
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    if (notionCallbackStatus === "connected") {
      setNotionMessage("Notion 연결이 완료됐어요.");
    } else if (notionCallbackStatus === "denied") {
      setNotionMessage("Notion 연결이 취소됐어요.");
    } else if (notionCallbackStatus === "failed") {
      setNotionMessage("Notion 연결에 실패했어요.");
    }
  }, [notionCallbackStatus]);

  const readingAccuracy = stats?.area_accuracy.find((item) => item.area === "reading_comprehension")?.accuracy_rate ?? 0;
  const reasoningAccuracy = stats?.area_accuracy.find((item) => item.area === "reasoning_argumentation")?.accuracy_rate ?? 0;
  const weakTypeLabel = problemTypeLabels[settings?.weak_type] ?? null;
  const weakTypeAreaLabel = problemTypeAreaLabels[settings?.weak_type] ?? null;
  const normalizedPostSearchQuery = postSearchQuery.trim().toLowerCase();
  const filteredPosts = normalizedPostSearchQuery
    ? posts.filter((post) => {
        const searchableText = [
          post.title,
          areaLabels[post.area],
          post.is_correct ? "정답" : "오답",
          formatDate(post.created_at),
        ]
          .join(" ")
          .toLowerCase();
        return searchableText.includes(normalizedPostSearchQuery);
      })
    : posts;
  const totalPostPages = Math.max(1, Math.ceil(filteredPosts.length / POSTS_PER_PAGE));
  const normalizedPostPage = Math.min(postPage, totalPostPages);
  const visiblePosts = filteredPosts.slice(
    (normalizedPostPage - 1) * POSTS_PER_PAGE,
    normalizedPostPage * POSTS_PER_PAGE,
  );
  const pageNumbers = Array.from({ length: totalPostPages }, (_, index) => index + 1).filter(
    (pageNumber) =>
      totalPostPages <= 5 ||
      pageNumber === 1 ||
      pageNumber === totalPostPages ||
      Math.abs(pageNumber - normalizedPostPage) <= 1,
  );

  async function handleSettingsChange(payload) {
    try {
      setSettingsSaving(true);
      const updatedSettings = await updateMySettings(payload);
      setSettings(updatedSettings);
      setSettingsMessage("설정이 저장됐어요.");
    } catch (err) {
      setSettingsMessage(err.message);
    } finally {
      setSettingsSaving(false);
    }
  }

  async function handleSaveWeeklySummaryToNotion() {
    if (!notionConnection?.connected) {
      setNotionMessage("Notion을 먼저 연결해 주세요.");
      return;
    }
    if (!notionConnection.default_page_id) {
      setNotionMessage("Notion 템플릿 저장 위치를 찾을 수 없어요. Notion을 다시 연결해 주세요.");
      return;
    }
    try {
      setNotionSaving(true);
      setNotionMessage("");
      setNotionPageUrl("");
      const result = await saveMyWeeklySummaryToNotion();
      setNotionMessage(result.message);
      setNotionPageUrl(result.url ?? "");
    } catch (err) {
      setNotionMessage(err.message);
    } finally {
      setNotionSaving(false);
    }
  }

  async function handleConnectNotion() {
    try {
      setNotionConnecting(true);
      setNotionMessage("");
      const result = await fetchNotionLoginUrl();
      if (!result.url) {
        throw new Error("Notion 연결 URL을 받지 못했어요.");
      }
      window.location.assign(result.url);
      window.setTimeout(() => {
        setNotionConnecting(false);
      }, 3000);
    } catch (err) {
      setNotionMessage(err.message);
      setNotionConnecting(false);
    }
  }

  return (
    <Shell page={page} setPage={setPage}>
      <div className="mx-auto w-full max-w-[1100px] space-y-7 px-4 py-8 sm:px-5 lg:px-8">
        <Card className="border-pepper px-6 py-8">
          <div className="mb-10 grid place-items-center">
            <Avatar />
            <h2 className="mt-5 text-3xl font-black">{stats?.nickname ?? "ifuril"}</h2>
          </div>

          <div className="grid gap-4 md:grid-cols-4">
            <Stat label="가입일" value={formatDate(stats?.created_at)} />
            <Stat label="누적 풀이" value={`${stats?.total_attempts ?? 0}문제`} />
            <Stat label="스트릭" value={`${stats?.current_streak ?? 0}일`} />
            <Stat label="정답률" value={`${stats?.accuracy_rate ?? 0}%`} />
          </div>
        </Card>

        <Card className="p-6">
          <p className="mb-3 text-sm font-black">내 정보</p>
          <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <h2 className="text-3xl font-black">내 학습 게시글</h2>
            <label className="w-full md:max-w-[320px]">
              <span className="mb-2 block text-xs font-black text-[#666]">문제 검색</span>
              <input
                type="search"
                value={postSearchQuery}
                onChange={(event) => {
                  setPostSearchQuery(event.target.value);
                  setPostPage(1);
                }}
                placeholder="문제명, 영역, 정답 여부"
                className="h-11 w-full rounded-md border border-smoke px-4 text-sm font-black outline-none focus:border-pepper"
              />
            </label>
          </div>
          {loading ? (
            <div className="rounded-md border border-ash p-5 text-sm font-black">학습 게시글을 불러오는 중...</div>
          ) : error ? (
            <div className="rounded-md border border-pepper bg-paper p-5 text-sm font-black">{error}</div>
          ) : posts.length === 0 ? (
            <div className="rounded-md border border-ash p-5 text-sm font-black">아직 작성한 추론 게시글이 없어요.</div>
          ) : filteredPosts.length === 0 ? (
            <div className="rounded-md border border-ash p-5 text-sm font-black">검색 결과가 없어요.</div>
          ) : (
            <>
              <div className="overflow-hidden rounded-md border border-ash">
                {visiblePosts.map((post) => (
                  <button
                    key={post.id}
                    onClick={() => onOpenBoardProblem(post.problem_id)}
                    className="grid w-full gap-3 border-b border-ash px-5 py-4 text-left last:border-b-0 md:grid-cols-[1fr_100px_80px_120px] md:items-center"
                  >
                    <strong>{post.title}</strong>
                    <span className="rounded-md bg-ash px-3 py-2 text-center text-xs font-black">{areaLabels[post.area]}</span>
                    <span className={post.is_correct ? "font-black text-pepper" : "font-black text-[#777]"}>
                      {post.is_correct ? "정답" : "오답"}
                    </span>
                    <span className="text-sm text-[#666]">{formatDate(post.created_at)}</span>
                  </button>
                ))}
              </div>

              <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm font-black text-[#666]">
                  총 {filteredPosts.length}개 중 {(normalizedPostPage - 1) * POSTS_PER_PAGE + 1}-
                  {Math.min(normalizedPostPage * POSTS_PER_PAGE, filteredPosts.length)}개 표시
                  {postSearchQuery.trim() && ` / 전체 ${posts.length}개`}
                </p>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={normalizedPostPage === 1}
                    onClick={() => setPostPage((current) => Math.max(1, current - 1))}
                    className="h-10 rounded-md border border-smoke px-4 text-sm font-black hover:bg-paper disabled:cursor-not-allowed disabled:bg-ash disabled:text-[#777]"
                  >
                    이전
                  </button>
                  {pageNumbers.map((pageNumber, index) => {
                    const previousPageNumber = pageNumbers[index - 1];
                    const showGap = previousPageNumber && pageNumber - previousPageNumber > 1;
                    return (
                      <div key={pageNumber} className="flex gap-2">
                        {showGap && (
                          <span className="grid h-10 w-8 place-items-center text-sm font-black text-[#777]">...</span>
                        )}
                        <button
                          type="button"
                          onClick={() => setPostPage(pageNumber)}
                          className={`h-10 min-w-10 rounded-md border px-3 text-sm font-black ${
                            normalizedPostPage === pageNumber
                              ? "border-pepper bg-pepper text-white"
                              : "border-smoke hover:bg-paper"
                          }`}
                        >
                          {pageNumber}
                        </button>
                      </div>
                    );
                  })}
                  <button
                    type="button"
                    disabled={normalizedPostPage === totalPostPages}
                    onClick={() => setPostPage((current) => Math.min(totalPostPages, current + 1))}
                    className="h-10 rounded-md border border-smoke px-4 text-sm font-black hover:bg-paper disabled:cursor-not-allowed disabled:bg-ash disabled:text-[#777]"
                  >
                    다음
                  </button>
                </div>
              </div>
            </>
          )}
        </Card>

        <Card className="p-6">
          <p className="mb-3 text-sm font-black">환경 설정</p>
          <h2 className="mb-5 text-3xl font-black">학습 설정</h2>
          <div className="grid gap-4 lg:grid-cols-3">
            <SettingOptionGroup
              label="문제 범위"
              value={settings?.problem_scope}
              options={problemScopeOptions}
              onChange={(problem_scope) => handleSettingsChange({ problem_scope })}
            />
            <SettingOptionGroup
              label="타이머 설정"
              value={settings?.timer_limit_sec}
              options={timerOptions}
              onChange={(timer_limit_sec) => handleSettingsChange({ timer_limit_sec })}
            />
            <SettingOptionGroup
              label="오답 복습"
              value={settings?.review_interval_days}
              options={reviewOptions}
              onChange={(review_interval_days) => handleSettingsChange({ review_interval_days })}
            />
            <div className="rounded-md border border-smoke bg-white px-4 py-3">
              <p className="text-xs font-medium text-[#666]">취약 유형</p>
              {weakTypeLabel ? (
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <span className="rounded-md bg-pepper px-3 py-2 text-sm font-black text-white">{weakTypeLabel}</span>
                  <span className="rounded-md bg-paper px-3 py-2 text-xs font-black text-[#555]">{weakTypeAreaLabel}</span>
                </div>
              ) : (
                <p className="mt-1 text-xl font-black text-[#777]">풀이 기록 없음</p>
              )}
            </div>
            <div className="rounded-md border border-smoke bg-white px-4 py-3 lg:col-span-2">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-medium text-[#666]">이번 주 요약</p>
                  <p className="mt-1 text-xl font-black">
                    {weeklySummary
                      ? `${formatDate(weeklySummary.week_start)} - ${formatDate(weeklySummary.week_end)}`
                      : "불러오는 중"}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {notionConnection?.connected && (
                    <span className="rounded-md bg-paper px-3 py-2 text-xs font-black text-[#555]">
                      {notionConnection.default_page_id
                        ? notionConnection.workspace_name || "Notion 연결됨"
                        : "저장 위치 없음"}
                    </span>
                  )}
                  {weeklySummary?.weak_type && (
                    <span className="rounded-md bg-paper px-3 py-2 text-xs font-black text-[#555]">
                      {problemTypeLabels[weeklySummary.weak_type] ?? weeklySummary.weak_type}
                    </span>
                  )}
                  {!notionConnection?.connected && (
                    <button
                      type="button"
                      disabled={notionConnecting}
                      onClick={handleConnectNotion}
                      className="h-10 rounded-md border border-pepper px-4 text-sm font-black hover:bg-paper disabled:cursor-not-allowed disabled:border-ash disabled:bg-ash disabled:text-[#777]"
                    >
                      {notionConnecting ? "연결 중..." : "Notion 연결"}
                    </button>
                  )}
                  <button
                    type="button"
                    disabled={!weeklySummary || !notionConnection?.connected || !notionConnection?.default_page_id || notionSaving}
                    onClick={handleSaveWeeklySummaryToNotion}
                    className="h-10 rounded-md border border-pepper px-4 text-sm font-black hover:bg-paper disabled:cursor-not-allowed disabled:border-ash disabled:bg-ash disabled:text-[#777]"
                  >
                    {notionSaving ? "저장 중..." : "Notion에 저장"}
                  </button>
                </div>
              </div>
              <p className="leet-text mt-4 text-sm font-black leading-6 text-[#555]">
                {weeklySummary?.summary_text ?? "이번 주 학습 요약을 불러오는 중..."}
              </p>
              <div className="mt-4 grid gap-2 sm:grid-cols-4">
                <div className="rounded-md bg-paper px-3 py-2">
                  <p className="text-[11px] font-black text-[#777]">풀이</p>
                  <p className="text-sm font-black">{weeklySummary?.total_attempts ?? 0}문제</p>
                </div>
                <div className="rounded-md bg-paper px-3 py-2">
                  <p className="text-[11px] font-black text-[#777]">정답률</p>
                  <p className="text-sm font-black">{weeklySummary?.accuracy_rate ?? 0}%</p>
                </div>
                <div className="rounded-md bg-paper px-3 py-2">
                  <p className="text-[11px] font-black text-[#777]">추가 연습</p>
                  <p className="text-sm font-black">{weeklySummary?.practice_attempts ?? 0}문제</p>
                </div>
                <div className="rounded-md bg-paper px-3 py-2">
                  <p className="text-[11px] font-black text-[#777]">평균 풀이</p>
                  <p className="text-sm font-black">{formatDuration(weeklySummary?.average_solve_duration_sec)}</p>
                </div>
              </div>
              <p className="mt-3 min-h-5 text-sm font-black text-[#666]">
                {notionPageUrl ? (
                  <a href={notionPageUrl} target="_blank" rel="noreferrer" className="underline underline-offset-4">
                    {notionMessage}
                  </a>
                ) : (
                  notionMessage
                )}
              </p>
            </div>
          </div>
          <p className="mt-4 min-h-5 text-sm font-black text-[#666]">
            {settingsSaving ? "설정을 저장하는 중..." : settingsMessage}
          </p>
        </Card>
      </div>
    </Shell>
  );
}
