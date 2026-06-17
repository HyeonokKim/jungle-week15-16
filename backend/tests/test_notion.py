import unittest
from datetime import date

from backend.app.services.me import WeeklySummary
from backend.app.services.notion import (
    NotionConfigurationError,
    NotionSaveResult,
    build_weekly_summary_page_payload,
    format_duration,
    save_weekly_summary_to_notion_once,
    save_weekly_summary_to_notion,
)


def weekly_summary() -> WeeklySummary:
    return WeeklySummary(
        week_start=date(2026, 6, 15),
        week_end=date(2026, 6, 16),
        total_attempts=3,
        correct_attempts=2,
        accuracy_rate=67,
        daily_attempts=2,
        practice_attempts=1,
        average_solve_duration_sec=125,
        weak_type="inference",
        area_accuracy=[],
        summary_text="이번 주에는 총 3문제를 풀고 2문제를 맞혔어요.",
    )


class SettingsStub:
    notion_token = None
    notion_version = "2026-03-11"
    notion_page_id = "abc-def"


class UserStub:
    id = 1


class ExecuteResultStub:
    def __init__(self, existing_export):
        self.existing_export = existing_export

    def scalar_one_or_none(self):
        return self.existing_export


class DBStub:
    def __init__(self, existing_export=None):
        self.existing_export = existing_export
        self.added = None
        self.committed = False

    def execute(self, _query):
        return ExecuteResultStub(self.existing_export)

    def add(self, item):
        self.added = item

    def commit(self):
        self.committed = True

    def refresh(self, _item):
        pass


class ExistingExportStub:
    external_page_id = "existing-page"
    external_url = "https://notion.so/existing"


class NotionTest(unittest.TestCase):
    def test_builds_weekly_summary_page_payload(self):
        payload = build_weekly_summary_page_payload(weekly_summary(), "abc-def")

        self.assertEqual(payload["parent"], {"page_id": "abcdef"})
        self.assertEqual(
            payload["properties"]["title"]["title"][0]["text"]["content"],
            "2026-06-15 - 2026-06-16 LEET 이번 주 요약",
        )
        self.assertIn("이번 주에는 총 3문제를", payload["children"][1]["paragraph"]["rich_text"][0]["text"]["content"])

    def test_save_requires_token(self):
        with self.assertRaises(NotionConfigurationError):
            save_weekly_summary_to_notion(weekly_summary(), SettingsStub())

    def test_does_not_save_again_when_export_exists(self):
        db = DBStub(existing_export=ExistingExportStub())

        result = save_weekly_summary_to_notion_once(
            db,
            UserStub(),
            weekly_summary(),
            notion_saver=lambda _summary, _settings: self.fail("Notion saver should not be called"),
        )

        self.assertTrue(result.already_saved)
        self.assertEqual(result.page_id, "existing-page")
        self.assertFalse(db.committed)

    def test_records_export_after_notion_save(self):
        db = DBStub()

        result = save_weekly_summary_to_notion_once(
            db,
            UserStub(),
            weekly_summary(),
            notion_saver=lambda _summary, _settings: NotionSaveResult(
                page_id="new-page",
                url="https://notion.so/new",
            ),
        )

        self.assertFalse(result.already_saved)
        self.assertEqual(result.page_id, "new-page")
        self.assertEqual(db.added.external_page_id, "new-page")
        self.assertTrue(db.committed)

    def test_formats_duration(self):
        self.assertEqual(format_duration(None), "없음")
        self.assertEqual(format_duration(45), "45초")
        self.assertEqual(format_duration(120), "2분")
        self.assertEqual(format_duration(125), "2분 5초")


if __name__ == "__main__":
    unittest.main()
