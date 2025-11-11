from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from console_log_server.models import User


class UserRepository:
    """사용자 데이터 접근 계층."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        username: str,
        email: str,
        password_hash: str,
    ) -> User:
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
        )

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return user

    def get_by_username(self, username: str) -> Optional[User]:
        return (
            self.session.query(User)
            .filter(User.username == username)
            .one_or_none()
        )

    def get_by_email(self, email: str) -> Optional[User]:
        return (
            self.session.query(User)
            .filter(User.email == email)
            .one_or_none()
        )
