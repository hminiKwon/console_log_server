from __future__ import annotations

from datetime import datetime, timezone
from typing import Tuple
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from console_log_server.api.schemas import LoginRequest, RegisterRequest
from console_log_server.models import User
from console_log_server.repositories import RefreshTokenRepository, UserRepository
from console_log_server.utils.security import hash_password, verify_password
from console_log_server.utils.token import (
    create_access_token,
    create_refresh_token,
    decode_token,
)


class AuthService:
    """회원 가입 및 인증 비즈니스 로직."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = UserRepository(session)
        self.refresh_repository = RefreshTokenRepository(session)

    def register(self, payload: RegisterRequest) -> User:
        if self.repository.get_by_username(payload.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 사용자명입니다.",
            )

        if self.repository.get_by_email(payload.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 이메일입니다.",
            )

        user = self.repository.create(
            username=payload.username,
            email=payload.email,
            password_hash=hash_password(payload.password),
        )

        return user

    def authenticate(self, payload: LoginRequest) -> User:
        user = self.repository.get_by_email(payload.email)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="잘못된 인증 정보입니다.",
            )

        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="잘못된 인증 정보입니다.",
            )

        return user

    def issue_tokens(
        self,
        user: User,
        *,
        replace_existing: bool = False,
        session_id: str | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> Tuple[str, str, str]:
        session_id = session_id or str(uuid4())

        if replace_existing:
            self.refresh_repository.revoke_all_for_session(user.id, session_id)

        additional_claims = {"sid": session_id}

        access_token = create_access_token(str(user.id), additional_claims=additional_claims)
        refresh_token = create_refresh_token(str(user.id), additional_claims=additional_claims)

        payload = decode_token(refresh_token, expected_type="refresh")
        expires_at = self._parse_expiration(payload.get("exp"))

        self.refresh_repository.create(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
            session_id=session_id,
            jti=payload.get("jti"),
            user_agent=user_agent,
            ip_address=ip_address,
        )

        return access_token, refresh_token, session_id

    def validate_refresh_token(self, token: str, *, session_id: str | None = None) -> User:
        try:
            payload = decode_token(token, expected_type="refresh")
        except Exception as exc:  # broad except to map to HTTP error
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="리프레시 토큰이 유효하지 않습니다.",
            ) from exc

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="리프레시 토큰이 유효하지 않습니다.",
            )

        token_record = self.refresh_repository.get_by_token(token)

        if token_record is None or token_record.is_expired or token_record.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="리프레시 토큰이 유효하지 않습니다.",
            )

        if session_id and token_record.session_id != session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="세션이 일치하지 않습니다.",
            )

        if str(token_record.user_id) != str(user_id):
            self.refresh_repository.delete(token_record)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="리프레시 토큰이 유효하지 않습니다.",
            )

        user = self.session.get(User, token_record.user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다.",
            )

        self.refresh_repository.mark_revoked(token_record)

        return user

    def revoke_session_tokens(self, user: User, session_id: str | None) -> None:
        if session_id is None:
            return
        self.refresh_repository.revoke_all_for_session(user.id, session_id)

    def _parse_expiration(self, exp_value: object) -> datetime:
        if isinstance(exp_value, (int, float)):
            return datetime.fromtimestamp(exp_value, tz=timezone.utc)
        if isinstance(exp_value, datetime):
            if exp_value.tzinfo is None:
                return exp_value.replace(tzinfo=timezone.utc)
            return exp_value.astimezone(timezone.utc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="토큰 만료 시간을 계산할 수 없습니다.",
        )
