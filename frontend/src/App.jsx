import { useEffect, useState } from "react";

import { AUTH_REQUIRED_EVENT, consumeTokenFromUrl, hasAccessToken } from "./api/client";
import BoardPage from "./pages/BoardPage";
import DailyPage from "./pages/DailyPage";
import LoginPage from "./pages/LoginPage";
import MyPage from "./pages/MyPage";

export default function App() {
  const [page, setPage] = useState(() => (hasAccessToken() ? "daily" : "login"));
  const [authMessage, setAuthMessage] = useState("");

  useEffect(() => {
    const token = consumeTokenFromUrl();
    if (token) {
      setAuthMessage("");
      setPage("daily");
    }

    function handleAuthRequired(event) {
      setAuthMessage(event.detail || "로그인이 필요합니다.");
      setPage("login");
    }

    window.addEventListener(AUTH_REQUIRED_EVENT, handleAuthRequired);
    return () => window.removeEventListener(AUTH_REQUIRED_EVENT, handleAuthRequired);
  }, []);

  if (page === "login") {
    return <LoginPage authMessage={authMessage} setAuthMessage={setAuthMessage} setPage={setPage} />;
  }

  if (page === "board") {
    return <BoardPage page={page} setPage={setPage} />;
  }

  if (page === "mypage") {
    return <MyPage page={page} setPage={setPage} />;
  }

  return <DailyPage page={page} setPage={setPage} />;
}
