from __future__ import annotations

import logging
import logging.config
import os
from pathlib import Path

from console_log_server.core.settings import Settings


def setup_logging(settings: Settings) -> None:
    """루트/uvicorn 로거를 앱 설정에 맞게 초기화."""

    log_level = settings.log_level.upper()
    log_file = Path(settings.log_file)
    if log_file.parent:
        os.makedirs(log_file.parent, exist_ok=True)

    fmt = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": fmt, "datefmt": datefmt},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "standard",
                "filename": str(log_file),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "root": {"level": log_level, "handlers": ["console", "file"]},
        "loggers": {
            "uvicorn": {"level": log_level, "handlers": ["console", "file"], "propagate": False},
            "uvicorn.error": {"level": log_level, "handlers": ["console", "file"], "propagate": False},
            "uvicorn.access": {"level": log_level, "handlers": ["console", "file"], "propagate": False},
        },
    }

    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """로거 헬퍼."""

    return logging.getLogger(name)
