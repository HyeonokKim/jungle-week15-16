import { useEffect, useState } from "react";

import { fetchMyPosts, fetchMySettings, fetchMyStats, updateMySettings } from "../api/client";
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

export default function MyPage({ page, setPage }) {
  const [posts, setPosts] = useState([]);
  const [postPage, setPostPage] = useState(1);
  const [stats, setStats] = useState(null);
  const [settings, setSettings] = useState(null);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [settingsMessage, setSettingsMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;

    async function loadMyPage() {
      try {
        setLoading(true);
        const [postData, statData, settingData] = await Promise.all([
          fetchMyPosts(),
          fetchMyStats(),
          fetchMySettings(),
        ]);
        if (!ignore) {
          setPosts(postData);
          setPostPage(1);
          setStats(statData);
          setSettings(settingData);
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

  const readingAccuracy = stats?.area_accuracy.find((item) => item.area === "reading_comprehension")?.accuracy_rate ?? 0;
  const reasoningAccuracy = stats?.area_accuracy.find((item) => item.area === "reasoning_argumentation")?.accuracy_rate ?? 0;
  const weakTypeLabel = problemTypeLabels[settings?.weak_type] ?? null;
  const weakTypeAreaLabel = problemTypeAreaLabels[settings?.weak_type] ?? null;
  const totalPostPages = Math.max(1, Math.ceil(posts.length / POSTS_PER_PAGE));
  const normalizedPostPage = Math.min(postPage, totalPostPages);
  const visiblePosts = posts.slice(
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
          <h2 className="mb-5 text-3xl font-black">내 학습 게시글</h2>
          {loading ? (
            <div className="rounded-md border border-ash p-5 text-sm font-black">학습 게시글을 불러오는 중...</div>
          ) : error ? (
            <div className="rounded-md border border-pepper bg-paper p-5 text-sm font-black">{error}</div>
          ) : posts.length === 0 ? (
            <div className="rounded-md border border-ash p-5 text-sm font-black">아직 작성한 추론 게시글이 없어요.</div>
          ) : (
            <>
              <div className="overflow-hidden rounded-md border border-ash">
                {visiblePosts.map((post) => (
                  <button
                    key={post.id}
                    onClick={() => setPage("board")}
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
                  총 {posts.length}개 중 {(normalizedPostPage - 1) * POSTS_PER_PAGE + 1}-
                  {Math.min(normalizedPostPage * POSTS_PER_PAGE, posts.length)}개 표시
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
            <Stat label="이번 주 요약" value="추후 추가" className="opacity-50" />
          </div>
          <p className="mt-4 min-h-5 text-sm font-black text-[#666]">
            {settingsSaving ? "설정을 저장하는 중..." : settingsMessage}
          </p>
        </Card>
      </div>
    </Shell>
  );
}
