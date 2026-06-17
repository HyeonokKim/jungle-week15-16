import unittest
from datetime import date

from backend.app.mcp.notion_weekly_summary import parse_target_date, save_weekly_summary_to_notion_tool


class MCPNotionTest(unittest.TestCase):
    def test_parse_target_date(self):
        self.assertEqual(parse_target_date("2026-06-16"), date(2026, 6, 16))

    def test_tool_rejects_invalid_target_date(self):
        result = save_weekly_summary_to_notion_tool(target_date="2026/06/16")

        self.assertFalse(result["ok"])
        self.assertIn("YYYY-MM-DD", result["error"])


if __name__ == "__main__":
    unittest.main()
