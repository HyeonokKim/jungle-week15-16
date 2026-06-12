import Card from "../components/Card";
import Shell from "../components/Shell";

export default function LoginPage({ setPage }) {
  return (
    <Shell page="login" setPage={setPage}>
      <div className="grid min-h-[680px] place-items-center px-6 py-10">
        <Card className="w-full max-w-[330px] border-pepper p-8 sm:p-10">
          <div className="mb-7 flex items-center gap-6">
            <div className="grid h-12 w-12 place-items-center rounded-md bg-pepper text-lg font-black text-white">
              H
            </div>
            <h2 className="text-2xl font-black">로그인</h2>
          </div>

          <label className="mb-5 block">
            <span className="mb-2 block text-xs font-black">아이디</span>
            <input
              defaultValue="hyunwoo@haripool.kr"
              className="h-12 w-full rounded-md border border-smoke px-4 text-sm"
            />
          </label>

          <label className="mb-6 block">
            <span className="mb-2 block text-xs font-black">비밀번호</span>
            <input
              type="password"
              defaultValue="password"
              className="h-12 w-full rounded-md border border-smoke px-4 text-sm"
            />
          </label>

          <button
            onClick={() => setPage("daily")}
            className="h-12 w-full rounded-md bg-pepper text-sm font-black text-white hover:bg-[#444]"
          >
            로그인하기
          </button>

          <div className="mt-4 flex items-center justify-around text-sm font-black">
            <button>계정 만들기</button>
            <button>비밀번호 찾기</button>
          </div>
        </Card>
      </div>
    </Shell>
  );
}
