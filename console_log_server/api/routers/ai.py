from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from console_log_server.api.deps import get_app_settings, get_current_user
from console_log_server.api.schemas import AiChatRequest, AiChatResponse
from console_log_server.core import Settings
from console_log_server.models import User
from console_log_server.services.ai import AiChatService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post(
    "/chat",
    summary="AI 챗봇 대화",
    response_model=AiChatResponse,
    status_code=status.HTTP_200_OK,
)
def chat(
    payload: AiChatRequest,
    request: Request,
    _: User = Depends(get_current_user),
    settings: Settings = Depends(get_app_settings),
) -> AiChatResponse:
    service = AiChatService()
    thread_id = request.cookies.get(settings.jwt_session_cookie_name)

    try:
        reply = service.chat(payload.message, thread_id=thread_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return AiChatResponse(reply=reply)
