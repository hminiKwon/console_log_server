from __future__ import annotations

from pydantic import BaseModel, Field


class FortuneRequest(BaseModel):
    """오늘의 운세 요청 스키마."""

    birth_date: str = Field(..., description="출생일 YYYY-MM-DD")
    calendar: str = Field(..., pattern="^(solar|lunar)$", description="solar 또는 lunar")
    gender: str = Field(..., pattern="^(male|female)$", description="male 또는 female")
    birth_time: int | None = Field(
        default=None,
        ge=0,
        le=11,
        description="태어난 시각(지지) 0~11: 자=0, 축=1, 인=2, 묘=3, 진=4, 사=5, 오=6, 미=7, 신=8, 유=9, 술=10, 해=11",
    )


class FortuneResponse(BaseModel):
    """오늘의 운세 응답 스키마."""

    overall: str
    wealth: str
    business: str
    career: str
    love: str
    wish: str
    advice: str
    score: int | None = Field(default=None, ge=0, le=100)
