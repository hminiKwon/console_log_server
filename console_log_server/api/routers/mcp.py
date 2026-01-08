from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from console_log_server.api.deps import get_current_user
from console_log_server.api.schemas import (
    McpServerListResponse,
    McpToolCallRequest,
    McpToolCallResponse,
    McpToolListResponse,
)
from console_log_server.models import User
from console_log_server.services.mcp.manager import McpClientManager

router = APIRouter(prefix="/mcp", tags=["mcp"])


def get_mcp_manager() -> McpClientManager:
    return McpClientManager()


@router.get(
    "/servers",
    summary="등록된 MCP 서버 목록",
    response_model=McpServerListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_servers(
    _: User = Depends(get_current_user),
    manager: McpClientManager = Depends(get_mcp_manager),
) -> McpServerListResponse:
    servers = [
        {
            "name": server.name,
            "transport": server.transport,
            "description": server.description,
        }
        for server in manager.list_servers()
    ]
    return McpServerListResponse(servers=servers)


@router.get(
    "/servers/{server_name}/tools",
    summary="MCP 서버의 도구 목록",
    response_model=McpToolListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_tools(
    server_name: str,
    _: User = Depends(get_current_user),
    manager: McpClientManager = Depends(get_mcp_manager),
) -> McpToolListResponse:
    try:
        tools = await manager.list_tools(server_name)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="MCP 서버 응답이 지연되었습니다.",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return McpToolListResponse(tools=tools)


@router.post(
    "/servers/{server_name}/tools/{tool_name}",
    summary="MCP 도구 실행",
    response_model=McpToolCallResponse,
    status_code=status.HTTP_200_OK,
)
async def call_tool(
    server_name: str,
    tool_name: str,
    payload: McpToolCallRequest,
    _: User = Depends(get_current_user),
    manager: McpClientManager = Depends(get_mcp_manager),
) -> McpToolCallResponse:
    try:
        result = await manager.call_tool(
            server_name,
            tool_name,
            arguments=payload.arguments,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="MCP 서버 응답이 지연되었습니다.",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return McpToolCallResponse(**result)
