from cryptography.fernet import Fernet, InvalidToken

from backend.app.core.config import get_settings


class SecretEncryptionConfigurationError(Exception):
    pass


class SecretDecryptionError(Exception):
    pass


def encrypt_secret(value: str) -> str:
    return get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str:
    try:
        return get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise SecretDecryptionError("저장된 Notion 토큰을 복호화할 수 없습니다.") from exc


def get_fernet() -> Fernet:
    key = get_settings().notion_token_encryption_key
    if not key:
        raise SecretEncryptionConfigurationError("NOTION_TOKEN_ENCRYPTION_KEY 설정이 필요합니다.")
    try:
        return Fernet(key.encode("utf-8"))
    except ValueError as exc:
        raise SecretEncryptionConfigurationError("NOTION_TOKEN_ENCRYPTION_KEY 형식이 올바르지 않습니다.") from exc
