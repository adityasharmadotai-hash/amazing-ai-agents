"""SQL formatting and summarising helpers."""

from __future__ import annotations

import sqlparse


def format_sql(sql: str) -> str:
    """Pretty-print a SQL statement for display."""
    if not sql:
        return ""
    return sqlparse.format(
        sql,
        reindent=True,
        keyword_case="upper",
        identifier_case=None,
        strip_comments=False,
    ).strip()


def summarise_sql(sql: str, max_length: int = 80) -> str:
    """Return a single-line, whitespace-collapsed summary of a query."""
    if not sql:
        return ""
    collapsed = " ".join(sql.split())
    if len(collapsed) <= max_length:
        return collapsed
    return collapsed[: max_length - 1] + "…"
