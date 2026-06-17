import unittest
from datetime import date
from types import SimpleNamespace

from backend.app.models.enums import ProblemArea, ProblemType
from backend.app.services.me import get_week_start, summarize_weekly_attempts


def attempt(
    *,
    area: ProblemArea,
    problem_type: ProblemType | None,
    is_correct: bool,
    is_daily: bool,
    solve_duration_sec: int | None = None,
):
    return SimpleNamespace(
        problem=SimpleNamespace(
            area=area,
            problem_type=problem_type,
        ),
        is_correct=is_correct,
        is_daily=is_daily,
        solve_duration_sec=solve_duration_sec,
    )


class WeeklySummaryTest(unittest.TestCase):
    def test_week_starts_on_monday(self):
        self.assertEqual(get_week_start(date(2026, 6, 18)), date(2026, 6, 15))

    def test_empty_summary(self):
        summary = summarize_weekly_attempts([], date(2026, 6, 18))

        self.assertEqual(summary.total_attempts, 0)
        self.assertEqual(summary.correct_attempts, 0)
        self.assertEqual(summary.accuracy_rate, 0)
        self.assertIsNone(summary.weak_type)
        self.assertIn("아직 없어요", summary.summary_text)

    def test_summarizes_weekly_attempts(self):
        summary = summarize_weekly_attempts(
            [
                attempt(
                    area=ProblemArea.reading_comprehension,
                    problem_type=ProblemType.inference,
                    is_correct=False,
                    is_daily=True,
                    solve_duration_sec=120,
                ),
                attempt(
                    area=ProblemArea.reasoning_argumentation,
                    problem_type=ProblemType.conditional_reasoning,
                    is_correct=True,
                    is_daily=False,
                    solve_duration_sec=180,
                ),
            ],
            date(2026, 6, 18),
        )

        self.assertEqual(summary.total_attempts, 2)
        self.assertEqual(summary.correct_attempts, 1)
        self.assertEqual(summary.accuracy_rate, 50)
        self.assertEqual(summary.daily_attempts, 1)
        self.assertEqual(summary.practice_attempts, 1)
        self.assertEqual(summary.average_solve_duration_sec, 150)
        self.assertEqual(summary.weak_type, ProblemType.inference.value)
        self.assertIn("추론", summary.summary_text)


if __name__ == "__main__":
    unittest.main()
