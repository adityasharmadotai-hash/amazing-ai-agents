"""Model Context Protocol (MCP) integration package.

This package exposes the database-analyst capabilities as a set of
independently-callable MCP tools, a registry that describes them with JSON
schemas, and a server that dispatches tool calls over JSON-RPC (stdio).

Note: this local package is named ``mcp`` to match the project layout. It
implements an MCP-faithful tool protocol (tool discovery + typed invocation)
rather than importing the third-party ``mcp`` SDK, which keeps the application
self-contained and immediately runnable.
"""

from mcp.registry import MCPTool, MCPToolRegistry
from mcp.tools import build_registry

__all__ = ["MCPTool", "MCPToolRegistry", "build_registry"]
