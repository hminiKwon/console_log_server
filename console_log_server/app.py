from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from console_log_server.api import init_app
from console_log_server.core import get_settings
from console_log_server.core.database import create_all_tables


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_all_tables()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Console Log Server",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    init_app(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "https://www.hmini.co.kr",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()
