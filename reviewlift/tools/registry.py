"""Registers MCP tools so agents can discover and call them."""

from reviewlift.tools.mcp_server import get_diff, list_hunks

TOOL_REGISTRY = {
    "get_diff": get_diff,
    "list_hunks": list_hunks,
}


def get_tool(name: str):
    return TOOL_REGISTRY[name]