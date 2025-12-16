from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from console_log_server.models import Room


class RoomRepository:
    """방 메타데이터 접근 계층."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        room_number: str,
        title: str,
        password_hash: str | None,
        creator_id: int | None,
        janus_room_id: str | None,
        max_participants: int | None,
    ) -> Room:
        room = Room(
            room_number=room_number,
            title=title,
            password_hash=password_hash,
            creator_id=creator_id,
            janus_room_id=janus_room_id,
            max_participants=max_participants,
        )
        self.session.add(room)
        self.session.commit()
        self.session.refresh(room)
        return room

    def exists(self, room_number: str) -> bool:
        stmt = select(Room.id).where(Room.room_number == room_number)
        return self.session.execute(stmt).first() is not None

    def get_active_by_number(self, room_number: str) -> Optional[Room]:
        stmt = (
            select(Room)
            .where(Room.room_number == room_number)
            .where(Room.is_active.is_(True))
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_number(self, room_number: str) -> Optional[Room]:
        stmt = select(Room).where(Room.room_number == room_number)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_active(self) -> Iterable[Room]:
        stmt = (
            select(Room)
            .where(Room.is_active.is_(True))
            .order_by(Room.created_at.desc())
        )
        return (row[0] for row in self.session.execute(stmt).all())

    def deactivate(self, room: Room) -> None:
        room.is_active = False
        self.session.add(room)
        self.session.commit()
