import { getGoogleLoginUrl } from "../api/client";
import Card from "../components/Card";
import Shell from "../components/Shell";

export default function LoginPage({ authMessage, setAuthMessage, setPage }) {
  function handleGoogleLogin() {
    window.location.href = getGoogleLoginUrl();
  }

  function handleDevMode() {
    setAuthMessage("");
    setPage("daily");
  }

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

          {authMessage && (
            <div className="mb-5 rounded-md border border-pepper bg-paper px-4 py-3 text-sm font-black">
              {authMessage}
            </div>
          )}

          <button
            onClick={handleGoogleLogin}
            className="h-12 w-full rounded-md bg-pepper text-sm font-black text-white hover:bg-[#444]"
          >
            Google로 로그인하기
          </button>

          <button
            onClick={handleDevMode}
            className="mt-4 h-12 w-full rounded-md border border-smoke bg-white text-sm font-black text-pepper hover:bg-paper"
          >
            개발 모드로 둘러보기
          </button>
        </Card>
      </div>
    </Shell>
  );
}
