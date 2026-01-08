from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("console-log-server-echo")


@mcp.tool()
def echo(message: str) -> str:
    return message


@mcp.tool()
def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    mcp.run()
