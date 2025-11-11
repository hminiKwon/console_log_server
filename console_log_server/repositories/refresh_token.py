from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from console_log_server.models import RefreshToken
from console_log_server.utils.token import hash_token


class RefreshTokenRepository:
    """리프레시 토큰을 관리하는 저장소."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        user_id: int,
        token: str,
        expires_at: datetime,
        session_id: str,
        jti: str,
        user_agent: str | None,
        ip_address: str | None,
    ) -> RefreshToken:
        hashed = hash_token(token)

        refresh_token = RefreshToken(
            user_id=user_id,
            session_id=session_id,
            token_hash=hashed,
            jti=jti,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
        )
        self.session.add(refresh_token)
        self.session.commit()
        self.session.refresh(refresh_token)
        return refresh_token

    def get_by_token(self, token: str) -> Optional[RefreshToken]:
        hashed = hash_token(token)
        return (
            self.session.query(RefreshToken)
            .filter(RefreshToken.token_hash == hashed)
            .one_or_none()
        )

    def delete(self, token: RefreshToken) -> None:
        self.session.delete(token)
        self.session.commit()

    def delete_all_for_user(self, user_id: int) -> None:
        (
            self.session.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id)
            .delete(synchronize_session=False)
        )
        self.session.commit()

    def mark_revoked(self, token: RefreshToken) -> None:
        token.revoked = True
        self.session.add(token)
        self.session.commit()

    def revoke_all_for_session(self, user_id: int, session_id: str) -> None:
        (
            self.session.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.session_id == session_id,
                RefreshToken.revoked.is_(False),
            )
            .update({"revoked": True}, synchronize_session=False)
        )
        self.session.commit()
