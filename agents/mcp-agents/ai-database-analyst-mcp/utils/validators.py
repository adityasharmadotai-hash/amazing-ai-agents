"""Input validation helpers.

Validates user-supplied connection details and SQL identifiers to prevent
malformed input and identifier-based injection.
"""

from __future__ import annotations

import re

from core.config import DatabaseType
from core.exceptions import ValidationError

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


def validate_identifier(name: str) -> str:
    """Validate a SQL identifier (table/column). Raises on invalid input."""
    if not name or not _IDENTIFIER_RE.match(name):
        raise ValidationError(f"Invalid SQL identifier: {name!r}")
    return name


def validate_connection_input(
    db_type: str,
    host: str,
    port: object,
    username: str,
    database: str,
) -> list[str]:
    """Validate connection form input; return a list of human-readable errors."""
    errors: list[str] = []
    try:
        dbt = DatabaseType.from_str(db_type)
    except ValueError:
        return [f"Unsupported database type: {db_type}"]

    if dbt in (DatabaseType.SQLITE, DatabaseType.DUCKDB):
        if not database or not str(database).strip():
            errors.append("A database file path is required for file-based databases.")
    else:
        if not host or not str(host).strip():
            errors.append("Host is required.")
        if not database or not str(database).strip():
            errors.append("Database name is required.")
        if not username or not str(username).strip():
            errors.append("Username is required.")
        if port not in (None, "", 0):
            try:
                p = int(port)
                if not (1 <= p <= 65535):
                    errors.append("Port must be between 1 and 65535.")
            except (TypeError, ValueError):
                errors.append("Port must be a number.")
    return errors
