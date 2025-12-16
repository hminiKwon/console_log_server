from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from console_log_server.models import Base


class Room(Base):
    """화상 통화 방 메타데이터."""

    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_number: Mapped[str] = mapped_column(String(6), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    creator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    janus_room_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    max_participants: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
