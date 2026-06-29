"""Database connection management.

Wraps SQLAlchemy engine creation with connection pooling, validation,
timeouts and automatic reconnect (``pool_pre_ping``). One ``ConnectionManager``
owns a single engine for a single :class:`ConnectionConfig`.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.pool import QueuePool, StaticPool

from core.config import ConnectionConfig, DatabaseType
from core.exceptions import (
    AuthenticationError,
    ConnectionTimeoutError,
    DBConnectionError,
)
from core.logging_config import get_logger

logger = get_logger(__name__)

# Substrings that hint the failure is an authentication problem.
_AUTH_HINTS = ("access denied", "authentication failed", "password", "auth")
_TIMEOUT_HINTS = ("timeout", "timed out", "could not connect", "connection refused")


class ConnectionManager:
    """Owns a SQLAlchemy engine and its lifecycle for one configuration."""

    def __init__(self, config: ConnectionConfig) -> None:
        self.config = config
        self._engine: Optional[Engine] = None

    # --- Engine lifecycle -------------------------------------------------
    def _build_engine(self) -> Engine:
        url = self.config.build_url()
        connect_args: dict[str, object] = {}
        engine_kwargs: dict[str, object] = {
            "pool_pre_ping": True,  # automatic reconnect / liveness check
            "future": True,
            "echo": False,
        }

        if self.config.db_type == DatabaseType.SQLITE:
            # SQLite needs special pooling; allow cross-thread use for Streamlit.
            connect_args["check_same_thread"] = False
            connect_args["timeout"] = self.config.connect_timeout
            if self.config.database in ("", ":memory:"):
                engine_kwargs["poolclass"] = StaticPool
        elif self.config.db_type == DatabaseType.DUCKDB:
            engine_kwargs["poolclass"] = QueuePool
            engine_kwargs["pool_size"] = self.config.pool_size
            engine_kwargs["max_overflow"] = self.config.max_overflow
            engine_kwargs["pool_timeout"] = self.config.pool_timeout
        else:
            engine_kwargs["poolclass"] = QueuePool
            engine_kwargs["pool_size"] = self.config.pool_size
            engine_kwargs["max_overflow"] = self.config.max_overflow
            engine_kwargs["pool_timeout"] = self.config.pool_timeout
            engine_kwargs["pool_recycle"] = 1800
            if self.config.db_type == DatabaseType.MYSQL:
                connect_args["connect_timeout"] = self.config.connect_timeout
            elif self.config.db_type == DatabaseType.POSTGRESQL:
                connect_args["connect_timeout"] = self.config.connect_timeout

        if connect_args:
            engine_kwargs["connect_args"] = connect_args

        logger.info(
            "Creating engine for %s", self.config.safe_summary()
        )
        return create_engine(url, **engine_kwargs)

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = self._build_engine()
        return self._engine

    def connect(self) -> Engine:
        """Create the engine and validate the connection. Raises on failure."""
        self._engine = self._build_engine()
        self.validate()
        return self._engine

    def validate(self) -> bool:
        """Run a trivial query to verify the connection works.

        Translates SQLAlchemy errors into friendly application exceptions.
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Connection validated: %s", self.config.display_name())
            return True
        except OperationalError as exc:
            message = str(exc.orig or exc).lower()
            if any(h in message for h in _AUTH_HINTS):
                raise AuthenticationError(detail=str(exc.orig or exc)) from exc
            if any(h in message for h in _TIMEOUT_HINTS):
                raise ConnectionTimeoutError(detail=str(exc.orig or exc)) from exc
            raise DBConnectionError(detail=str(exc.orig or exc)) from exc
        except SQLAlchemyError as exc:
            raise DBConnectionError(detail=str(exc)) from exc

    def dispose(self) -> None:
        """Close all pooled connections and drop the engine."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            logger.info("Engine disposed for %s", self.config.display_name())

    @property
    def dialect(self) -> str:
        return self.engine.dialect.name
