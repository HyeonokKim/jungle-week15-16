from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select

from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.services.me import get_weekly_attempts, summarize_weekly_attempts
from backend.app.services.notion import (
    NotionAPIError,
    NotionConfigurationError,
    save_weekly_summary_to_notion_once,
)


def parse_target_date(target_date: str | None) -> date:
    if not target_date:
        return date.today()
    try:
        return date.fromisoformat(target_date)
    except ValueError as exc:
        raise ValueError("target_date는 YYYY-MM-DD 형식이어야 합니다.") from exc


def save_weekly_summary_to_notion_tool(
    user_id: int = 1,
    target_date: str | None = None,
) -> dict[str, Any]:
    """Save a user's weekly LEET study summary to Notion.

    Args:
        user_id: Haripool user ID. In development mode, user 1 is the default test user.
        target_date: Optional date in YYYY-MM-DD format. The week containing this date is exported.
    """
    try:
        today = parse_target_date(target_date)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            return {"ok": False, "error": "사용자를 찾을 수 없습니다."}

        weekly_summary = summarize_weekly_attempts(get_weekly_attempts(db, user, today), today)
        result = save_weekly_summary_to_notion_once(db, user, weekly_summary)
        return {
            "ok": True,
            "message": "이미 저장된 이번 주 요약이에요." if result.already_saved else "이번 주 요약을 Notion에 저장했어요.",
            "already_saved": result.already_saved,
            "page_id": result.page_id,
            "url": result.url,
            "week_start": weekly_summary.week_start.isoformat(),
            "week_end": weekly_summary.week_end.isoformat(),
            "summary_text": weekly_summary.summary_text,
        }
    except (NotionConfigurationError, NotionAPIError) as exc:
        return {"ok": False, "error": str(exc)}
    finally:
        db.close()


def create_mcp_server():
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("haripool-notion")
    mcp.tool()(save_weekly_summary_to_notion_tool)
    return mcp


def main() -> None:
    create_mcp_server().run(transport="stdio")


if __name__ == "__main__":
    main()
