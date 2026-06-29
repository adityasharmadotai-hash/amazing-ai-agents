"""Repository pattern for database access.

The :class:`DatabaseRepository` is the single gateway through which the rest of
the application reads from / writes to the database. It enforces SQL safety,
parameterisation, result limits, timeouts and timing instrumentation.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from core.exceptions import QueryExecutionError, QueryTimeoutError
from core.logging_config import get_logger
from core.models import QueryResult, SchemaInfo
from database.connection import ConnectionManager
from database.safe_sql import SafeSQLGuard, SQLStatementType
from database.schema_inspector import SchemaInspector

logger = get_logger(__name__)


class DatabaseRepository:
    """High-level, safe data-access object."""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        guard: Optional[SafeSQLGuard] = None,
        max_result_rows: int = 10000,
    ) -> None:
        self._cm = connection_manager
        self.guard = guard or SafeSQLGuard(read_only=True)
        self.max_result_rows = max_result_rows
        self._inspector = SchemaInspector(self._cm.engine)

    @property
    def engine(self) -> Engine:
        return self._cm.engine

    @property
    def dialect(self) -> str:
        return self._cm.dialect

    # --- Schema -----------------------------------------------------------
    def get_schema(self, include_row_counts: bool = True) -> SchemaInfo:
        return self._inspector.inspect_schema(include_row_counts=include_row_counts)

    def find_tables_with_column(self, schema: SchemaInfo, keyword: str) -> list[str]:
        return self._inspector.find_tables_with_column(schema, keyword)

    # --- Execution --------------------------------------------------------
    def execute(
        self, sql: str, params: Optional[dict[str, Any]] = None
    ) -> QueryResult:
        """Validate and execute a SQL statement, returning a typed result.

        Parameters are bound safely (named ``:param`` style) to prevent SQL
        injection. Read-only statements are fetched; write statements (only
        permitted when write-mode is enabled) report affected rows.
        """
        stmt_type = self.guard.validate(sql)
        is_write = stmt_type in {
            SQLStatementType.INSERT,
            SQLStatementType.UPDATE,
            SQLStatementType.DELETE,
            SQLStatementType.CREATE,
            SQLStatementType.ALTER,
            SQLStatementType.DROP,
            SQLStatementType.TRUNCATE,
        }

        start = time.perf_counter()
        try:
            with self.engine.connect() as conn:
                self._apply_statement_timeout(conn)
                cursor = conn.execute(text(sql), params or {})

                if cursor.returns_rows:
                    columns = list(cursor.keys())
                    rows_raw = cursor.fetchmany(self.max_result_rows + 1)
                    truncated = len(rows_raw) > self.max_result_rows
                    rows = [list(r) for r in rows_raw[: self.max_result_rows]]
                    elapsed = (time.perf_counter() - start) * 1000
                    result = QueryResult(
                        sql=sql,
                        columns=columns,
                        rows=rows,
                        row_count=len(rows),
                        execution_time_ms=round(elapsed, 2),
                        truncated=truncated,
                        is_write=False,
                    )
                else:
                    conn.commit()
                    elapsed = (time.perf_counter() - start) * 1000
                    result = QueryResult(
                        sql=sql,
                        columns=[],
                        rows=[],
                        row_count=0,
                        execution_time_ms=round(elapsed, 2),
                        is_write=is_write,
                        affected_rows=cursor.rowcount,
                    )

            logger.info(
                "Executed SQL (%s) in %.2f ms, rows=%d",
                stmt_type.value,
                result.execution_time_ms,
                result.row_count,
            )
            return result

        except OperationalError as exc:
            message = str(exc.orig or exc).lower()
            if "timeout" in message or "cancel" in message:
                raise QueryTimeoutError(detail=str(exc.orig or exc)) from exc
            raise QueryExecutionError(detail=str(exc.orig or exc)) from exc
        except SQLAlchemyError as exc:
            raise QueryExecutionError(detail=str(exc)) from exc

    def _apply_statement_timeout(self, conn) -> None:
        """Best-effort per-statement timeout, dialect dependent."""
        timeout_s = self._cm.config.query_timeout
        try:
            if self.dialect == "postgresql":
                conn.execute(text(f"SET statement_timeout = {timeout_s * 1000}"))
            elif self.dialect == "mysql":
                conn.execute(text(f"SET SESSION MAX_EXECUTION_TIME = {timeout_s * 1000}"))
        except SQLAlchemyError:  # pragma: no cover - non-critical
            pass

    def explain(self, sql: str) -> QueryResult:
        """Return the database execution plan for a SELECT statement."""
        self.guard.validate(sql)  # ensure the underlying query is safe
        if self.dialect == "postgresql":
            plan_sql = f"EXPLAIN (FORMAT TEXT) {sql}"
        elif self.dialect == "mysql":
            plan_sql = f"EXPLAIN {sql}"
        elif self.dialect == "sqlite":
            plan_sql = f"EXPLAIN QUERY PLAN {sql}"
        else:  # duckdb and others
            plan_sql = f"EXPLAIN {sql}"

        start = time.perf_counter()
        try:
            with self.engine.connect() as conn:
                cursor = conn.execute(text(plan_sql))
                columns = list(cursor.keys())
                rows = [list(r) for r in cursor.fetchall()]
            elapsed = (time.perf_counter() - start) * 1000
            return QueryResult(
                sql=plan_sql,
                columns=columns,
                rows=rows,
                row_count=len(rows),
                execution_time_ms=round(elapsed, 2),
            )
        except SQLAlchemyError as exc:
            raise QueryExecutionError(detail=str(exc)) from exc

    def sample_rows(self, table_name: str, limit: int = 5) -> QueryResult:
        """Return a small sample of rows from a table (safe, parameterised limit)."""
        quoted = self.engine.dialect.identifier_preparer.quote(table_name)
        return self.execute(f"SELECT * FROM {quoted} LIMIT :limit", {"limit": int(limit)})
