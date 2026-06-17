import unittest

from backend.app.services.notion_oauth import (
    NotionOAuthError,
    NotionOAuthToken,
    build_notion_oauth_login_url,
    parse_notion_oauth_token,
)


class UserStub:
    id = 7


class SettingsStub:
    notion_oauth_client_id = "client-id"
    notion_oauth_client_secret = "client-secret"
    notion_oauth_redirect_uri = "http://127.0.0.1:8000/auth/notion/callback"
    notion_version = "2026-03-11"


class NotionOAuthTest(unittest.TestCase):
    def test_builds_oauth_login_url(self):
        url = build_notion_oauth_login_url(UserStub(), SettingsStub())

        self.assertTrue(url.startswith("https://api.notion.com/v1/oauth/authorize?"))
        self.assertIn("client_id=client-id", url)
        self.assertIn("response_type=code", url)
        self.assertIn("owner=user", url)
        self.assertIn("state=", url)

    def test_parses_oauth_token(self):
        token = parse_notion_oauth_token(
            {
                "access_token": "access",
                "refresh_token": "refresh",
                "bot_id": "bot",
                "workspace_id": "workspace",
                "workspace_name": "My Notion",
                "workspace_icon": None,
                "duplicated_template_id": "template-page",
            }
        )

        self.assertEqual(
            token,
            NotionOAuthToken(
                access_token="access",
                refresh_token="refresh",
                bot_id="bot",
                workspace_id="workspace",
                workspace_name="My Notion",
                workspace_icon=None,
                duplicated_template_id="template-page",
            ),
        )

    def test_token_requires_required_fields(self):
        with self.assertRaises(NotionOAuthError):
            parse_notion_oauth_token({})


if __name__ == "__main__":
    unittest.main()
