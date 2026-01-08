from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class McpServerConfig(BaseModel):
    name: str
    description: str | None = None
    transport: Literal["stdio"] = "stdio"
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    cwd: str | None = None
    timeout_seconds: float = 10.0

    @model_validator(mode="after")
    def _validate_transport(self) -> "McpServerConfig":
        if self.transport != "stdio":
            raise ValueError(f"Unsupported transport: {self.transport}")
        if not self.command:
            raise ValueError("stdio transport requires command")
        return self
