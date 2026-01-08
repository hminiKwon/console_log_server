from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from console_log_server.services.mcp.config import McpServerConfig
from console_log_server.services.mcp.registry import (
    McpServerRegistry,
    get_mcp_registry,
)



class McpClientManager:
    def __init__(self, registry: McpServerRegistry | None = None) -> None:
        self._registry = registry or get_mcp_registry()

    def list_servers(self) -> list[McpServerConfig]:
        return self._registry.list_servers()

    async def list_tools(self, server_name: str) -> list[dict[str, Any]]:
        server = self._registry.get_server(server_name)
        async with self._session(server) as session:
            result = await asyncio.wait_for(
                session.list_tools(), timeout=server.timeout_seconds
            )
        return _normalize_tools(result)

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        server = self._registry.get_server(server_name)
        async with self._session(server) as session:
            result = await asyncio.wait_for(
                session.call_tool(tool_name, arguments or {}),
                timeout=server.timeout_seconds,
            )
        return _normalize_tool_result(result)

    @asynccontextmanager
    async def _session(self, server: McpServerConfig) -> AsyncIterator[Any]:
        ClientSession, StdioServerParameters, stdio_client = _load_mcp_client()
        command = (
            sys.executable if server.command in {"python", "python3"} else server.command
        )
        params = StdioServerParameters(
            command=command,
            args=server.args,
            env=server.env,
            cwd=server.cwd,
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session


def _load_mcp_client() -> tuple[Any, Any, Any]:
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("MCP client requires the 'mcp' package.") from exc
    return ClientSession, StdioServerParameters, stdio_client


def _normalize_tools(result: Any) -> list[dict[str, Any]]:
    if hasattr(result, "tools"):
        tools = result.tools
    elif isinstance(result, dict) and "tools" in result:
        tools = result["tools"]
    else:
        tools = result
    if not isinstance(tools, list):
        tools = [tools]
    return [_normalize_tool(tool) for tool in tools]


def _normalize_tool(tool: Any) -> dict[str, Any]:
    if isinstance(tool, dict):
        data = tool
    elif hasattr(tool, "model_dump"):
        data = tool.model_dump()
    elif hasattr(tool, "__dict__"):
        data = tool.__dict__
    else:
        return {"name": str(tool)}
    return {
        "name": data.get("name", ""),
        "description": data.get("description"),
        "input_schema": data.get("inputSchema") or data.get("input_schema"),
    }


def _normalize_tool_result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        data = result
    elif hasattr(result, "model_dump"):
        data = result.model_dump()
    elif hasattr(result, "__dict__"):
        data = result.__dict__
    else:
        return {"content": [{"text": str(result)}]}

    content = data.get("content", [])
    if not isinstance(content, list):
        content = [content]
    normalized = [_normalize_content(item) for item in content]
    payload: dict[str, Any] = {"content": normalized}
    if "isError" in data:
        payload["is_error"] = bool(data["isError"])
    if "is_error" in data:
        payload["is_error"] = bool(data["is_error"])
    return payload


def _normalize_content(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return item
    if hasattr(item, "model_dump"):
        return item.model_dump()
    if hasattr(item, "__dict__"):
        return dict(item.__dict__)
    return {"text": str(item)}
