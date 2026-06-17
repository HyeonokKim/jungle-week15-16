const DAY_COUNT = 84;
const cells = Array.from({ length: DAY_COUNT }, (_, index) => {
  const daysAgo = DAY_COUNT - index - 1;
  const date = new Date();
  date.setHours(0, 0, 0, 0);
  date.setDate(date.getDate() - daysAgo);
  return {
    date,
    daysAgo,
  };
});

function formatDate(date) {
  return date.toLocaleDateString("ko-KR", {
    month: "2-digit",
    day: "2-digit",
  });
}

export default function ActivityGrid({ currentStreak = 0, completedToday = false }) {
  return (
    <div className="grid max-w-[250px] grid-cols-[repeat(14,minmax(0,1fr))] gap-1.5" aria-label="최근 12주 풀이 잔디">
      {cells.map(({ date }, index) => {
        const solvedCount = currentStreak + (completedToday && currentStreak === 0 ? 1 : 0);
        const solved = index < solvedCount;
        return (
          <div
            key={date.toISOString()}
            title={`${formatDate(date)} ${solved ? "풀이 완료" : "미완료"}`}
            className={`h-3 w-3 rounded-[3px] ${solved ? "bg-pepper" : "bg-ash"}`}
          />
        );
      })}
    </div>
  );
}
