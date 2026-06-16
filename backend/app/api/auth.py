from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.core.security import create_access_token
from backend.app.models.user import User
from backend.app.services.crypto import SecretEncryptionConfigurationError
from backend.app.services.auth import (
    build_google_login_url,
    exchange_google_code,
    fetch_google_userinfo,
    get_or_create_google_user,
)
from backend.app.services.notion_oauth import (
    NotionOAuthConfigurationError,
    NotionOAuthError,
    build_notion_oauth_login_url,
    exchange_notion_code,
    read_user_id_from_notion_oauth_state,
    upsert_user_notion_connection,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/login")
def google_login() -> RedirectResponse:
    return RedirectResponse(build_google_login_url())


@router.get("/google/login-url")
def google_login_url() -> dict[str, str]:
    return {"url": build_google_login_url()}


@router.get("/google/callback")
def google_callback(
    code: str = Query(min_length=1),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    token_response = exchange_google_code(code)
    access_token = token_response.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Google access token was not returned")

    userinfo = fetch_google_userinfo(access_token)
    user = get_or_create_google_user(db, userinfo)
    app_token = create_access_token(subject=str(user.id), extra_claims={"email": user.email})
    redirect_url = f"{get_settings().frontend_auth_redirect_url}?{urlencode({'token': app_token})}"
    return RedirectResponse(redirect_url)


@router.get("/notion/login-url")
def notion_login_url(user: User = Depends(get_current_user)) -> dict[str, str]:
    try:
        return {"url": build_notion_oauth_login_url(user)}
    except NotionOAuthConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/notion/callback")
def notion_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    app_settings = get_settings()
    if error:
        redirect_url = f"{app_settings.frontend_auth_redirect_url}?{urlencode({'notion': 'denied'})}"
        return RedirectResponse(redirect_url)
    if not code or not state:
        redirect_url = f"{app_settings.frontend_auth_redirect_url}?{urlencode({'notion': 'failed'})}"
        return RedirectResponse(redirect_url)

    try:
        user_id = read_user_id_from_notion_oauth_state(state)
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=400, detail="사용자를 찾을 수 없습니다.")
        token = exchange_notion_code(code)
        upsert_user_notion_connection(db, user, token)
    except (HTTPException, NotionOAuthConfigurationError, NotionOAuthError, SecretEncryptionConfigurationError):
        redirect_url = f"{app_settings.frontend_auth_redirect_url}?{urlencode({'notion': 'failed'})}"
        return RedirectResponse(redirect_url)

    redirect_url = f"{app_settings.frontend_auth_redirect_url}?{urlencode({'notion': 'connected'})}"
    return RedirectResponse(redirect_url)


@router.get("/me")
def read_auth_me(user: User = Depends(get_current_user)) -> dict[str, str | int]:
    return {
        "id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "auth_provider": user.auth_provider,
    }
