"""Tests for the MCP tool registry and individual tools."""

from __future__ import annotations


def test_tools_listed(registry):
    names = {t["name"] for t in registry.list_tools()}
    expected = {
        "schema_reader",
        "table_inspector",
        "column_inspector",
        "sql_executor",
        "index_inspector",
        "relationship_analyzer",
        "statistics_collector",
        "csv_export",
        "pdf_export",
        "chart_generator",
    }
    assert expected.issubset(names)


def test_schema_reader_tool(registry):
    result = registry.call("schema_reader", {"include_row_counts": False})
    assert result.ok
    assert "tables" in result.data


def test_sql_executor_tool(registry):
    result = registry.call("sql_executor", {"sql": "SELECT COUNT(*) AS n FROM customers"})
    assert result.ok
    assert result.data["rows"][0][0] == 3


def test_sql_executor_blocks_write(registry):
    result = registry.call("sql_executor", {"sql": "DROP TABLE customers"})
    assert not result.ok
    assert "read-only" in (result.error or "").lower()


def test_column_inspector_keyword(registry):
    result = registry.call("column_inspector", {"keyword": "email"})
    assert result.ok
    assert any("email" in m for m in result.data["matches"])


def test_statistics_tool(registry):
    result = registry.call("statistics_collector", {"table_name": "orders"})
    assert result.ok
    assert result.data["row_sample"] == 4


def test_missing_required_argument(registry):
    result = registry.call("statistics_collector", {})
    assert not result.ok


def test_csv_export_tool(registry):
    result = registry.call("csv_export", {"sql": "SELECT * FROM customers"})
    assert result.ok
    assert result.data["format"] == "csv"
    assert result.data["bytes"] > 0


def test_chart_generator_tool(registry):
    result = registry.call(
        "chart_generator",
        {"sql": "SELECT country, COUNT(*) AS n FROM customers GROUP BY country"},
    )
    assert result.ok
    assert "chart_spec" in result.data
