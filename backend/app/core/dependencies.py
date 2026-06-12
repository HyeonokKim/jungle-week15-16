from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.config import get_settings
from backend.app.core.security import decode_access_token, raise_credentials_error
from backend.app.models.user import User
from backend.app.services.dev_user import get_or_create_dev_user


DEV_USER_ID = 1
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if credentials:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.isdigit():
            raise_credentials_error()
        user = db.get(User, int(subject))
        if not user:
            raise_credentials_error()
        return user

    if get_settings().auth_dev_mode:
        return get_or_create_dev_user(db, DEV_USER_ID)

    raise_credentials_error()
