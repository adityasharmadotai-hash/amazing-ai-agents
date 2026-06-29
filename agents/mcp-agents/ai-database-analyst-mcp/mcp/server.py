"""MCP server (stdio, JSON-RPC 2.0).

Exposes the database-analyst tools over a line-delimited JSON-RPC interface on
stdin/stdout — the transport used by the Model Context Protocol. Supported
methods:

  * ``initialize``  -> server capabilities
  * ``tools/list``  -> discover available tools
  * ``tools/call``  -> invoke a tool by name with arguments

Run it standalone:

    python -m mcp.server

It builds the registry from the default connection in your ``.env``.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from core.config import get_settings
from core.logging_config import get_logger
from database.connection import ConnectionManager
from database.repository import DatabaseRepository
from database.safe_sql import SafeSQLGuard
from mcp.registry import MCPToolRegistry
from mcp.tools import build_registry
from services.chart_service import ChartService
from services.export_service import ExportService
from services.optimization_service import OptimizationService
from services.query_service import QueryService

logger = get_logger("mcp.server")

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "ai-database-analyst", "version": "1.0.0"}


def build_default_registry() -> MCPToolRegistry:
    """Build a registry wired to the default database from settings."""
    settings = get_settings()
    config = settings.default_connection()
    cm = ConnectionManager(config)
    cm.connect()
    guard = SafeSQLGuard(read_only=settings.read_only_mode)
    repo = DatabaseRepository(cm, guard=guard, max_result_rows=settings.max_result_rows)
    query_service = QueryService(repo)
    chart_service = ChartService(theme=settings.chart_theme)
    export_service = ExportService(export_dir=settings.export_dir)
    optimization_service = OptimizationService(repo)
    return build_registry(
        repository=repo,
        query_service=query_service,
        chart_service=chart_service,
        export_service=export_service,
        optimization_service=optimization_service,
    )


class MCPServer:
    """A minimal JSON-RPC 2.0 server over stdio for MCP tool dispatch."""

    def __init__(self, registry: MCPToolRegistry) -> None:
        self.registry = registry

    def handle(self, request: dict[str, Any]) -> dict[str, Any] | None:
        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params") or {}

        # Notifications (no id) get no response.
        if request_id is None and method and method.startswith("notifications/"):
            return None

        try:
            result = self._dispatch(method, params)
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception as exc:  # noqa: BLE001
            logger.exception("RPC error for method %s", method)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": str(exc)},
            }

    def _dispatch(self, method: str | None, params: dict[str, Any]) -> Any:
        if method == "initialize":
            return {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
            }
        if method == "tools/list":
            return {"tools": self.registry.list_tools()}
        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            result = self.registry.call(name, arguments)
            if not result.ok:
                return {
                    "content": [{"type": "text", "text": result.error or "tool error"}],
                    "isError": True,
                }
            return {
                "content": [
                    {"type": "text", "text": json.dumps(result.data, default=str)}
                ],
                "isError": False,
            }
        raise ValueError(f"Unknown method: {method}")

    def serve_forever(self) -> None:  # pragma: no cover - I/O loop
        logger.info("MCP server ready (stdio). Tools: %s", list(self.registry.tools))
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                continue
            response = self.handle(request)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()


def main() -> None:  # pragma: no cover
    registry = build_default_registry()
    MCPServer(registry).serve_forever()


if __name__ == "__main__":  # pragma: no cover
    main()
