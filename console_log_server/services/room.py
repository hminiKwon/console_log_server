from __future__ import annotations

import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from console_log_server.api.schemas.room import RoomCreateRequest
from console_log_server.models import Room
from console_log_server.repositories import RoomRepository
from console_log_server.core.logging_config import get_logger
from console_log_server.services.janus import JanusAdminClient
from console_log_server.core.settings import get_settings
from console_log_server.utils.security import hash_password, verify_password


class RoomService:
    """화상 통화 방 생성/입장/삭제 비즈니스 로직."""

    def __init__(
        self, session: Session, *, janus_client: JanusAdminClient | None = None
    ) -> None:
        self.session = session
        self.repository = RoomRepository(session)
        self.janus_client = janus_client or self._build_janus_client()
        self.logger = get_logger(__name__)

    def create_room(
        self, payload: RoomCreateRequest, *, creator_id: int | None
    ) -> Room:
        if payload.password and not (4 <= len(payload.password) <= 6):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="비밀번호는 4~6자리여야 합니다.",
            )

        max_participants = payload.max_participants or 4
        if max_participants > 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="최대 참가자 수는 4명까지입니다.",
            )

        room_number = self._generate_unique_room_number()
        password_hash = hash_password(payload.password) if payload.password else None

        janus_room_id: str | None = None
        if self.janus_client:
            try:
                janus_room_id = self.janus_client.create_room(
                    title=payload.title,
                    room_number=room_number,
                    pin=payload.password,
                    max_participants=max_participants,
                )
            except HTTPException as exc:
                self.logger.error(
                    "janus_create_room_failed number=%s err=%s",
                    room_number,
                    exc.detail if isinstance(exc.detail, str) else exc.detail,
                )
                raise

        return self.repository.create(
            room_number=room_number,
            title=payload.title,
            password_hash=password_hash,
            creator_id=creator_id,
            janus_room_id=janus_room_id,
            max_participants=max_participants,
        )

    def list_active_rooms(self) -> list[Room]:
        return list(self.repository.list_active())

    def join_room(self, room_number: str, *, password: str | None) -> Room:
        room = self.repository.get_active_by_number(room_number)
        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="방을 찾을 수 없습니다.",
            )

        if room.password_hash:
            if not password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="비밀번호가 필요합니다.",
                )
            if not verify_password(password, room.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="비밀번호가 일치하지 않습니다.",
                )

        return room

    def delete_room(self, room_number: str, *, requester_id: int) -> None:
        room = self.repository.get_by_number(room_number)
        if room is None or not room.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="방을 찾을 수 없습니다.",
            )

        if room.creator_id and room.creator_id != requester_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="삭제 권한이 없습니다.",
            )

        self.repository.deactivate(room)
        if self.janus_client and room.janus_room_id:
            # 방 삭제와 Janus destroy 순서가 달라도 메타만 비활성화하면 되므로 예외는 올리지 않음
            try:
                self.janus_client.destroy_room(room.janus_room_id)
            except HTTPException as exc:
                # 이미 비활성화했으므로 Janus 실패는 로깅/모니터링 수준으로 처리
                self.logger.warning(
                    "janus_destroy_room_failed number=%s janus_room_id=%s err=%s",
                    room.room_number,
                    room.janus_room_id,
                    exc.detail if isinstance(exc.detail, str) else exc.detail,
                )

    def _generate_unique_room_number(self, *, max_attempts: int = 5) -> str:
        for _ in range(max_attempts):
            candidate = f"{secrets.randbelow(1_000_000):06d}"
            if not self.repository.exists(candidate):
                return candidate
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="방 번호를 생성할 수 없습니다. 잠시 후 다시 시도하세요.",
        )

    def _build_janus_client(self) -> JanusAdminClient | None:
        settings = get_settings()

        if not settings.janus_admin_url:
            return None
        return JanusAdminClient(
            base_url=settings.janus_admin_url,
            admin_secret=settings.janus_admin_secret,
            api_secret=settings.janus_api_secret,
        )
