from __future__ import annotations

from pydantic import BaseModel, Field


class AiChatRequest(BaseModel):
    """AI 챗봇 요청 스키마."""

    message: str = Field(min_length=1, description="사용자가 보낸 메시지")


class AiChatResponse(BaseModel):
    """AI 챗봇 응답 스키마."""

    reply: str = Field(description="모델이 생성한 답변")
