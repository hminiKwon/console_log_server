from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from console_log_server.api.deps import get_current_user, get_db_session
from console_log_server.api.schemas import (
    RoomCreateRequest,
    RoomCreateResponse,
    RoomJoinRequest,
    RoomJoinResponse,
    RoomSummaryResponse,
)
from console_log_server.models import Room, User
from console_log_server.services.room import RoomService

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post(
    "",
    summary="방 생성",
    response_model=RoomCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_room(
    payload: RoomCreateRequest,
    session: Session = Depends(get_db_session),
) -> RoomCreateResponse:
    room = RoomService(session).create_room(payload, creator_id=user.id)
    return _to_create_response(room)


@router.get(
    "",
    summary="방 목록 조회",
    response_model=list[RoomSummaryResponse],
)
def list_rooms(
    session: Session = Depends(get_db_session),
) -> list[RoomSummaryResponse]:
    rooms = RoomService(session).list_active_rooms()
    return [_to_summary_response(room) for room in rooms]


@router.post(
    "/{room_number}/join",
    summary="방 입장",
    response_model=RoomJoinResponse,
)
def join_room(
    room_number: str,
    payload: RoomJoinRequest,
    session: Session = Depends(get_db_session),
) -> RoomJoinResponse:
    room = RoomService(session).join_room(room_number, password=payload.password)
    return _to_join_response(room)


@router.delete(
    "/{room_number}",
    summary="방 삭제",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_room(
    room_number: str,
    session: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> None:
    RoomService(session).delete_room(room_number, requester_id=user.id)


def _to_create_response(room: Room) -> RoomCreateResponse:
    return RoomCreateResponse(
        room_number=room.room_number,
        title=room.title,
        need_password=bool(room.password_hash),
        janus_room_id=room.janus_room_id,
    )


def _to_summary_response(room: Room) -> RoomSummaryResponse:
    return RoomSummaryResponse(
        room_number=room.room_number,
        title=room.title,
        need_password=bool(room.password_hash),
        created_at=room.created_at,
        max_participants=room.max_participants,
    )


def _to_join_response(room: Room) -> RoomJoinResponse:
    return RoomJoinResponse(
        room_number=room.room_number,
        title=room.title,
        janus_room_id=room.janus_room_id,
        need_password=bool(room.password_hash),
    )
