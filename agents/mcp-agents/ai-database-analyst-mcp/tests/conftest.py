"""Shared pytest fixtures.

Builds an in-memory SQLite database with a tiny schema + data, and wires up the
repository, services and MCP registry against it — no network or API key
required.
"""

from __future__ import annotations

import os
import sys

import pytest

# Make the project root importable.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.config import ConnectionConfig, DatabaseType  # noqa: E402
from database.connection import ConnectionManager  # noqa: E402
from database.repository import DatabaseRepository  # noqa: E402
from database.safe_sql import SafeSQLGuard  # noqa: E402
from mcp.tools import build_registry  # noqa: E402
from services.chart_service import ChartService  # noqa: E402
from services.export_service import ExportService  # noqa: E402
from services.optimization_service import OptimizationService  # noqa: E402
from services.query_service import QueryService  # noqa: E402


@pytest.fixture()
def connection_manager() -> ConnectionManager:
    config = ConnectionConfig(db_type=DatabaseType.SQLITE, database=":memory:")
    cm = ConnectionManager(config)
    cm.connect()
    from sqlalchemy import text

    with cm.engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE customers ("
                "id INTEGER PRIMARY KEY, name TEXT, email TEXT, country TEXT)"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE orders ("
                "id INTEGER PRIMARY KEY, customer_id INTEGER, amount REAL, "
                "FOREIGN KEY(customer_id) REFERENCES customers(id))"
            )
        )
        conn.execute(
            text("INSERT INTO customers VALUES (1,'Alice','a@x.com','USA'), "
                 "(2,'Bob','b@x.com','UK'), (3,'Carla','c@x.com','USA')")
        )
        conn.execute(
            text("INSERT INTO orders VALUES (1,1,100.0),(2,1,50.0),(3,2,75.0),(4,3,20.0)")
        )
    yield cm
    cm.dispose()


@pytest.fixture()
def repository(connection_manager) -> DatabaseRepository:
    guard = SafeSQLGuard(read_only=True)
    return DatabaseRepository(connection_manager, guard=guard, max_result_rows=1000)


@pytest.fixture()
def registry(repository):
    return build_registry(
        repository=repository,
        query_service=QueryService(repository),
        chart_service=ChartService(theme="plotly"),
        export_service=ExportService(export_dir="exports"),
        optimization_service=OptimizationService(repository),
    )
