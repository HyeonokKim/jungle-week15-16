const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const DEV_USER_ID = 1;

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const detail = Array.isArray(errorBody.detail)
      ? errorBody.detail.map((item) => item.msg).join(", ")
      : errorBody.detail;
    throw new Error(detail || "API 요청에 실패했습니다.");
  }

  return response.json();
}

export function fetchDailyProblem() {
  return request(`/daily?user_id=${DEV_USER_ID}`);
}

export function fetchPracticeProblem() {
  return request(`/practice/next?user_id=${DEV_USER_ID}`);
}

export function submitAttempt({ problemId, selectedIndex, reasoning }) {
  return request("/attempts", {
    method: "POST",
    body: JSON.stringify({
      user_id: DEV_USER_ID,
      problem_id: problemId,
      selected_index: selectedIndex,
      reasoning,
    }),
  });
}

export function fetchProblemBoard(problemId) {
  return request(`/problems/${problemId}/board?user_id=${DEV_USER_ID}`);
}

export function fetchMyPosts() {
  return request(`/me/posts?user_id=${DEV_USER_ID}`);
}

export function fetchMyStats() {
  return request(`/stats/me?user_id=${DEV_USER_ID}`);
}

export function fetchMySettings() {
  return request(`/settings/me?user_id=${DEV_USER_ID}`);
}

export function updateMySettings(payload) {
  return request("/settings/me", {
    method: "PUT",
    body: JSON.stringify({
      user_id: DEV_USER_ID,
      ...payload,
    }),
  });
}
