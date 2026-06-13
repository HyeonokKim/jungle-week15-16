from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.core.security import create_access_token
from backend.app.models.user import User
from backend.app.services.auth import (
    build_google_login_url,
    exchange_google_code,
    fetch_google_userinfo,
    get_or_create_google_user,
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


@router.get("/me")
def read_auth_me(user: User = Depends(get_current_user)) -> dict[str, str | int]:
    return {
        "id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "auth_provider": user.auth_provider,
    }
