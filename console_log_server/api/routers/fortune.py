from __future__ import annotations

from fastapi import APIRouter, Depends, status

from console_log_server.api.schemas import FortuneRequest, FortuneResponse
from console_log_server.services.fortune import FortuneService

router = APIRouter(prefix="/fortune", tags=["fortune"])


@router.post(
    "/today",
    summary="오늘의 운세",
    response_model=FortuneResponse,
    status_code=status.HTTP_200_OK,
)
def today_fortune(payload: FortuneRequest) -> FortuneResponse:
    return FortuneService().get_today_fortune(payload)
