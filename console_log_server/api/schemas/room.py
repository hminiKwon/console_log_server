from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RoomCreateRequest(BaseModel):
    """방 생성 요청."""

    title: str = Field(..., min_length=1, max_length=100)
    password: str | None = Field(
        default=None,
        min_length=4,
        max_length=6,
        description="4~6자리 비밀번호(선택)",
    )
    max_participants: int | None = Field(
        default=4,
        gt=0,
        le=4,
        description="최대 참가자 수(기본 4, 최대 4)",
    )


class RoomCreateResponse(BaseModel):
    """방 생성 응답."""

    room_number: str
    title: str
    need_password: bool
    janus_room_id: str | None = None


class RoomSummaryResponse(BaseModel):
    """방 목록 조회 시 사용."""

    room_number: str
    title: str
    need_password: bool
    created_at: datetime
    max_participants: int | None = None


class RoomJoinRequest(BaseModel):
    """방 입장 요청."""

    password: str | None = Field(
        default=None,
        min_length=4,
        max_length=6,
        description="비밀번호가 있는 방만 필요",
    )


class RoomJoinResponse(BaseModel):
    """방 입장 응답."""

    room_number: str
    title: str
    janus_room_id: str | None = None
    need_password: bool
