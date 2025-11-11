from __future__ import annotations

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    """평문 비밀번호를 해시."""

    return _pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """입력 비밀번호와 저장된 해시를 비교."""

    return _pwd_context.verify(password, hashed_password)
