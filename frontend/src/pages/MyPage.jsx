import ActivityGrid from "../components/ActivityGrid";
import Avatar from "../components/Avatar";
import Card from "../components/Card";
import Shell from "../components/Shell";
import Stat from "../components/Stat";
import { myPosts } from "../data/mockData";

export default function MyPage({ page, setPage }) {
  return (
    <Shell page={page} setPage={setPage} label="04 마이 페이지">
      <div className="space-y-7 px-5 py-8 lg:px-8">
        <Card className="border-pepper px-6 py-8">
          <div className="mb-10 grid place-items-center">
            <Avatar />
            <h2 className="mt-5 text-3xl font-black">ifuril</h2>
          </div>

          <div className="grid gap-4 md:grid-cols-4">
            <Stat label="가입일" value="2026.05.01" />
            <Stat label="목표" value="매일 1문제" />
            <Stat label="스트릭" value="15일" />
            <Stat label="레벨" value="level 4" />
          </div>
        </Card>

        <Card className="p-6">
          <p className="mb-3 text-sm font-black">내 정보</p>
          <h2 className="mb-5 text-3xl font-black">내 학습 게시글</h2>
          <div className="overflow-hidden rounded-md border border-ash">
            {myPosts.map(([title, area, result, date]) => (
              <button
                key={`${title}-${date}`}
                className="grid w-full gap-3 border-b border-ash px-5 py-4 text-left last:border-b-0 md:grid-cols-[1fr_100px_80px_120px] md:items-center"
              >
                <strong>{title}</strong>
                <span className="rounded-md bg-ash px-3 py-2 text-center text-xs font-black">{area}</span>
                <span className={result === "정답" ? "font-black text-pepper" : "font-black text-[#777]"}>{result}</span>
                <span className="text-sm text-[#666]">{date}</span>
              </button>
            ))}
          </div>
        </Card>

        <Card className="p-6">
          <p className="mb-3 text-sm font-black">학습 기록</p>
          <h2 className="mb-5 text-3xl font-black">잔디와 통계</h2>
          <div className="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
            <div className="rounded-md border border-ash p-5">
              <p className="mb-4 font-black">나의 잔디밭</p>
              <ActivityGrid />
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <Stat label="누적 풀이" value="42문제" />
              <Stat label="언어이해 정답률" value="79%" />
              <Stat label="추리논증 정답률" value="84%" />
            </div>
          </div>
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
