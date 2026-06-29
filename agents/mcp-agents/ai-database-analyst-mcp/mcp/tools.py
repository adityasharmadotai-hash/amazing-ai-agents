"""MCP tool implementations.

Each capability of the database analyst is exposed as an independently-callable
MCP tool with a JSON-schema input contract:

  * schema_reader          - read the full database schema
  * table_inspector        - inspect a single table
  * column_inspector       - inspect columns / find columns by keyword
  * sql_executor           - safely execute a SQL statement
  * index_inspector        - list indexes and suggest missing ones
  * relationship_analyzer  - explicit + inferred relationships
  * statistics_collector   - descriptive statistics for a table
  * csv_export             - run a query and export to CSV
  * pdf_export             - run a query and export a PDF report
  * chart_generator        - recommend the best chart for a query

The whole set is assembled into an :class:`MCPToolRegistry` by
:func:`build_registry`, wiring in the concrete services (dependency injection).
"""

from __future__ import annotations

import base64
from typing import Any, Optional

from core.models import QueryResult, SchemaInfo
from database.repository import DatabaseRepository
from mcp.registry import MCPTool, MCPToolRegistry
from services.chart_service import ChartService
from services.export_service import ExportService
from services.optimization_service import OptimizationService
from services.query_service import QueryService


def _result_to_dict(result: QueryResult) -> dict[str, Any]:
    return {
        "sql": result.sql,
        "columns": result.columns,
        "rows": result.rows,
        "row_count": result.row_count,
        "execution_time_ms": result.execution_time_ms,
        "truncated": result.truncated,
        "affected_rows": result.affected_rows,
    }


def build_registry(
    repository: DatabaseRepository,
    query_service: QueryService,
    chart_service: ChartService,
    export_service: ExportService,
    optimization_service: OptimizationService,
    schema_provider: Optional[Any] = None,
) -> MCPToolRegistry:
    """Construct and populate the MCP tool registry.

    ``schema_provider`` is an optional callable returning a cached
    :class:`SchemaInfo`; when absent the schema is read live.
    """

    registry = MCPToolRegistry()

    def get_schema(include_row_counts: bool = False) -> SchemaInfo:
        if schema_provider is not None:
            cached = schema_provider()
            if cached is not None:
                return cached
        return repository.get_schema(include_row_counts=include_row_counts)

    # --- 1. Schema Reader ------------------------------------------------
    def _schema_reader(args: dict[str, Any]) -> dict[str, Any]:
        include_counts = bool(args.get("include_row_counts", True))
        schema = repository.get_schema(include_row_counts=include_counts)
        return schema.model_dump(mode="json")

    registry.register(
        MCPTool(
            name="schema_reader",
            description="Read the full database schema (tables, columns, keys, indexes).",
            input_schema={
                "type": "object",
                "properties": {
                    "include_row_counts": {
                        "type": "boolean",
                        "description": "Include approximate row counts per table.",
                        "default": True,
                    }
                },
                "required": [],
            },
            handler=_schema_reader,
        )
    )

    # --- 2. Table Inspector ----------------------------------------------
    def _table_inspector(args: dict[str, Any]) -> dict[str, Any]:
        table_name = args["table_name"]
        schema = get_schema(include_row_counts=True)
        table = schema.get_table(table_name)
        if table is None:
            raise ValueError(f"Table not found: {table_name}")
        payload = table.model_dump(mode="json")
        if args.get("include_sample", False):
            sample = repository.sample_rows(table_name, int(args.get("sample_limit", 5)))
            payload["sample"] = _result_to_dict(sample)
        return payload

    registry.register(
        MCPTool(
            name="table_inspector",
            description="Inspect a single table: columns, keys, indexes and optional sample rows.",
            input_schema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table."},
                    "include_sample": {"type": "boolean", "default": False},
                    "sample_limit": {"type": "integer", "default": 5},
                },
                "required": ["table_name"],
            },
            handler=_table_inspector,
        )
    )

    # --- 3. Column Inspector ---------------------------------------------
    def _column_inspector(args: dict[str, Any]) -> dict[str, Any]:
        schema = get_schema()
        keyword = args.get("keyword")
        if keyword:
            matches = repository.find_tables_with_column(schema, keyword)
            return {"keyword": keyword, "matches": matches}
        table_name = args.get("table_name")
        if not table_name:
            raise ValueError("Provide either 'table_name' or 'keyword'.")
        table = schema.get_table(table_name)
        if table is None:
            raise ValueError(f"Table not found: {table_name}")
        return {"table": table.name, "columns": [c.model_dump(mode="json") for c in table.columns]}

    registry.register(
        MCPTool(
            name="column_inspector",
            description="List a table's columns, or find tables containing a column keyword (e.g. 'email').",
            input_schema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"},
                    "keyword": {"type": "string", "description": "Substring to search column names for."},
                },
                "required": [],
            },
            handler=_column_inspector,
        )
    )

    # --- 4. SQL Executor -------------------------------------------------
    def _sql_executor(args: dict[str, Any]) -> dict[str, Any]:
        sql = args["sql"]
        params = args.get("params") or {}
        result = repository.execute(sql, params)
        return _result_to_dict(result)

    registry.register(
        MCPTool(
            name="sql_executor",
            description="Safely execute a SQL statement (read-only unless write mode is enabled).",
            input_schema={
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "The SQL statement to run."},
                    "params": {"type": "object", "description": "Named bind parameters."},
                },
                "required": ["sql"],
            },
            handler=_sql_executor,
        )
    )

    # --- 5. Index Inspector ----------------------------------------------
    def _index_inspector(args: dict[str, Any]) -> dict[str, Any]:
        schema = get_schema()
        table_name = args.get("table_name")
        out: dict[str, Any] = {}
        if table_name:
            table = schema.get_table(table_name)
            if table is None:
                raise ValueError(f"Table not found: {table_name}")
            out["indexes"] = {table.name: [i.model_dump(mode="json") for i in table.indexes]}
        else:
            out["indexes"] = {
                t.name: [i.model_dump(mode="json") for i in t.indexes] for t in schema.tables
            }
        sql = args.get("sql")
        if sql:
            report = optimization_service.analyze(sql, schema)
            out["missing_indexes"] = report.missing_indexes
        return out

    registry.register(
        MCPTool(
            name="index_inspector",
            description="List indexes for a table (or all tables) and suggest missing indexes for a query.",
            input_schema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"},
                    "sql": {"type": "string", "description": "Optional SQL to analyse for missing indexes."},
                },
                "required": [],
            },
            handler=_index_inspector,
        )
    )

    # --- 6. Relationship Analyzer ----------------------------------------
    def _relationship_analyzer(_args: dict[str, Any]) -> dict[str, Any]:
        schema = get_schema()
        return {"relationships": query_service.relationships(schema)}

    registry.register(
        MCPTool(
            name="relationship_analyzer",
            description="Analyse explicit foreign keys and infer likely relationships between tables.",
            input_schema={"type": "object", "properties": {}, "required": []},
            handler=_relationship_analyzer,
        )
    )

    # --- 7. Statistics Collector -----------------------------------------
    def _statistics_collector(args: dict[str, Any]) -> dict[str, Any]:
        return query_service.statistics(args["table_name"])

    registry.register(
        MCPTool(
            name="statistics_collector",
            description="Collect descriptive statistics (min/max/mean/distinct/nulls) for a table.",
            input_schema={
                "type": "object",
                "properties": {"table_name": {"type": "string"}},
                "required": ["table_name"],
            },
            handler=_statistics_collector,
        )
    )

    # --- 8. CSV Export ---------------------------------------------------
    def _csv_export(args: dict[str, Any]) -> dict[str, Any]:
        result = repository.execute(args["sql"])
        data = export_service.to_csv(result, persist=True)
        return {
            "format": "csv",
            "row_count": result.row_count,
            "bytes": len(data),
            "content_base64": base64.b64encode(data).decode("ascii"),
        }

    registry.register(
        MCPTool(
            name="csv_export",
            description="Run a query and export the result set to CSV.",
            input_schema={
                "type": "object",
                "properties": {"sql": {"type": "string"}},
                "required": ["sql"],
            },
            handler=_csv_export,
        )
    )

    # --- 9. PDF Export ---------------------------------------------------
    def _pdf_export(args: dict[str, Any]) -> dict[str, Any]:
        result = repository.execute(args["sql"])
        title = args.get("title", "Database Report")
        body = args.get("report_markdown", "## Executive Summary\nAutomated export.")
        data = export_service.to_pdf(title, body, result=result, persist=True)
        return {
            "format": "pdf",
            "bytes": len(data),
            "content_base64": base64.b64encode(data).decode("ascii"),
        }

    registry.register(
        MCPTool(
            name="pdf_export",
            description="Run a query and export a PDF report including a data sample.",
            input_schema={
                "type": "object",
                "properties": {
                    "sql": {"type": "string"},
                    "title": {"type": "string", "default": "Database Report"},
                    "report_markdown": {"type": "string"},
                },
                "required": ["sql"],
            },
            handler=_pdf_export,
        )
    )

    # --- 10. Chart Generator ---------------------------------------------
    def _chart_generator(args: dict[str, Any]) -> dict[str, Any]:
        result = repository.execute(args["sql"])
        spec = chart_service.recommend(result)
        figure = chart_service.build_figure(result, spec)
        payload: dict[str, Any] = {"chart_spec": spec.model_dump(mode="json"), "row_count": result.row_count}
        if figure is not None and args.get("include_figure", False):
            payload["figure_json"] = figure.to_json()
        return payload

    registry.register(
        MCPTool(
            name="chart_generator",
            description="Run a query and recommend (optionally build) the best chart for the result.",
            input_schema={
                "type": "object",
                "properties": {
                    "sql": {"type": "string"},
                    "include_figure": {"type": "boolean", "default": False},
                },
                "required": ["sql"],
            },
            handler=_chart_generator,
        )
    )

    return registry
