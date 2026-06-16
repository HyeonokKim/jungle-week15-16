const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const TOKEN_STORAGE_KEY = "haripool_access_token";
export const AUTH_REQUIRED_EVENT = "haripool:auth-required";

async function request(path, options = {}) {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const detail = Array.isArray(errorBody.detail)
      ? errorBody.detail.map((item) => item.msg).join(", ")
      : errorBody.detail;
    if (response.status === 401) {
      clearAccessToken();
      window.dispatchEvent(new CustomEvent(AUTH_REQUIRED_EVENT, { detail: detail || "로그인이 필요합니다." }));
    }
    throw new Error(detail || "API 요청에 실패했습니다.");
  }

  return response.json();
}

export function getGoogleLoginUrl() {
  return `${API_BASE_URL}/auth/google/login`;
}

export function fetchGoogleLoginUrl() {
  return request("/auth/google/login-url");
}

export function getAccessToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setAccessToken(token) {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearAccessToken() {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export function hasAccessToken() {
  return Boolean(getAccessToken());
}

export function consumeTokenFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");
  if (!token) {
    return null;
  }

  setAccessToken(token);
  params.delete("token");
  const nextQuery = params.toString();
  const nextUrl = `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ""}${window.location.hash}`;
  window.history.replaceState({}, "", nextUrl);
  return token;
}

export function fetchAuthMe() {
  return request("/auth/me");
}

export function fetchDailyProblem() {
  return request("/daily");
}

export function fetchPracticeProblem() {
  return request("/practice/next");
}

export function submitAttempt({ problemId, selectedIndex, reasoning, solveDurationSec }) {
  return request("/attempts", {
    method: "POST",
    body: JSON.stringify({
      problem_id: problemId,
      selected_index: selectedIndex,
      reasoning,
      solve_duration_sec: solveDurationSec,
    }),
  });
}

export function generateAIExplanation(attemptId) {
  return request(`/attempts/${attemptId}/ai-explanation`, {
    method: "POST",
  });
}

export function fetchAIExplanation(attemptId) {
  return request(`/attempts/${attemptId}/ai-explanation`);
}

export function fetchProblemBoard(problemId) {
  return request(`/problems/${problemId}/board`);
}

export function updateBoardPost({ problemId, postId, content }) {
  return request(`/problems/${problemId}/board/posts/${postId}`, {
    method: "PATCH",
    body: JSON.stringify({ content }),
  });
}

export function deleteBoardPost({ problemId, postId }) {
  return request(`/problems/${problemId}/board/posts/${postId}`, {
    method: "DELETE",
  });
}

export function createBoardComment({ problemId, postId, content }) {
  return request(`/problems/${problemId}/board/posts/${postId}/comments`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export function fetchMyPosts() {
  return request("/me/posts");
}

export function fetchMyAttemptHistory() {
  return request("/me/attempt-history");
}

export function fetchMyWeeklySummary() {
  return request("/me/weekly-summary");
}

export function fetchMyNotionConnection() {
  return request("/me/notion-connection");
}

export function fetchNotionLoginUrl() {
  return request("/auth/notion/login-url");
}

export function saveMyWeeklySummaryToNotion() {
  return request("/me/weekly-summary/notion", {
    method: "POST",
  });
}

export function fetchMyStats() {
  return request("/stats/me");
}

export function fetchMySettings() {
  return request("/settings/me");
}

export function updateMySettings(payload) {
  return request("/settings/me", {
    method: "PUT",
    body: JSON.stringify({
      ...payload,
    }),
  });
}
