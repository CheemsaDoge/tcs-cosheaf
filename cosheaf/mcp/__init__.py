"""Read-only MCP server surface for TCS-Cosheaf."""

from cosheaf.mcp.server import (
    READ_ONLY_TOOL_NAMES,
    ReadOnlyMcpServer,
    resource_definitions,
    serve_stdio,
    tool_definitions,
)

__all__ = [
    "READ_ONLY_TOOL_NAMES",
    "ReadOnlyMcpServer",
    "resource_definitions",
    "serve_stdio",
    "tool_definitions",
]
