"""Application configuration using Pydantic settings.

All configuration is centralised here. Settings are loaded from environment
variables (and an optional ``.env`` file) and exposed through strongly-typed,
validated Pydantic models. Never hard-code secrets — they always come from the
environment.
"""

from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from typing import Optional
from urllib.parse import quote_plus

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseType(str, Enum):
    """Supported database backends."""

    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    DUCKDB = "duckdb"

    @classmethod
    def from_str(cls, value: str) -> "DatabaseType":
        normalised = (value or "").strip().lower()
        aliases = {
            "postgres": cls.POSTGRESQL,
            "psql": cls.POSTGRESQL,
            "pg": cls.POSTGRESQL,
            "maria": cls.MYSQL,
            "mariadb": cls.MYSQL,
            "duck": cls.DUCKDB,
        }
        if normalised in aliases:
            return aliases[normalised]
        return cls(normalised)


# Default network ports per database type.
DEFAULT_PORTS: dict[DatabaseType, int] = {
    DatabaseType.MYSQL: 3306,
    DatabaseType.POSTGRESQL: 5432,
    DatabaseType.SQLITE: 0,
    DatabaseType.DUCKDB: 0,
}


class ConnectionConfig(BaseSettings):
    """Connection parameters for a single database.

    File-based databases (SQLite, DuckDB) only require ``database`` (a path).
    Server-based databases (MySQL, PostgreSQL) require host/port/credentials.
    """

    db_type: DatabaseType = Field(default=DatabaseType.SQLITE)
    host: str = Field(default="localhost")
    port: Optional[int] = Field(default=None)
    username: str = Field(default="")
    password: SecretStr = Field(default=SecretStr(""))
    database: str = Field(default="")

    # Engine tuning
    pool_size: int = Field(default=5, ge=1, le=50)
    max_overflow: int = Field(default=10, ge=0, le=100)
    pool_timeout: int = Field(default=30, ge=1)
    connect_timeout: int = Field(default=10, ge=1)
    query_timeout: int = Field(default=30, ge=1)

    model_config = SettingsConfigDict(extra="ignore")

    @field_validator("db_type", mode="before")
    @classmethod
    def _coerce_db_type(cls, value: object) -> object:
        if isinstance(value, str):
            return DatabaseType.from_str(value)
        return value

    @model_validator(mode="after")
    def _apply_default_port(self) -> "ConnectionConfig":
        if self.port in (None, 0) and self.db_type in (DatabaseType.MYSQL, DatabaseType.POSTGRESQL):
            object.__setattr__(self, "port", DEFAULT_PORTS[self.db_type])
        return self

    @property
    def is_file_based(self) -> bool:
        return self.db_type in (DatabaseType.SQLITE, DatabaseType.DUCKDB)

    def build_url(self) -> str:
        """Return a SQLAlchemy connection URL for this configuration.

        Passwords are URL-encoded; the resulting URL is suitable for
        ``sqlalchemy.create_engine``. Never log this value.
        """
        pwd = quote_plus(self.password.get_secret_value()) if self.password else ""
        user = quote_plus(self.username) if self.username else ""

        if self.db_type == DatabaseType.SQLITE:
            path = self.database or ":memory:"
            return f"sqlite:///{path}"

        if self.db_type == DatabaseType.DUCKDB:
            path = self.database or ":memory:"
            return f"duckdb:///{path}"

        if self.db_type == DatabaseType.MYSQL:
            return (
                f"mysql+pymysql://{user}:{pwd}@{self.host}:{self.port}/"
                f"{self.database}?charset=utf8mb4"
            )

        if self.db_type == DatabaseType.POSTGRESQL:
            return f"postgresql+psycopg2://{user}:{pwd}@{self.host}:{self.port}/{self.database}"

        raise ValueError(f"Unsupported database type: {self.db_type}")

    def safe_summary(self) -> dict[str, object]:
        """Return a dict describing the connection WITHOUT the password."""
        return {
            "db_type": self.db_type.value,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "database": self.database,
        }

    def display_name(self) -> str:
        if self.is_file_based:
            name = os.path.basename(self.database) or self.database or ":memory:"
            return f"{self.db_type.value}: {name}"
        return f"{self.db_type.value}://{self.host}:{self.port}/{self.database}"


class AppSettings(BaseSettings):
    """Top-level application settings, loaded from environment / .env."""

    # --- Gemini ---
    gemini_api_key: SecretStr = Field(default=SecretStr(""), alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")
    gemini_temperature: float = Field(default=0.2, ge=0.0, le=2.0, alias="GEMINI_TEMPERATURE")
    gemini_max_tokens: int = Field(default=4096, ge=256, le=32768, alias="GEMINI_MAX_TOKENS")

    # --- Default DB connection ---
    db_type: str = Field(default="sqlite", alias="DB_TYPE")
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: Optional[int] = Field(default=None, alias="DB_PORT")
    db_user: str = Field(default="", alias="DB_USER")
    db_password: SecretStr = Field(default=SecretStr(""), alias="DB_PASSWORD")
    db_name: str = Field(default="sample_data/northwind.db", alias="DB_NAME")

    # --- Safety ---
    read_only_mode: bool = Field(default=True, alias="READ_ONLY_MODE")

    # --- Engine ---
    pool_size: int = Field(default=5, alias="POOL_SIZE")
    max_overflow: int = Field(default=10, alias="MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, alias="POOL_TIMEOUT")
    connect_timeout: int = Field(default=10, alias="CONNECT_TIMEOUT")
    query_timeout: int = Field(default=30, alias="QUERY_TIMEOUT")
    max_result_rows: int = Field(default=10000, alias="MAX_RESULT_ROWS")

    # --- UI / behaviour ---
    app_theme: str = Field(default="dark", alias="APP_THEME")
    chart_theme: str = Field(default="plotly_dark", alias="CHART_THEME")
    auto_explain_sql: bool = Field(default=True, alias="AUTO_EXPLAIN_SQL")
    auto_generate_charts: bool = Field(default=True, alias="AUTO_GENERATE_CHARTS")

    # --- Paths / logging ---
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    export_dir: str = Field(default="exports", alias="EXPORT_DIR")
    log_dir: str = Field(default="logs", alias="LOG_DIR")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    def default_connection(self) -> ConnectionConfig:
        """Build a ``ConnectionConfig`` from the default DB env settings."""
        return ConnectionConfig(
            db_type=DatabaseType.from_str(self.db_type),
            host=self.db_host,
            port=self.db_port,
            username=self.db_user,
            password=self.db_password,
            database=self.db_name,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            connect_timeout=self.connect_timeout,
            query_timeout=self.query_timeout,
        )

    def has_gemini_key(self) -> bool:
        return bool(self.gemini_api_key.get_secret_value().strip())


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return a cached singleton of the application settings."""
    return AppSettings()
