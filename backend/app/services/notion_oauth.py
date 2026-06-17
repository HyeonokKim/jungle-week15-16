from __future__ import annotations

import base64
import json
import ssl
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.core.security import create_access_token, decode_access_token
from backend.app.models.user import User
from backend.app.models.user_notion_connection import UserNotionConnection
from backend.app.services.crypto import encrypt_secret


NOTION_OAUTH_AUTHORIZE_URL = "https://api.notion.com/v1/oauth/authorize"
NOTION_OAUTH_TOKEN_URL = "https://api.notion.com/v1/oauth/token"
NOTION_OAUTH_STATE_PURPOSE = "notion_oauth"


class NotionOAuthConfigurationError(Exception):
    pass


class NotionOAuthError(Exception):
    pass


@dataclass(frozen=True)
class NotionOAuthToken:
    access_token: str
    refresh_token: str | None
    bot_id: str
    workspace_id: str
    workspace_name: str | None
    workspace_icon: str | None
    duplicated_template_id: str | None


def build_notion_oauth_login_url(user: User, settings: Settings | None = None) -> str:
    app_settings = settings or get_settings()
    ensure_oauth_configured(app_settings)
    state = create_notion_oauth_state(user)
    query = urlencode(
        {
            "owner": "user",
            "client_id": app_settings.notion_oauth_client_id,
            "redirect_uri": app_settings.notion_oauth_redirect_uri,
            "response_type": "code",
            "state": state,
        }
    )
    return f"{NOTION_OAUTH_AUTHORIZE_URL}?{query}"


def create_notion_oauth_state(user: User) -> str:
    return create_access_token(subject=str(user.id), extra_claims={"purpose": NOTION_OAUTH_STATE_PURPOSE})


def read_user_id_from_notion_oauth_state(state: str) -> int:
    payload = decode_access_token(state)
    if payload.get("purpose") != NOTION_OAUTH_STATE_PURPOSE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Notion OAuth state가 올바르지 않습니다.")
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.isdigit():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Notion OAuth state에 사용자 정보가 없습니다.")
    return int(subject)


def exchange_notion_code(code: str, settings: Settings | None = None) -> NotionOAuthToken:
    app_settings = settings or get_settings()
    ensure_oauth_configured(app_settings)

    payload = notion_oauth_token_request(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": app_settings.notion_oauth_redirect_uri,
        },
        app_settings,
    )
    return parse_notion_oauth_token(payload)


def upsert_user_notion_connection(db: Session, user: User, token: NotionOAuthToken) -> UserNotionConnection:
    connection = db.execute(
        select(UserNotionConnection).where(UserNotionConnection.user_id == user.id)
    ).scalar_one_or_none()
    if connection is None:
        connection = UserNotionConnection(user_id=user.id)
        db.add(connection)

    connection.workspace_id = token.workspace_id
    connection.workspace_name = token.workspace_name
    connection.workspace_icon = token.workspace_icon
    connection.bot_id = token.bot_id
    connection.duplicated_template_id = token.duplicated_template_id
    connection.default_page_id = token.duplicated_template_id
    connection.access_token_encrypted = encrypt_secret(token.access_token)
    connection.refresh_token_encrypted = encrypt_secret(token.refresh_token) if token.refresh_token else None

    db.commit()
    db.refresh(connection)
    return connection


def get_user_notion_connection(db: Session, user: User) -> UserNotionConnection | None:
    return db.execute(
        select(UserNotionConnection).where(UserNotionConnection.user_id == user.id)
    ).scalar_one_or_none()


def notion_oauth_token_request(body: dict[str, Any], settings: Settings) -> dict[str, Any]:
    credential = f"{settings.notion_oauth_client_id}:{settings.notion_oauth_client_secret}"
    encoded_credential = base64.b64encode(credential.encode("utf-8")).decode("ascii")
    request = Request(
        NOTION_OAUTH_TOKEN_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Authorization": f"Basic {encoded_credential}",
            "Content-Type": "application/json",
            "Notion-Version": settings.notion_version,
        },
        method="POST",
    )

    try:
        context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(request, timeout=10, context=context) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise NotionOAuthError(f"Notion OAuth 토큰 교환에 실패했습니다. (status: {exc.code})") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise NotionOAuthError("Notion OAuth 토큰 교환에 실패했습니다.") from exc

    if not isinstance(payload, dict):
        raise NotionOAuthError("Notion OAuth 응답 형식이 올바르지 않습니다.")
    return payload


def parse_notion_oauth_token(payload: dict[str, Any]) -> NotionOAuthToken:
    access_token = payload.get("access_token")
    bot_id = payload.get("bot_id")
    workspace_id = payload.get("workspace_id")
    if not isinstance(access_token, str) or not isinstance(bot_id, str) or not isinstance(workspace_id, str):
        raise NotionOAuthError("Notion OAuth 응답에 필수 토큰 정보가 없습니다.")

    refresh_token = payload.get("refresh_token")
    workspace_name = payload.get("workspace_name")
    workspace_icon = payload.get("workspace_icon")
    duplicated_template_id = payload.get("duplicated_template_id")
    return NotionOAuthToken(
        access_token=access_token,
        refresh_token=refresh_token if isinstance(refresh_token, str) else None,
        bot_id=bot_id,
        workspace_id=workspace_id,
        workspace_name=workspace_name if isinstance(workspace_name, str) else None,
        workspace_icon=workspace_icon if isinstance(workspace_icon, str) else None,
        duplicated_template_id=duplicated_template_id if isinstance(duplicated_template_id, str) else None,
    )


def ensure_oauth_configured(settings: Settings) -> None:
    if not settings.notion_oauth_client_id or not settings.notion_oauth_client_secret:
        raise NotionOAuthConfigurationError("Notion OAuth Client ID/Secret 설정이 필요합니다.")
