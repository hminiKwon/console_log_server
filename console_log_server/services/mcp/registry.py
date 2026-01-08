from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from console_log_server.core import Settings, get_settings
from console_log_server.core.logging_config import get_logger
from console_log_server.services.mcp.config import McpServerConfig

logger = get_logger(__name__)


class McpServerRegistry:
    def __init__(self, servers: list[McpServerConfig]) -> None:
        self._servers = {server.name: server for server in servers}

    @classmethod
    def from_settings(
        cls,
        settings: Settings | None = None,
    ) -> "McpServerRegistry":
        settings = settings or get_settings()
        raw_entries: list[dict[str, Any]] = []

        file_entries = _load_server_file(settings.mcp_servers_file)
        raw_entries.extend(file_entries)
        raw_entries.extend(settings.mcp_servers)

        servers: list[McpServerConfig] = []
        seen: set[str] = set()
        for entry in raw_entries:
            if not isinstance(entry, dict):
                logger.warning("Skipping MCP server entry: not a dict")
                continue
            try:
                server = McpServerConfig.model_validate(entry)
            except ValidationError as exc:
                logger.warning("Skipping MCP server entry: %s", exc)
                continue
            if server.name in seen:
                logger.warning("Skipping MCP server entry: duplicate name %s", server.name)
                continue
            seen.add(server.name)
            servers.append(server)

        return cls(servers)

    def list_servers(self) -> list[McpServerConfig]:
        return list(self._servers.values())

    def get_server(self, name: str) -> McpServerConfig:
        try:
            return self._servers[name]
        except KeyError as exc:
            raise KeyError(f"MCP server not found: {name}") from exc


@lru_cache
def get_mcp_registry() -> McpServerRegistry:
    return McpServerRegistry.from_settings()


def _load_server_file(path_str: str | None) -> list[dict[str, Any]]:
    if not path_str:
        return []
    path = Path(path_str)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        logger.info("MCP servers file not found: %s", path)
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.warning("Invalid MCP server file JSON: %s", exc)
        return []
    if not isinstance(payload, list):
        logger.warning("MCP servers file must be a JSON list")
        return []
    return payload
