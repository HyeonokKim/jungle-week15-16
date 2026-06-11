import Avatar from "../components/Avatar";
import Card from "../components/Card";
import Shell from "../components/Shell";
import { rankingCards, solvedRows } from "../data/mockData";

export default function BoardPage({ page, setPage }) {
  return (
    <Shell page={page} setPage={setPage} label="03 풀이 현황">
      <div className="space-y-7 px-5 py-8 lg:px-8">
        <Card className="border-pepper p-7">
          <div className="mb-8 flex items-start justify-between gap-4">
            <div>
              <p className="mb-4 text-sm font-black">문제 풀이 랭킹</p>
              <h2 className="text-3xl font-black">누가 제일 많이 풀었을까</h2>
            </div>
            <button className="h-11 rounded-md border border-smoke px-5 text-sm font-black hover:bg-paper">이번 주</button>
          </div>

          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
            {rankingCards.map(([letter, name, status, streak, problem, solved, rate]) => (
              <article key={name} className="rounded-md border border-smoke p-4">
                <div className="mb-5 flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <Avatar letter={letter} size="h-11 w-11" text="text-2xl" />
                    <div>
                      <p className="font-black">{name}</p>
                      <p className="text-xs text-[#666]">{status}</p>
                    </div>
                  </div>
                  <span className="rounded-md bg-ash px-3 py-2 text-xs font-black">{streak}</span>
                </div>
                <p className="mb-5 text-sm font-black">{problem}</p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-md border border-smoke p-3 text-center text-sm">
                    푼 문제 <strong className="text-xl">{solved}</strong>
                  </div>
                  <div className="rounded-md border border-smoke p-3 text-center text-sm">
                    정답률 <strong className="text-xl">{rate}</strong>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </Card>

        <Card className="overflow-hidden">
          <table className="w-full min-w-[720px] border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-ash">
                {["사용자", "최근 풀이 문제", "상태", "정답률"].map((head) => (
                  <th key={head} className="px-7 py-5 font-black">
                    {head}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {solvedRows.map(([name, problem, status, rate]) => (
                <tr key={name} className="border-b border-ash last:border-b-0">
                  <td className="px-7 py-6 font-black">{name}</td>
                  <td className="px-7 py-6">{problem}</td>
                  <td className="px-7 py-6 font-black">{status}</td>
                  <td className="px-7 py-6 font-black">{rate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </Shell>
  );
}
