"""API 라우터 등록."""

from fastapi import FastAPI

from . import ai, auth, health, hello


def register_routers(app: FastAPI) -> None:
    app.include_router(health.router)
    app.include_router(hello.router)
    app.include_router(auth.router)
    app.include_router(ai.router)
