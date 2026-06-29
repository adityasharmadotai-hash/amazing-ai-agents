"""Pydantic data models shared across the application.

These models define the typed contracts that flow between the database layer,
the MCP tools, the AI agent and the UI.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    """Metadata describing a single database column."""

    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    default: Optional[str] = None
    autoincrement: bool = False


class ForeignKeyInfo(BaseModel):
    """A foreign-key relationship between two tables."""

    constrained_columns: list[str]
    referred_table: str
    referred_columns: list[str]


class IndexInfo(BaseModel):
    """An index defined on a table."""

    name: str
    column_names: list[str]
    unique: bool = False


class TableInfo(BaseModel):
    """Full metadata for a single table."""

    name: str
    columns: list[ColumnInfo] = Field(default_factory=list)
    primary_keys: list[str] = Field(default_factory=list)
    foreign_keys: list[ForeignKeyInfo] = Field(default_factory=list)
    indexes: list[IndexInfo] = Field(default_factory=list)
    row_count: Optional[int] = None
    comment: Optional[str] = None

    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]


class SchemaInfo(BaseModel):
    """A snapshot of the full database schema."""

    dialect: str
    tables: list[TableInfo] = Field(default_factory=list)
    collected_at: datetime = Field(default_factory=datetime.utcnow)

    def table_names(self) -> list[str]:
        return [t.name for t in self.tables]

    def get_table(self, name: str) -> Optional[TableInfo]:
        lname = name.lower()
        for table in self.tables:
            if table.name.lower() == lname:
                return table
        return None

    def to_prompt_text(self, max_tables: int = 60) -> str:
        """Render a compact textual schema description for the LLM prompt."""
        lines: list[str] = [f"Dialect: {self.dialect}", ""]
        for table in self.tables[:max_tables]:
            cols = ", ".join(
                f"{c.name} {c.type}{' PK' if c.primary_key else ''}"
                f"{'' if c.nullable else ' NOT NULL'}"
                for c in table.columns
            )
            rc = f" (~{table.row_count} rows)" if table.row_count is not None else ""
            lines.append(f"TABLE {table.name}{rc}: {cols}")
            for fk in table.foreign_keys:
                lines.append(
                    f"  FK {', '.join(fk.constrained_columns)} -> "
                    f"{fk.referred_table}({', '.join(fk.referred_columns)})"
                )
        return "\n".join(lines)


class QueryResult(BaseModel):
    """The result of executing a SQL statement."""

    sql: str
    columns: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    truncated: bool = False
    is_write: bool = False
    affected_rows: Optional[int] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def to_records(self) -> list[dict[str, Any]]:
        return [dict(zip(self.columns, row)) for row in self.rows]


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"
    TABLE = "table"


class ChartSpec(BaseModel):
    """Specification describing which chart to draw from a result set."""

    chart_type: ChartType = ChartType.BAR
    x: Optional[str] = None
    y: Optional[list[str]] = None
    color: Optional[str] = None
    title: str = "Chart"
    reason: str = ""


class QueryPlan(BaseModel):
    """The AI agent's plan for answering a natural-language question."""

    intent: str = ""
    relevant_tables: list[str] = Field(default_factory=list)
    sql: str = ""
    explanation: str = ""
    is_write: bool = False
    needs_confirmation: bool = False
    assumptions: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    """The fully assembled answer returned to the UI."""

    question: str
    plan: QueryPlan
    result: Optional[QueryResult] = None
    chart_spec: Optional[ChartSpec] = None
    insights: str = ""
    recommendations: list[str] = Field(default_factory=list)
    sql_explanation: str = ""
    error: Optional[str] = None


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    role: ChatRole
    content: str
    analysis: Optional[AnalysisResult] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
