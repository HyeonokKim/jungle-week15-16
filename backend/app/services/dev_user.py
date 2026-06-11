from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.user_setting import UserSetting


def get_or_create_dev_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user:
        return user

    user = User(
        id=user_id,
        email=f"dev{user_id}@haripool.local",
        nickname=f"dev-user-{user_id}",
        auth_provider="dev",
        provider_id=str(user_id),
    )
    db.add(user)
    db.flush()
    db.add(UserSetting(user_id=user.id))
    db.flush()
    return user
