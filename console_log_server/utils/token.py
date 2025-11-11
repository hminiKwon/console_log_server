from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4

import jwt

from console_log_server.core import get_settings


def _get_expiry(delta: timedelta) -> datetime:
    return datetime.now(tz=timezone.utc) + delta


def create_access_token(subject: str, *, additional_claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.jwt_access_token_expires_minutes)
    claims = dict(additional_claims or {})
    claims.setdefault("jti", uuid4().hex)
    return _encode_token(
        subject=subject,
        expires_at=_get_expiry(expires_delta),
        token_type="access",
        additional_claims=claims,
    )


def create_refresh_token(subject: str, *, additional_claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expires_delta = timedelta(days=settings.jwt_refresh_token_expires_days)
    claims = dict(additional_claims or {})
    claims.setdefault("jti", uuid4().hex)
    return _encode_token(
        subject=subject,
        expires_at=_get_expiry(expires_delta),
        token_type="refresh",
        additional_claims=claims,
    )


def decode_token(token: str, *, expected_type: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    if expected_type is not None and payload.get("typ") != expected_type:
        raise jwt.InvalidTokenError("Invalid token type")

    return payload


def hash_token(token: str) -> str:
    """리프레시 토큰을 안전하게 저장하기 위한 해시."""

    return sha256(token.encode("utf-8")).hexdigest()


def _encode_token(
    *,
    subject: str,
    expires_at: datetime,
    token_type: str,
    additional_claims: dict[str, Any] | None,
) -> str:
    settings = get_settings()

    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expires_at,
        "typ": token_type,
        "iat": datetime.now(tz=timezone.utc),
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
