from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.services.dev_user import get_or_create_dev_user


DEV_USER_ID = 1


def get_current_user(db: Session = Depends(get_db)) -> User:
    return get_or_create_dev_user(db, DEV_USER_ID)
