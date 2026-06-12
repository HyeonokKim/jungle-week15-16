import { useEffect, useState } from "react";

import { consumeTokenFromUrl, getAccessToken } from "./api/client";
import BoardPage from "./pages/BoardPage";
import DailyPage from "./pages/DailyPage";
import LoginPage from "./pages/LoginPage";
import MyPage from "./pages/MyPage";

export default function App() {
  const [page, setPage] = useState(() => (getAccessToken() ? "daily" : "login"));

  useEffect(() => {
    const token = consumeTokenFromUrl();
    if (token) {
      setPage("daily");
    }
  }, []);

  if (page === "login") {
    return <LoginPage setPage={setPage} />;
  }

  if (page === "board") {
    return <BoardPage page={page} setPage={setPage} />;
  }

  if (page === "mypage") {
    return <MyPage page={page} setPage={setPage} />;
  }

  return <DailyPage page={page} setPage={setPage} />;
}
