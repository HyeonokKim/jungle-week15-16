import { useEffect, useState } from "react";

import { fetchMyPosts, fetchMySettings, fetchMyStats, updateMySettings } from "../api/client";
import ActivityGrid from "../components/ActivityGrid";
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
      <div className="space-y-7 px-5 py-8 lg:px-8">
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
            <div className="overflow-hidden rounded-md border border-ash">
              {posts.map((post) => (
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
            <Stat label="취약 유형" value="추후 추가" className="opacity-50" />
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
