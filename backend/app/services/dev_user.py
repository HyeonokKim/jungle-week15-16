from sqlalchemy.orm import Session
from sqlalchemy import text

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
    sync_user_id_sequence(db)
    db.flush()
    return user


def sync_user_id_sequence(db: Session) -> None:
    db.execute(
        text(
            """
            SELECT setval(
                pg_get_serial_sequence('users', 'id'),
                GREATEST((SELECT COALESCE(MAX(id), 1) FROM users), 1)
            )
            """
        )
    )
