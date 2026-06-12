import { useEffect, useState } from "react";

import { fetchMyPosts, fetchMyStats } from "../api/client";
import ActivityGrid from "../components/ActivityGrid";
import Avatar from "../components/Avatar";
import Card from "../components/Card";
import Shell from "../components/Shell";
import Stat from "../components/Stat";

const areaLabels = {
  reading_comprehension: "언어이해",
  reasoning_argumentation: "추리논증",
};

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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;

    async function loadMyPage() {
      try {
        setLoading(true);
        const [postData, statData] = await Promise.all([fetchMyPosts(), fetchMyStats()]);
        if (!ignore) {
          setPosts(postData);
          setStats(statData);
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
            <Stat label="누적 풀이" value="1문제" />
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
            <Stat label="문제 범위" value="전체 회차 랜덤" />
            <Stat label="타이머 설정" value="3분 제한" />
            <Stat label="오답 복습" value="3일 뒤 자동 재노출" />
            <Stat label="취약 유형" value="추후 추가" className="opacity-50" />
            <Stat label="이번 주 요약" value="추후 추가" className="opacity-50" />
          </div>
        </Card>
      </div>
    </Shell>
  );
}
