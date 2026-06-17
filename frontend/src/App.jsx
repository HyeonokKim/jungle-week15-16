import { useEffect, useState } from "react";

import { AUTH_REQUIRED_EVENT, consumeTokenFromUrl, hasAccessToken } from "./api/client";
import BoardPage from "./pages/BoardPage";
import DailyPage from "./pages/DailyPage";
import LoginPage from "./pages/LoginPage";
import MyPage from "./pages/MyPage";

export default function App() {
  const [page, setPage] = useState(() => (hasAccessToken() ? "daily" : "login"));
  const [authMessage, setAuthMessage] = useState("");
  const [notionCallbackStatus, setNotionCallbackStatus] = useState("");
  const [selectedBoardProblemId, setSelectedBoardProblemId] = useState(null);

  function navigatePage(nextPage) {
    if (nextPage === "board") {
      setSelectedBoardProblemId(null);
    }
    setPage(nextPage);
  }

  function openProblemBoard(problemId) {
    setSelectedBoardProblemId(problemId);
    setPage("board");
  }

  useEffect(() => {
    const token = consumeTokenFromUrl();
    if (token) {
      setAuthMessage("");
      setPage("daily");
    }
    const params = new URLSearchParams(window.location.search);
    const notionStatus = params.get("notion");
    if (notionStatus) {
      setNotionCallbackStatus(notionStatus);
      setPage("mypage");
      params.delete("notion");
      const nextQuery = params.toString();
      const nextUrl = `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ""}${window.location.hash}`;
      window.history.replaceState({}, "", nextUrl);
    }

    function handleAuthRequired(event) {
      setAuthMessage(event.detail || "로그인이 필요합니다.");
      setPage("login");
    }

    window.addEventListener(AUTH_REQUIRED_EVENT, handleAuthRequired);
    return () => window.removeEventListener(AUTH_REQUIRED_EVENT, handleAuthRequired);
  }, []);

  if (page === "login") {
    return <LoginPage authMessage={authMessage} setAuthMessage={setAuthMessage} setPage={navigatePage} />;
  }

  if (page === "board") {
    return <BoardPage page={page} setPage={navigatePage} selectedProblemId={selectedBoardProblemId} />;
  }

  if (page === "mypage") {
    return (
      <MyPage
        page={page}
        setPage={navigatePage}
        onOpenBoardProblem={openProblemBoard}
        notionCallbackStatus={notionCallbackStatus}
      />
    );
  }

  return <DailyPage page={page} setPage={navigatePage} onOpenBoardProblem={openProblemBoard} />;
}
