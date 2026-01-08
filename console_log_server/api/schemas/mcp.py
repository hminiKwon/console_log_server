from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class McpServerInfo(BaseModel):
    name: str
    transport: str
    description: str | None = None


class McpServerListResponse(BaseModel):
    servers: list[McpServerInfo]


class McpTool(BaseModel):
    name: str
    description: str | None = None
    input_schema: dict[str, Any] | None = None


class McpToolListResponse(BaseModel):
    tools: list[McpTool]


class McpToolCallRequest(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)


class McpToolCallResponse(BaseModel):
    content: list[dict[str, Any]] = Field(default_factory=list)
    is_error: bool | None = None
