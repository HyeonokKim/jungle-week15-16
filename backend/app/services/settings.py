from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.user_setting import UserSetting
from backend.app.schemas.settings import UserSettingsUpdate


def get_or_create_user_settings(db: Session, user: User) -> UserSetting:
    setting = db.execute(select(UserSetting).where(UserSetting.user_id == user.id)).scalar_one_or_none()
    if setting:
        return setting

    setting = UserSetting(user_id=user.id)
    db.add(setting)
    db.flush()
    return setting


def update_user_settings(db: Session, setting: UserSetting, payload: UserSettingsUpdate) -> UserSetting:
    update_data = payload.model_dump(exclude={"user_id"}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(setting, field, value)

    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting
