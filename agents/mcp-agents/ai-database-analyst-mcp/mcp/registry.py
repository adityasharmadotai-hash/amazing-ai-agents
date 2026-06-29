"""MCP tool registry.

Defines the :class:`MCPTool` abstraction (a name, description, JSON-schema for
inputs and a handler) and a :class:`MCPToolRegistry` that supports tool
discovery and typed invocation — the two core operations of the Model Context
Protocol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from core.logging_config import get_logger

logger = get_logger(__name__)

ToolHandler = Callable[[dict[str, Any]], Any]


@dataclass
class MCPTool:
    """A single, independently-callable MCP tool."""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler

    def to_spec(self) -> dict[str, Any]:
        """Return the MCP-style tool descriptor (for ``tools/list``)."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }

    def validate_arguments(self, arguments: dict[str, Any]) -> None:
        """Lightweight validation of arguments against required schema fields."""
        required = self.input_schema.get("required", [])
        missing = [r for r in required if r not in arguments or arguments[r] in (None, "")]
        if missing:
            raise ValueError(
                f"Tool '{self.name}' missing required argument(s): {', '.join(missing)}"
            )


@dataclass
class MCPToolResult:
    """The structured result of a tool invocation."""

    ok: bool
    tool: str
    data: Any = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "tool": self.tool, "data": self.data, "error": self.error}


@dataclass
class MCPToolRegistry:
    """Holds the available tools and dispatches calls to them."""

    tools: dict[str, MCPTool] = field(default_factory=dict)

    def register(self, tool: MCPTool) -> None:
        if tool.name in self.tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self.tools[tool.name] = tool
        logger.debug("Registered MCP tool: %s", tool.name)

    def list_tools(self) -> list[dict[str, Any]]:
        """MCP ``tools/list`` — discover all available tools."""
        return [tool.to_spec() for tool in self.tools.values()]

    def get(self, name: str) -> MCPTool:
        if name not in self.tools:
            raise KeyError(f"Unknown tool: {name}")
        return self.tools[name]

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> MCPToolResult:
        """MCP ``tools/call`` — invoke a tool by name with arguments."""
        arguments = arguments or {}
        try:
            tool = self.get(name)
            tool.validate_arguments(arguments)
            logger.info("Calling MCP tool '%s' with keys=%s", name, list(arguments.keys()))
            data = tool.handler(arguments)
            return MCPToolResult(ok=True, tool=name, data=data)
        except Exception as exc:  # noqa: BLE001 - surface any tool error uniformly
            logger.exception("MCP tool '%s' failed", name)
            return MCPToolResult(ok=False, tool=name, error=str(exc))
