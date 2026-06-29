"""SQL optimisation service.

Performs static analysis of SQL queries and the live schema to suggest indexes,
JOIN improvements, query simplifications and performance warnings, and to read
the database execution plan.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import sqlparse

from core.logging_config import get_logger
from core.models import QueryResult, SchemaInfo
from database.repository import DatabaseRepository

logger = get_logger(__name__)


@dataclass
class OptimizationReport:
    """Structured optimisation findings for a query."""

    suggestions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_indexes: list[str] = field(default_factory=list)
    execution_plan: Optional[QueryResult] = None

    def is_empty(self) -> bool:
        return not (self.suggestions or self.warnings or self.missing_indexes)


# Columns/identifiers referenced after WHERE/JOIN/ON clauses.
_WHERE_COL = re.compile(r"\bWHERE\b(.+?)(?:\bGROUP\b|\bORDER\b|\bLIMIT\b|$)", re.IGNORECASE | re.DOTALL)
_JOIN_ON = re.compile(r"\bON\b(.+?)(?:\bWHERE\b|\bGROUP\b|\bJOIN\b|\bLIMIT\b|$)", re.IGNORECASE | re.DOTALL)
_COL_REF = re.compile(r"([A-Za-z_][\w]*)\.([A-Za-z_][\w]*)")
_BARE_COL = re.compile(
    r"\b([A-Za-z_][\w]*)\s*(?:>=|<=|<>|!=|=|>|<|\bLIKE\b|\bIN\b)", re.IGNORECASE
)
# SQL keywords that must never be treated as column names.
_SQL_KEYWORDS = {
    "and", "or", "not", "where", "select", "from", "group", "order", "by",
    "having", "limit", "offset", "join", "on", "as", "in", "like", "between",
    "is", "null", "asc", "desc", "case", "when", "then", "else", "end",
}


class OptimizationService:
    """Static + plan-based SQL optimisation advisor."""

    def __init__(self, repository: DatabaseRepository) -> None:
        self.repo = repository

    def analyze(self, sql: str, schema: Optional[SchemaInfo] = None) -> OptimizationReport:
        report = OptimizationReport()
        normalised = sqlparse.format(sql, keyword_case="upper", strip_comments=True)
        upper = normalised.upper()

        self._check_select_star(upper, report)
        self._check_limit(upper, report)
        self._check_leading_wildcard(normalised, report)
        self._check_functions_on_columns(normalised, report)
        self._check_cartesian_join(upper, report)
        self._check_distinct(upper, report)
        self._check_or_conditions(upper, report)

        if schema is not None:
            self._suggest_indexes(normalised, schema, report)

        # Try to fetch the real execution plan.
        try:
            report.execution_plan = self.repo.explain(sql)
        except Exception as exc:  # noqa: BLE001 - plan is best-effort
            logger.debug("EXPLAIN failed: %s", exc)

        if report.is_empty():
            report.suggestions.append("No obvious issues found — the query looks reasonable.")
        return report

    # --- individual checks -----------------------------------------------
    def _check_select_star(self, upper: str, report: OptimizationReport) -> None:
        if re.search(r"SELECT\s+\*", upper):
            report.suggestions.append(
                "Avoid SELECT * — list only the columns you need to reduce I/O and "
                "make the query intent explicit."
            )

    def _check_limit(self, upper: str, report: OptimizationReport) -> None:
        if upper.strip().startswith("SELECT") and "LIMIT" not in upper and "COUNT(" not in upper:
            report.warnings.append(
                "No LIMIT clause — this query may return a very large result set."
            )

    def _check_leading_wildcard(self, sql: str, report: OptimizationReport) -> None:
        if re.search(r"LIKE\s+'%", sql, re.IGNORECASE):
            report.warnings.append(
                "Leading-wildcard LIKE ('%term') cannot use an index and forces a full scan."
            )

    def _check_functions_on_columns(self, sql: str, report: OptimizationReport) -> None:
        if re.search(r"WHERE[^;]*\b(LOWER|UPPER|DATE|CAST|SUBSTR)\s*\(", sql, re.IGNORECASE):
            report.suggestions.append(
                "Applying functions to columns in WHERE prevents index use; consider a "
                "functional index or rewriting the predicate."
            )

    def _check_cartesian_join(self, upper: str, report: OptimizationReport) -> None:
        join_count = upper.count(" JOIN ")
        on_count = upper.count(" ON ")
        if join_count and on_count < join_count:
            report.warnings.append(
                "A JOIN appears to be missing an ON condition — verify you are not "
                "producing a Cartesian product."
            )
        if re.search(r"FROM\s+\w+\s*,\s*\w+", upper):
            report.suggestions.append(
                "Comma-style joins detected; prefer explicit JOIN ... ON syntax for clarity "
                "and to avoid accidental cross joins."
            )

    def _check_distinct(self, upper: str, report: OptimizationReport) -> None:
        if "SELECT DISTINCT" in upper:
            report.suggestions.append(
                "DISTINCT can be expensive — confirm duplicates are not caused by a missing "
                "JOIN condition before relying on it."
            )

    def _check_or_conditions(self, upper: str, report: OptimizationReport) -> None:
        if re.search(r"WHERE[^;]*\bOR\b", upper):
            report.suggestions.append(
                "OR conditions can defeat indexes; consider UNION of indexed queries or an "
                "IN (...) list where applicable."
            )

    def _suggest_indexes(self, sql: str, schema: SchemaInfo, report: OptimizationReport) -> None:
        """Suggest indexes for columns used in WHERE / JOIN that are not indexed."""
        candidate_cols: set[tuple[str, str]] = set()

        for match in _WHERE_COL.finditer(sql):
            self._collect_columns(match.group(1), schema, candidate_cols)
        for match in _JOIN_ON.finditer(sql):
            self._collect_columns(match.group(1), schema, candidate_cols)

        for table_name, column in sorted(candidate_cols):
            table = schema.get_table(table_name)
            if not table:
                continue
            indexed = {
                c for idx in table.indexes for c in idx.column_names
            } | set(table.primary_keys)
            if column not in indexed:
                report.missing_indexes.append(
                    f"CREATE INDEX idx_{table_name}_{column} ON {table_name} ({column});"
                )

    def _collect_columns(
        self, clause: str, schema: SchemaInfo, out: set[tuple[str, str]]
    ) -> None:
        # Qualified columns: alias.column or table.column
        for _, col in _COL_REF.findall(clause):
            for table in schema.tables:
                if col in table.column_names():
                    out.add((table.name, col))
        # Bare columns compared against something.
        for col in _BARE_COL.findall(clause):
            if col.lower() in _SQL_KEYWORDS:
                continue
            for table in schema.tables:
                if col in table.column_names():
                    out.add((table.name, col))
