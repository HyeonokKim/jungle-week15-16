from __future__ import annotations

import json
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.models.user import User
from backend.app.models.user_setting import UserSetting
from backend.app.services.dev_user import sync_user_id_sequence


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def build_google_login_url() -> str:
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")

    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "select_account",
        }
    )
    return f"{GOOGLE_AUTH_URL}?{query}"


def exchange_google_code(code: str) -> dict[str, str]:
    settings = get_settings()
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")

    body = urlencode(
        {
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        }
    ).encode("utf-8")
    request = Request(
        GOOGLE_TOKEN_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    return _request_json(request)


def fetch_google_userinfo(access_token: str) -> dict[str, str]:
    request = Request(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
    return _request_json(request)


def get_or_create_google_user(db: Session, userinfo: dict[str, str]) -> User:
    provider_id = userinfo.get("sub")
    email = userinfo.get("email")
    if not provider_id or not email:
        raise HTTPException(status_code=400, detail="Google user info is missing required fields")

    user = db.execute(
        select(User).where(User.auth_provider == "google", User.provider_id == provider_id)
    ).scalar_one_or_none()
    if user:
        return user

    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user:
        user.auth_provider = "google"
        user.provider_id = provider_id
    else:
        sync_user_id_sequence(db)
        user = User(
            email=email,
            nickname=generate_unique_nickname(db, userinfo),
            auth_provider="google",
            provider_id=provider_id,
            password_hash=None,
        )
        db.add(user)
        db.flush()

    if not user.settings:
        db.add(UserSetting(user_id=user.id))

    db.commit()
    db.refresh(user)
    return user


def generate_unique_nickname(db: Session, userinfo: dict[str, str]) -> str:
    base = userinfo.get("name") or userinfo.get("email", "user").split("@")[0]
    base = "".join(char for char in base.strip().lower().replace(" ", "-") if char.isalnum() or char == "-")
    if not base:
        base = "user"
    base = base[:40]

    nickname = base
    suffix = 1
    while db.execute(select(User.id).where(User.nickname == nickname)).scalar_one_or_none():
        suffix += 1
        nickname = f"{base[:40 - len(str(suffix)) - 1]}-{suffix}"
    return nickname


def _request_json(request: Request) -> dict[str, str]:
    try:
        context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(request, timeout=10, context=context) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Google OAuth request failed") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Invalid Google OAuth response")
    return payload
