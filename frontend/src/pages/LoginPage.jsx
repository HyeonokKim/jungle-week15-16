import { useState } from "react";

import { fetchGoogleLoginUrl } from "../api/client";
import Card from "../components/Card";
import Shell from "../components/Shell";

export default function LoginPage({ authMessage, setAuthMessage, setPage }) {
  const [loginLoading, setLoginLoading] = useState(false);

  async function handleGoogleLogin() {
    try {
      setLoginLoading(true);
      setAuthMessage("");
      const { url } = await fetchGoogleLoginUrl();
      window.location.href = url;
    } catch (err) {
      setAuthMessage(
        err.message === "Failed to fetch"
          ? "백엔드 서버가 실행 중인지 확인해주세요."
          : err.message
      );
    } finally {
      setLoginLoading(false);
    }
  }

  return (
    <Shell page="login" setPage={setPage}>
      <div className="grid min-h-[calc(100vh-11rem)] place-items-center px-4 py-8 sm:px-6 sm:py-12 lg:min-h-[680px]">
        <Card className="w-full max-w-sm border-pepper p-6 sm:p-10">
          <div className="mb-7 flex items-center gap-4 sm:gap-6">
            <div className="grid h-11 w-11 shrink-0 place-items-center rounded-md bg-pepper text-lg font-black text-white sm:h-12 sm:w-12">
              H
            </div>
            <h2 className="text-2xl font-black leading-tight">로그인</h2>
          </div>

          {authMessage && (
            <div className="mb-5 rounded-md border border-pepper bg-paper px-4 py-3 text-sm font-black">
              {authMessage}
            </div>
          )}

          <button
            onClick={handleGoogleLogin}
            disabled={loginLoading}
            className="min-h-12 w-full rounded-md bg-pepper px-4 py-3 text-sm font-black text-white hover:bg-[#444] disabled:cursor-not-allowed disabled:bg-smoke"
          >
            {loginLoading ? "Google 로그인 준비 중..." : "Google로 로그인하기"}
          </button>
        </Card>
      </div>
    </Shell>
  );
}
