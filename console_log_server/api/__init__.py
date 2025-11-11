"""API 초기화 모듈."""

from fastapi import FastAPI

from .routers import register_routers


def init_app(app: FastAPI) -> None:
    """모든 라우터를 FastAPI 애플리케이션에 등록."""

    register_routers(app)
