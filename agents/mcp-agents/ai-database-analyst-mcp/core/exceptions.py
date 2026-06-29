"""Custom exception hierarchy for the AI Database Analyst application.

A single, well-defined hierarchy lets the UI and service layers catch broad or
narrow categories of failure and present friendly, actionable messages to the
user instead of leaking raw tracebacks.
"""

from __future__ import annotations


class DatabaseAnalystError(Exception):
    """Base class for every error raised by this application."""

    #: Human-friendly default message shown to end users.
    default_message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        self.message = message or self.default_message
        self.detail = detail
        super().__init__(self.message)

    def __str__(self) -> str:  # pragma: no cover - trivial
        if self.detail:
            return f"{self.message} ({self.detail})"
        return self.message


class DBConnectionError(DatabaseAnalystError):
    """Raised when the application cannot connect to the target database."""

    default_message = "Could not connect to the database."


class ConnectionTimeoutError(DBConnectionError):
    """Raised when establishing a connection exceeds the configured timeout."""

    default_message = "The database connection timed out."


class AuthenticationError(DBConnectionError):
    """Raised when the database rejects the supplied credentials."""

    default_message = "Authentication failed for the database."


class QueryExecutionError(DatabaseAnalystError):
    """Raised when a SQL statement fails to execute."""

    default_message = "The SQL query failed to execute."


class QueryTimeoutError(QueryExecutionError):
    """Raised when a query exceeds the configured execution timeout."""

    default_message = "The query took too long and was cancelled."


class UnsafeSQLError(DatabaseAnalystError):
    """Raised when a statement is blocked by the safety guard."""

    default_message = "This statement was blocked because it is not allowed in read-only mode."


class AIAgentError(DatabaseAnalystError):
    """Raised when the LLM agent fails (generation, parsing, rate limits...)."""

    default_message = "The AI agent could not complete the request."


class RateLimitError(AIAgentError):
    """Raised when the LLM provider returns a rate-limit response."""

    default_message = "The AI provider rate limit was reached. Please retry shortly."


class ExportError(DatabaseAnalystError):
    """Raised when an export (CSV/Excel/PDF/...) fails."""

    default_message = "The export could not be generated."


class ValidationError(DatabaseAnalystError):
    """Raised when user-supplied input fails validation."""

    default_message = "The supplied input is invalid."
