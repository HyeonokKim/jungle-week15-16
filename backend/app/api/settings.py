from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.models.user_setting import UserSetting
from backend.app.schemas.settings import UserSettingsResponse, UserSettingsUpdate
from backend.app.services.settings import get_or_create_user_settings, update_user_settings


router = APIRouter(tags=["settings"])


def serialize_user_settings(setting: UserSetting) -> UserSettingsResponse:
    return UserSettingsResponse(
        user_id=setting.user_id,
        problem_scope=setting.problem_scope,
        timer_limit_sec=setting.timer_limit_sec,
        review_interval_days=setting.review_interval_days,
        weak_type=setting.weak_type,
        created_at=setting.created_at.isoformat(),
        updated_at=setting.updated_at.isoformat(),
    )


@router.get("/settings/me", response_model=UserSettingsResponse)
def read_my_settings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserSettingsResponse:
    setting = get_or_create_user_settings(db, user)
    return serialize_user_settings(setting)


@router.put("/settings/me", response_model=UserSettingsResponse)
def update_my_settings(
    payload: UserSettingsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserSettingsResponse:
    setting = get_or_create_user_settings(db, user)
    return serialize_user_settings(update_user_settings(db, setting, payload))
