"""Pydantic DTOs used by API endpoints."""

from .ai import AiChatRequest, AiChatResponse
from .auth import AuthResponse, LoginRequest, RegisterRequest, TokenResponse, UserResponse
from .responses import HealthResponse, HelloResponse
from .mcp import (
    McpServerInfo,
    McpServerListResponse,
    McpTool,
    McpToolListResponse,
    McpToolCallRequest,
    McpToolCallResponse,
)
from .room import (
    RoomCreateRequest,
    RoomCreateResponse,
    RoomJoinRequest,
    RoomJoinResponse,
    RoomSummaryResponse,
)
from .fortune import FortuneRequest, FortuneResponse

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
    "FortuneRequest",
    "FortuneResponse",
    "McpServerInfo",
    "McpServerListResponse",
    "McpTool",
    "McpToolListResponse",
    "McpToolCallRequest",
    "McpToolCallResponse",
]
