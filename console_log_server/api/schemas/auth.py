from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """회원 가입 요청 스키마."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    session_id: str | None = Field(default=None)
    user_agent: str | None = Field(default=None)
    ip: str | None = Field(default=None)


class LoginRequest(BaseModel):
    """로그인 요청 스키마."""

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    session_id: str | None = Field(default=None)
    user_agent: str | None = Field(default=None)
    ip: str | None = Field(default=None)


class UserResponse(BaseModel):
    """사용자 정보 응답 스키마."""

    id: int
    username: str
    email: EmailStr


class TokenResponse(BaseModel):
    """액세스 토큰 응답."""

    access_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """로그인/회원가입 응답 스키마."""

    user: UserResponse
    tokens: TokenResponse
