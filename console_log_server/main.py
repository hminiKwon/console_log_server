from __future__ import annotations

from console_log_server.app import create_app
from console_log_server.config import get_settings

app = create_app()


def run(*, reload: bool = False) -> None:
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "console_log_server.app:app",
        host=settings.host,
        port=settings.port,
        reload=reload,
        factory=False,
    )


def run_dev() -> None:
    run(reload=True)


if __name__ == "__main__":
    run()
