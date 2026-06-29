"""SQL safety guard.

Enforces read-only mode by default. Dangerous statements (DROP, DELETE,
TRUNCATE, ALTER, UPDATE, INSERT, ...) are blocked unless write-mode is
explicitly enabled. Also guards against multi-statement injection attempts.
"""

from __future__ import annotations

import re
from enum import Enum

import sqlparse

from core.exceptions import UnsafeSQLError


class SQLStatementType(str, Enum):
    """Classification of a SQL statement."""

    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    DROP = "DROP"
    TRUNCATE = "TRUNCATE"
    ALTER = "ALTER"
    CREATE = "CREATE"
    EXPLAIN = "EXPLAIN"
    PRAGMA = "PRAGMA"
    SHOW = "SHOW"
    WITH = "WITH"
    UNKNOWN = "UNKNOWN"


# Statements considered read-only / always safe to run automatically.
READ_ONLY_TYPES: frozenset[SQLStatementType] = frozenset(
    {
        SQLStatementType.SELECT,
        SQLStatementType.EXPLAIN,
        SQLStatementType.PRAGMA,
        SQLStatementType.SHOW,
        SQLStatementType.WITH,
    }
)

# Statements that mutate data or schema — blocked in read-only mode.
WRITE_TYPES: frozenset[SQLStatementType] = frozenset(
    {
        SQLStatementType.INSERT,
        SQLStatementType.UPDATE,
        SQLStatementType.DELETE,
        SQLStatementType.DROP,
        SQLStatementType.TRUNCATE,
        SQLStatementType.ALTER,
        SQLStatementType.CREATE,
    }
)

# Keywords that are dangerous regardless of position (defence in depth).
_DANGEROUS_KEYWORDS = re.compile(
    r"\b(DROP|TRUNCATE|ALTER|GRANT|REVOKE|ATTACH|DETACH)\b", re.IGNORECASE
)


class SafeSQLGuard:
    """Validates SQL statements against the configured safety policy."""

    def __init__(self, read_only: bool = True) -> None:
        self.read_only = read_only

    def set_read_only(self, read_only: bool) -> None:
        self.read_only = read_only

    @staticmethod
    def strip_comments(sql: str) -> str:
        """Remove SQL comments so they cannot hide dangerous statements."""
        return sqlparse.format(sql, strip_comments=True).strip()

    @staticmethod
    def split_statements(sql: str) -> list[str]:
        """Split a SQL string into individual non-empty statements."""
        parts = sqlparse.split(sql)
        return [p.strip().rstrip(";").strip() for p in parts if p.strip().rstrip(";").strip()]

    @staticmethod
    def classify(statement: str) -> SQLStatementType:
        """Return the statement type for a single statement."""
        cleaned = SafeSQLGuard.strip_comments(statement).lstrip("(").strip()
        if not cleaned:
            return SQLStatementType.UNKNOWN
        first = cleaned.split(None, 1)[0].upper()
        mapping = {item.value: item for item in SQLStatementType}
        return mapping.get(first, SQLStatementType.UNKNOWN)

    def is_write(self, sql: str) -> bool:
        """Return True if any statement in ``sql`` mutates data/schema."""
        for stmt in self.split_statements(sql):
            if self.classify(stmt) in WRITE_TYPES:
                return True
        return False

    def validate(self, sql: str) -> SQLStatementType:
        """Validate a SQL string for execution.

        Returns the primary statement type when allowed, raises
        :class:`UnsafeSQLError` otherwise.
        """
        if not sql or not sql.strip():
            raise UnsafeSQLError("Empty SQL statement.")

        statements = self.split_statements(sql)
        if not statements:
            raise UnsafeSQLError("No executable SQL statement found.")

        if len(statements) > 1:
            # Allow multiple statements only if ALL are read-only and write
            # mode is off; otherwise this looks like an injection attempt.
            non_read = [
                s for s in statements if self.classify(s) not in READ_ONLY_TYPES
            ]
            if non_read:
                raise UnsafeSQLError(
                    "Multiple statements containing non-read operations are not allowed.",
                    detail=f"{len(statements)} statements detected",
                )

        primary = self.classify(statements[0])

        # Defence-in-depth keyword scan (catches obfuscated DDL).
        if self.read_only and _DANGEROUS_KEYWORDS.search(self.strip_comments(sql)):
            raise UnsafeSQLError(
                "This statement contains a destructive keyword and is blocked in read-only mode.",
                detail="enable write mode to run it",
            )

        if primary in WRITE_TYPES and self.read_only:
            raise UnsafeSQLError(
                f"{primary.value} statements are blocked in read-only mode. "
                "Enable write mode in Settings to run them.",
                detail=primary.value,
            )

        if primary == SQLStatementType.UNKNOWN:
            raise UnsafeSQLError(
                "Could not classify the statement; it is blocked for safety.",
            )

        return primary
