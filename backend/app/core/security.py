from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status

from backend.app.core.config import get_settings


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expire_minutes)).timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    header = {"alg": settings.jwt_algorithm, "typ": "JWT"}
    signing_input = f"{_base64url_json(header)}.{_base64url_json(payload)}"
    signature = _sign(signing_input, settings.jwt_secret_key, settings.jwt_algorithm)
    return f"{signing_input}.{signature}"


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        header_part, payload_part, signature_part = token.split(".")
    except ValueError:
        raise_credentials_error()

    signing_input = f"{header_part}.{payload_part}"
    expected_signature = _sign(signing_input, settings.jwt_secret_key, settings.jwt_algorithm)
    if not hmac.compare_digest(expected_signature, signature_part):
        raise_credentials_error()

    header = _base64url_decode_json(header_part)
    if header.get("alg") != settings.jwt_algorithm:
        raise_credentials_error()

    payload = _base64url_decode_json(payload_part)
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(datetime.now(UTC).timestamp()):
        raise_credentials_error()

    return payload


def raise_credentials_error() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _sign(signing_input: str, secret_key: str, algorithm: str) -> str:
    if algorithm != "HS256":
        raise ValueError("Only HS256 is supported")
    digest = hmac.new(secret_key.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
    return _base64url_encode(digest)


def _base64url_json(value: dict[str, Any]) -> str:
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _base64url_encode(raw)


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _base64url_decode_json(value: str) -> dict[str, Any]:
    padding = "=" * (-len(value) % 4)
    try:
        raw = base64.urlsafe_b64decode(f"{value}{padding}")
        decoded = json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        raise_credentials_error()
    if not isinstance(decoded, dict):
        raise_credentials_error()
    return decoded
