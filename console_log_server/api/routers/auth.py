from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from console_log_server.api.deps import get_app_settings, get_current_user, get_db_session
from console_log_server.api.schemas import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from console_log_server.core import Settings
from console_log_server.models import User
from console_log_server.services import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    summary="회원 가입",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: Request,
    response: Response,
    payload: RegisterRequest,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> AuthResponse:
    service = AuthService(session)
    user = service.register(payload)

    session_id = (
        payload.session_id
        or request.cookies.get(settings.jwt_session_cookie_name)
        or str(uuid4())
    )
    user_agent = payload.user_agent or request.headers.get("user-agent")
    ip_address = payload.ip or (request.client.host if request.client else None)

    access_token, refresh_token, session_id = service.issue_tokens(
        user,
        replace_existing=False,
        session_id=session_id,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    _set_refresh_cookie(response, refresh_token, settings)
    _set_session_cookie(response, session_id, settings)
    return AuthResponse(
        user=UserResponse(id=user.id, username=user.username, email=user.email),
        tokens=TokenResponse(access_token=access_token),
    )


@router.post(
    "/login",
    summary="로그인",
    response_model=AuthResponse,
)
def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> AuthResponse:
    service = AuthService(session)
    user = service.authenticate(payload)
    session_id = (
        payload.session_id
        or request.cookies.get(settings.jwt_session_cookie_name)
        or str(uuid4())
    )
    user_agent = payload.user_agent or request.headers.get("user-agent")
    ip_address = payload.ip or (request.client.host if request.client else None)

    access_token, refresh_token, session_id = service.issue_tokens(
        user,
        replace_existing=True,
        session_id=session_id,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    _set_refresh_cookie(response, refresh_token, settings)
    _set_session_cookie(response, session_id, settings)
    return AuthResponse(
        user=UserResponse(id=user.id, username=user.username, email=user.email),
        tokens=TokenResponse(access_token=access_token),
    )


@router.post(
    "/refresh",
    summary="토큰 갱신",
    response_model=TokenResponse,
)
def refresh_token(
    response: Response,
    request: Request,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> TokenResponse:
    raw_refresh_token = request.cookies.get(settings.jwt_refresh_cookie_name)

    if raw_refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="리프레시 토큰이 필요합니다.",
        )

    session_id = request.cookies.get(settings.jwt_session_cookie_name)

    service = AuthService(session)
    user = service.validate_refresh_token(raw_refresh_token, session_id=session_id)
    access_token, new_refresh_token, session_id = service.issue_tokens(
        user,
        session_id=session_id,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    _set_refresh_cookie(response, new_refresh_token, settings)
    _set_session_cookie(response, session_id, settings)
    return TokenResponse(access_token=access_token)


@router.post(
    "/logout",
    summary="로그아웃",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    request: Request,
    response: Response,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    current_user: User = Depends(get_current_user),
) -> None:
    session_id = request.cookies.get(settings.jwt_session_cookie_name)
    service = AuthService(session)
    service.revoke_session_tokens(current_user, session_id)
    _clear_auth_cookies(response, settings)


def _set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    max_age = settings.jwt_refresh_token_expires_days * 24 * 60 * 60
    response.set_cookie(
        key=settings.jwt_refresh_cookie_name,
        value=token,
        httponly=True,
        secure=settings.jwt_refresh_cookie_secure,
        samesite=settings.jwt_refresh_cookie_samesite,
        max_age=max_age,
        expires=max_age,
        path="/",
    )


def _set_session_cookie(response: Response, session_id: str | None, settings: Settings) -> None:
    if session_id is None:
        session_id = str(uuid4())

    max_age = settings.jwt_refresh_token_expires_days * 24 * 60 * 60
    response.set_cookie(
        key=settings.jwt_session_cookie_name,
        value=session_id,
        httponly=False,
        secure=settings.jwt_refresh_cookie_secure,
        samesite=settings.jwt_refresh_cookie_samesite,
        max_age=max_age,
        expires=max_age,
        path="/",
    )


def _clear_auth_cookies(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.jwt_refresh_cookie_name,
        path="/",
    )
    response.delete_cookie(
        key=settings.jwt_session_cookie_name,
        path="/",
    )
