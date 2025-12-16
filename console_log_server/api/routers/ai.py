from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from console_log_server.api.deps import get_current_user
from console_log_server.api.schemas import AiChatRequest, AiChatResponse
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
    user: User = Depends(get_current_user),
) -> AiChatResponse:
    service = AiChatService()
    # 유저 ID를 thread_id로 사용해 사용자별 대화 메모리를 분리
    thread_id = str(user.id) if user and user.id is not None else "default"

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
