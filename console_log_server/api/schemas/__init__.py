"""Pydantic DTOs used by API endpoints."""

from .ai import AiChatRequest, AiChatResponse
from .auth import AuthResponse, LoginRequest, RegisterRequest, TokenResponse, UserResponse
from .responses import HealthResponse, HelloResponse
from .room import (
    RoomCreateRequest,
    RoomCreateResponse,
    RoomJoinRequest,
    RoomJoinResponse,
    RoomSummaryResponse,
)

__all__ = [
    "HealthResponse",
    "HelloResponse",
    "RegisterRequest",
    "AuthResponse",
    "LoginRequest",
    "UserResponse",
    "TokenResponse",
    "AiChatRequest",
    "AiChatResponse",
    "RoomCreateRequest",
    "RoomCreateResponse",
    "RoomJoinRequest",
    "RoomJoinResponse",
    "RoomSummaryResponse",
]
