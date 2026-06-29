"""Schema inspection.

Uses SQLAlchemy's ``Inspector`` to read tables, columns, primary/foreign keys,
indexes and (approximate) row counts. Results are returned as typed
:class:`SchemaInfo` models and can be cached in session memory.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from core.logging_config import get_logger
from core.models import (
    ColumnInfo,
    ForeignKeyInfo,
    IndexInfo,
    SchemaInfo,
    TableInfo,
)

logger = get_logger(__name__)


class SchemaInspector:
    """Reads structural metadata from a live database engine."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def inspect_schema(self, include_row_counts: bool = True) -> SchemaInfo:
        """Return the full schema of the connected database."""
        inspector = inspect(self.engine)
        dialect = self.engine.dialect.name
        tables: list[TableInfo] = []

        for table_name in inspector.get_table_names():
            try:
                tables.append(
                    self._inspect_table(
                        inspector, table_name, include_row_counts=include_row_counts
                    )
                )
            except SQLAlchemyError as exc:  # pragma: no cover - defensive
                logger.warning("Failed to inspect table %s: %s", table_name, exc)

        # Include views as read-only tables (no row counts).
        try:
            for view_name in inspector.get_view_names():
                tables.append(
                    self._inspect_table(inspector, view_name, include_row_counts=False)
                )
        except (SQLAlchemyError, NotImplementedError):  # pragma: no cover
            pass

        schema = SchemaInfo(dialect=dialect, tables=tables)
        logger.info(
            "Inspected schema: %d tables (dialect=%s)", len(tables), dialect
        )
        return schema

    def _inspect_table(
        self, inspector, table_name: str, include_row_counts: bool
    ) -> TableInfo:
        columns: list[ColumnInfo] = []
        pk = inspector.get_pk_constraint(table_name) or {}
        pk_cols = set(pk.get("constrained_columns") or [])

        for col in inspector.get_columns(table_name):
            columns.append(
                ColumnInfo(
                    name=col["name"],
                    type=str(col.get("type", "")),
                    nullable=bool(col.get("nullable", True)),
                    primary_key=col["name"] in pk_cols,
                    default=None if col.get("default") is None else str(col.get("default")),
                    autoincrement=bool(col.get("autoincrement", False)),
                )
            )

        foreign_keys = [
            ForeignKeyInfo(
                constrained_columns=fk.get("constrained_columns", []),
                referred_table=fk.get("referred_table", ""),
                referred_columns=fk.get("referred_columns", []),
            )
            for fk in inspector.get_foreign_keys(table_name)
        ]

        indexes = [
            IndexInfo(
                name=idx.get("name") or "",
                column_names=[c for c in (idx.get("column_names") or []) if c],
                unique=bool(idx.get("unique", False)),
            )
            for idx in inspector.get_indexes(table_name)
        ]

        row_count: Optional[int] = None
        if include_row_counts:
            row_count = self._safe_row_count(table_name)

        return TableInfo(
            name=table_name,
            columns=columns,
            primary_keys=sorted(pk_cols),
            foreign_keys=foreign_keys,
            indexes=indexes,
            row_count=row_count,
        )

    def _safe_row_count(self, table_name: str) -> Optional[int]:
        """Return an exact row count, or None if it cannot be obtained."""
        try:
            with self.engine.connect() as conn:
                quoted = self.engine.dialect.identifier_preparer.quote(table_name)
                result = conn.execute(text(f"SELECT COUNT(*) FROM {quoted}"))
                return int(result.scalar() or 0)
        except SQLAlchemyError:
            return None

    def find_tables_with_column(self, schema: SchemaInfo, keyword: str) -> list[str]:
        """Return tables that contain a column whose name matches ``keyword``."""
        kw = keyword.lower()
        matches = []
        for table in schema.tables:
            for col in table.columns:
                if kw in col.name.lower():
                    matches.append(f"{table.name}.{col.name}")
        return matches
