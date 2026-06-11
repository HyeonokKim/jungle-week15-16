import ActivityGrid from "../components/ActivityGrid";
import Avatar from "../components/Avatar";
import Card from "../components/Card";
import Shell from "../components/Shell";
import Stat from "../components/Stat";
import { recentSolved } from "../data/mockData";

export default function DailyPage({ page, setPage }) {
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
            {["추리논증", "2026학년도", "12번", "예상 3분"].map((tag) => (
              <span key={tag} className="rounded-md bg-ash px-4 py-2 text-xs font-black">
                {tag}
              </span>
            ))}
          </div>

          <div className="mb-5 rounded-md border border-pepper p-5">
            <p className="mb-3 text-sm font-black">[자료] 다음 글을 읽고 물음에 답하시오.</p>
            <p className="leading-7">
              그리고 그의 선장은 은밀한 질서에 있는데, 모양은 흙이 둘레와 그 오직은 영어의 징작을
              본다고. 암양의 발을 돌려대려 나는 자망과 짐을 벌어...
            </p>
          </div>

          <div className="mb-5 rounded-md border border-pepper p-5">
            <p className="mb-3 text-sm font-black">[문제] 위 글을 근거로 &lt;보기&gt;를 이해한 것으로 가장 적절한 것은?</p>
            <p className="leading-7">
              보기의 논지는 글의 핵심 비교 기준을 놓치고 있다. 대상의 정당화 기준과 적용 범위를 함께 묻고 있다.
            </p>
          </div>

          <div className="mb-6 space-y-3">
            {[
              "① 보기의 논지는 글의 핵심 비교 기준을 놓치고 있다.",
              "② 윗글은 대상의 정당화 기준과 적용 범위를 함께 묻고 있다.",
              "③ 보기는 원문의 인과 관계를 필연 관계로 과장하고 있다.",
            ].map((choice, index) => (
              <button
                key={choice}
                className={`w-full rounded-md border px-5 py-3 text-left text-sm ${
                  index === 1 ? "border-pepper bg-ash font-black" : "border-smoke bg-white hover:bg-paper"
                }`}
              >
                {choice}
              </button>
            ))}
          </div>

          <div className="grid gap-3 md:grid-cols-[repeat(3,minmax(0,1fr))_minmax(160px,1fr)]">
            <Stat label="정답률" value="42%" />
            <Stat label="평균 풀이" value="4:18" />
            <Stat label="누적 풀이" value="1,284명" />
            <button className="h-full min-h-12 rounded-md bg-pepper text-sm font-black text-white hover:bg-[#444]">
              정답 제출하기
            </button>
          </div>
        </Card>
      </div>
    </Shell>
  );
}
