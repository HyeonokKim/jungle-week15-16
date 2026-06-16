import unittest
from types import SimpleNamespace

from backend.app.models.enums import ProblemArea, ProblemType
from backend.app.services.weakness import calculate_weak_type


def attempt(problem_type: ProblemType | None, is_correct: bool):
    return SimpleNamespace(
        problem=SimpleNamespace(
            area=ProblemArea.reading_comprehension,
            problem_type=problem_type,
        ),
        is_correct=is_correct,
    )


class WeakTypeCalculationTest(unittest.TestCase):
    def test_returns_none_without_attempts(self):
        self.assertIsNone(calculate_weak_type([]))

    def test_returns_none_when_every_tagged_attempt_is_correct(self):
        attempts = [
            attempt(ProblemType.main_claim, True),
            attempt(ProblemType.inference, True),
        ]

        self.assertIsNone(calculate_weak_type(attempts))

    def test_ignores_untagged_attempts(self):
        attempts = [
            attempt(None, False),
            attempt(None, True),
        ]

        self.assertIsNone(calculate_weak_type(attempts))

    def test_selects_problem_type_with_lower_accuracy(self):
        attempts = [
            attempt(ProblemType.main_claim, False),
            attempt(ProblemType.main_claim, True),
            attempt(ProblemType.inference, False),
            attempt(ProblemType.inference, True),
            attempt(ProblemType.inference, True),
        ]

        self.assertEqual(calculate_weak_type(attempts), ProblemType.main_claim.value)

    def test_tie_breaks_by_more_incorrect_attempts(self):
        attempts = [
            attempt(ProblemType.main_claim, False),
            attempt(ProblemType.main_claim, True),
            attempt(ProblemType.inference, False),
            attempt(ProblemType.inference, False),
            attempt(ProblemType.inference, True),
            attempt(ProblemType.inference, True),
        ]

        self.assertEqual(calculate_weak_type(attempts), ProblemType.inference.value)


if __name__ == "__main__":
    unittest.main()
