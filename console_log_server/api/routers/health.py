from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from console_log_server.api.schemas import HealthResponse

router = APIRouter(tags=["health"])


def _current_timestamp() -> datetime:
    return datetime.now(tz=timezone.utc)


@router.get("/health", summary="Health check", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(timestamp=_current_timestamp())
