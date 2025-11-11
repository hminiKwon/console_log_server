from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """헬스 체크 응답 모델."""

    status: str = Field(default="ok", description="서비스 상태")
    timestamp: datetime = Field(description="UTC 기준 타임스탬프")


class HelloResponse(BaseModel):
    """Hello API 응답 모델."""

    message: str = Field(description="간단한 인사 메시지")
