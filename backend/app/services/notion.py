from __future__ import annotations

import json
import ssl
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi

from backend.app.core.config import Settings, get_settings
from backend.app.services.me import PROBLEM_TYPE_LABELS, WeeklySummary


NOTION_PAGES_URL = "https://api.notion.com/v1/pages"


class NotionConfigurationError(Exception):
    pass


class NotionAPIError(Exception):
    pass


@dataclass(frozen=True)
class NotionSaveResult:
    page_id: str
    url: str | None


def save_weekly_summary_to_notion(
    summary: WeeklySummary,
    settings: Settings | None = None,
) -> NotionSaveResult:
    app_settings = settings or get_settings()
    if not app_settings.notion_token:
        raise NotionConfigurationError("NOTION_TOKEN 설정이 필요합니다.")
    if not app_settings.notion_page_id:
        raise NotionConfigurationError("NOTION_PAGE_ID 설정이 필요합니다.")

    payload = build_weekly_summary_page_payload(summary, app_settings.notion_page_id)
    response = post_notion_page(payload, app_settings.notion_token, app_settings.notion_version)
    page_id = response.get("id")
    if not isinstance(page_id, str):
        raise NotionAPIError("Notion 저장 응답에 페이지 ID가 없습니다.")

    page_url = response.get("url")
    return NotionSaveResult(page_id=page_id, url=page_url if isinstance(page_url, str) else None)


def build_weekly_summary_page_payload(summary: WeeklySummary, parent_page_id: str) -> dict[str, Any]:
    title = f"{summary.week_start.isoformat()} - {summary.week_end.isoformat()} LEET 이번 주 요약"
    return {
        "parent": {"page_id": normalize_notion_id(parent_page_id)},
        "properties": {
            "title": {
                "title": rich_text(title),
            },
        },
        "children": build_weekly_summary_blocks(summary),
    }


def build_weekly_summary_blocks(summary: WeeklySummary) -> list[dict[str, Any]]:
    weak_type_label = PROBLEM_TYPE_LABELS.get(summary.weak_type, summary.weak_type) if summary.weak_type else "없음"
    return [
        heading_2("학습 요약"),
        paragraph(summary.summary_text),
        heading_2("주간 지표"),
        bullet(f"기간: {summary.week_start.isoformat()} - {summary.week_end.isoformat()}"),
        bullet(f"풀이: 총 {summary.total_attempts}문제"),
        bullet(f"정답: {summary.correct_attempts}문제"),
        bullet(f"정답률: {summary.accuracy_rate}%"),
        bullet(f"데일리: {summary.daily_attempts}문제"),
        bullet(f"추가 연습: {summary.practice_attempts}문제"),
        bullet(f"평균 풀이 시간: {format_duration(summary.average_solve_duration_sec)}"),
        bullet(f"취약 유형: {weak_type_label}"),
    ]


def post_notion_page(payload: dict[str, Any], notion_token: str, notion_version: str) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        NOTION_PAGES_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": notion_version,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(request, timeout=10, context=context) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise NotionAPIError(
            f"Notion 저장 요청에 실패했습니다. 대상 페이지 공유와 권한을 확인해 주세요. (status: {exc.code})"
        ) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise NotionAPIError("Notion 저장 요청에 실패했습니다. 잠시 후 다시 시도해 주세요.") from exc

    if not isinstance(response_payload, dict):
        raise NotionAPIError("Notion 저장 응답 형식이 올바르지 않습니다.")
    return response_payload


def normalize_notion_id(value: str) -> str:
    return value.strip().replace("-", "")


def rich_text(content: str) -> list[dict[str, Any]]:
    return [{"type": "text", "text": {"content": content}}]


def heading_2(content: str) -> dict[str, Any]:
    return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": rich_text(content)}}


def paragraph(content: str) -> dict[str, Any]:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": rich_text(content)}}


def bullet(content: str) -> dict[str, Any]:
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rich_text(content)}}


def format_duration(seconds: int | None) -> str:
    if seconds is None:
        return "없음"
    minutes, remainder = divmod(seconds, 60)
    if minutes == 0:
        return f"{remainder}초"
    if remainder == 0:
        return f"{minutes}분"
    return f"{minutes}분 {remainder}초"
