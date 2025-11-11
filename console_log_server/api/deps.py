from __future__ import annotations

from typing import Generator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from console_log_server.core import Settings, get_settings
from console_log_server.core.database import get_session as _get_db_session
from console_log_server.models import User
from console_log_server.utils import decode_token


def get_app_settings() -> Settings:
    """FastAPI 의존성 주입용 설정 객체 반환."""

    return get_settings()


def get_db_session() -> Generator[Session, None, None]:
    """요청 단위 DB 세션을 제공."""

    yield from _get_db_session()


def get_current_user(
    session: Session = Depends(get_db_session),
    authorization: str | None = Header(default=None),
) -> User:
    """Authorization 헤더의 Access Token을 검증하고 사용자 정보를 반환."""

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다.",
        )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="잘못된 인증 헤더 형식입니다.",
        )

    try:
        payload = decode_token(token, expected_type="access")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="액세스 토큰이 유효하지 않습니다.",
        ) from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="액세스 토큰이 유효하지 않습니다.",
        )

    user = session.get(User, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
        )

    return user
