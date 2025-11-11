from __future__ import annotations

from fastapi import APIRouter, Depends

from console_log_server.api.deps import get_app_settings, get_current_user
from console_log_server.api.schemas import HelloResponse
from console_log_server.core import Settings
from console_log_server.models import User

router = APIRouter(tags=["hello"])


@router.get("/hello", summary="Hello FastAPI", response_model=HelloResponse)
def hello(
    _: Settings = Depends(get_app_settings),
    __: User = Depends(get_current_user),
) -> HelloResponse:
    return HelloResponse(message="Hello, FastAPI!")
