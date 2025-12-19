from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from console_log_server.api import init_app
from console_log_server.core.logging_config import get_logger, setup_logging
from console_log_server.core import get_settings
from console_log_server.core.database import create_all_tables


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_all_tables()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings)

    app = FastAPI(
        title="Console Log Server",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    init_app(app)

    if settings.debug:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:3000",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    logger = get_logger("console_log_server.request")

    @app.middleware("http")
    async def log_requests(request, call_next):  # type: ignore[no-untyped-def]
        from time import perf_counter

        start = perf_counter()
        response = await call_next(request)
        duration_ms = (perf_counter() - start) * 1000
        logger.info(
            "%s %s %s %.2fms ua=%s ip=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request.headers.get("user-agent", "-"),
            request.client.host if request.client else "-",
        )
        return response

    return app


app = create_app()
