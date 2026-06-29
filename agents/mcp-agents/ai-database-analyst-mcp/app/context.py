"""Application context / dependency-injection container.

The :class:`AnalystContext` owns all live, connection-scoped objects: the
connection manager, repository, services, MCP registry and the AI agent. The UI
holds a single context per active database connection and rebuilds it on
connect / reconnect.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from agents.database_analyst import DatabaseAnalystAgent
from agents.gemini_client import GeminiClient
from core.config import AppSettings, ConnectionConfig
from core.exceptions import AIAgentError
from core.logging_config import get_logger
from core.session import SessionMemory
from database.connection import ConnectionManager
from database.repository import DatabaseRepository
from database.safe_sql import SafeSQLGuard
from mcp.registry import MCPToolRegistry
from mcp.tools import build_registry
from services.chart_service import ChartService
from services.export_service import ExportService
from services.optimization_service import OptimizationService
from services.query_service import QueryService
from services.report_service import ReportService

logger = get_logger(__name__)


@dataclass
class AnalystContext:
    """A fully-wired set of services bound to one database connection."""

    config: ConnectionConfig
    settings: AppSettings
    connection_manager: ConnectionManager
    repository: DatabaseRepository
    guard: SafeSQLGuard
    query_service: QueryService
    chart_service: ChartService
    export_service: ExportService
    optimization_service: OptimizationService
    report_service: ReportService
    registry: MCPToolRegistry
    agent: DatabaseAnalystAgent
    llm: Optional[GeminiClient] = None
    memory: SessionMemory = field(default_factory=SessionMemory)

    @property
    def dialect(self) -> str:
        return self.repository.dialect

    def set_read_only(self, read_only: bool) -> None:
        self.guard.set_read_only(read_only)

    def dispose(self) -> None:
        self.connection_manager.dispose()


def build_llm(settings: AppSettings, *, api_key: Optional[str] = None) -> Optional[GeminiClient]:
    """Create a Gemini client from settings (or an override key). None if no key."""
    key = (api_key or settings.gemini_api_key.get_secret_value()).strip()
    if not key:
        logger.warning("No Gemini API key configured; AI features disabled.")
        return None
    try:
        return GeminiClient(
            api_key=key,
            model=settings.gemini_model,
            temperature=settings.gemini_temperature,
            max_tokens=settings.gemini_max_tokens,
        )
    except AIAgentError as exc:
        logger.error("Failed to initialise Gemini: %s", exc)
        return None


def create_context(
    config: ConnectionConfig,
    settings: AppSettings,
    *,
    api_key: Optional[str] = None,
    memory: Optional[SessionMemory] = None,
) -> AnalystContext:
    """Connect to the database and wire up the full service graph."""
    cm = ConnectionManager(config)
    cm.connect()  # validates connection, raises friendly errors on failure

    guard = SafeSQLGuard(read_only=settings.read_only_mode)
    repo = DatabaseRepository(cm, guard=guard, max_result_rows=settings.max_result_rows)

    query_service = QueryService(repo)
    chart_service = ChartService(theme=settings.chart_theme)
    export_service = ExportService(export_dir=settings.export_dir)
    optimization_service = OptimizationService(repo)

    llm = build_llm(settings, api_key=api_key)
    report_service = ReportService(llm)

    mem = memory or SessionMemory()
    registry = build_registry(
        repository=repo,
        query_service=query_service,
        chart_service=chart_service,
        export_service=export_service,
        optimization_service=optimization_service,
        schema_provider=mem.get_schema,
    )

    agent = DatabaseAnalystAgent(
        repository=repo,
        llm=llm,
        chart_service=chart_service,
        optimization_service=optimization_service,
        guard=guard,
        auto_explain=settings.auto_explain_sql,
        auto_charts=settings.auto_generate_charts,
    )

    logger.info("AnalystContext created for %s (dialect=%s)", config.display_name(), repo.dialect)
    return AnalystContext(
        config=config,
        settings=settings,
        connection_manager=cm,
        repository=repo,
        guard=guard,
        query_service=query_service,
        chart_service=chart_service,
        export_service=export_service,
        optimization_service=optimization_service,
        report_service=report_service,
        registry=registry,
        agent=agent,
        llm=llm,
        memory=mem,
    )
