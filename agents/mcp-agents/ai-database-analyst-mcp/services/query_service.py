"""Query service.

A thin orchestration layer over the repository that adds statistics collection
and relationship analysis used by the MCP tools and the AI agent.
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from core.logging_config import get_logger
from core.models import QueryResult, SchemaInfo
from database.repository import DatabaseRepository

logger = get_logger(__name__)


class QueryService:
    """Read-oriented query helpers built on top of the repository."""

    def __init__(self, repository: DatabaseRepository) -> None:
        self.repo = repository

    def run(self, sql: str, params: Optional[dict[str, Any]] = None) -> QueryResult:
        return self.repo.execute(sql, params)

    def statistics(self, table_name: str, max_columns: int = 40) -> dict[str, Any]:
        """Collect descriptive statistics for a table using a row sample."""
        quoted = self.repo.engine.dialect.identifier_preparer.quote(table_name)
        result = self.repo.execute(f"SELECT * FROM {quoted} LIMIT 5000")
        df = pd.DataFrame(result.rows, columns=result.columns)
        if df.empty:
            return {"table": table_name, "row_sample": 0, "columns": {}}

        stats: dict[str, Any] = {
            "table": table_name,
            "row_sample": len(df),
            "columns": {},
        }
        for col in df.columns[:max_columns]:
            series = df[col]
            col_stats: dict[str, Any] = {
                "dtype": str(series.dtype),
                "non_null": int(series.notna().sum()),
                "nulls": int(series.isna().sum()),
                "distinct": int(series.nunique(dropna=True)),
            }
            if pd.api.types.is_numeric_dtype(series):
                described = series.describe()
                col_stats.update(
                    {
                        "min": _num(described.get("min")),
                        "max": _num(described.get("max")),
                        "mean": _num(described.get("mean")),
                        "std": _num(described.get("std")),
                        "median": _num(series.median()),
                    }
                )
            else:
                top = series.dropna().astype(str).value_counts().head(5)
                col_stats["top_values"] = {str(k): int(v) for k, v in top.items()}
            stats["columns"][col] = col_stats
        return stats

    def relationships(self, schema: SchemaInfo) -> list[dict[str, Any]]:
        """Return explicit foreign-key relationships plus inferred ones.

        Inferred relationships are heuristics where a column named like
        ``<table>_id`` or ``<table>id`` matches another table's primary key.
        """
        relationships: list[dict[str, Any]] = []

        # Explicit FK relationships.
        for table in schema.tables:
            for fk in table.foreign_keys:
                relationships.append(
                    {
                        "type": "explicit",
                        "from_table": table.name,
                        "from_columns": fk.constrained_columns,
                        "to_table": fk.referred_table,
                        "to_columns": fk.referred_columns,
                    }
                )

        # Inferred relationships by naming convention.
        pk_index = {
            t.name.lower(): (t.name, t.primary_keys[0] if t.primary_keys else None)
            for t in schema.tables
        }
        explicit_pairs = {
            (r["from_table"], tuple(r["from_columns"])) for r in relationships
        }
        for table in schema.tables:
            for col in table.columns:
                lname = col.name.lower()
                if not lname.endswith("id") or lname == "id":
                    continue
                base = lname[:-2].rstrip("_")
                candidates = [base, base + "s", base.rstrip("s")]
                for cand in candidates:
                    if cand in pk_index and pk_index[cand][0].lower() != table.name.lower():
                        target_name, target_pk = pk_index[cand]
                        if target_pk and (table.name, (col.name,)) not in explicit_pairs:
                            relationships.append(
                                {
                                    "type": "inferred",
                                    "from_table": table.name,
                                    "from_columns": [col.name],
                                    "to_table": target_name,
                                    "to_columns": [target_pk],
                                }
                            )
                        break
        return relationships


def _num(value: Any) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return None
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None
