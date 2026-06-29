"""Session memory.

Holds conversation history, previously generated SQL, previous results, the
schema cache, saved queries and recent connections for a single user session.
In Streamlit one instance of this lives in ``st.session_state``.
"""

from __future__ import annotations

from collections import deque
from typing import Optional

from core.models import (
    AnalysisResult,
    ChatMessage,
    ChatRole,
    QueryResult,
    SchemaInfo,
)


class SessionMemory:
    """In-memory store for everything the agent should remember in a session."""

    def __init__(self, max_history: int = 50) -> None:
        self.max_history = max_history
        self.messages: list[ChatMessage] = []
        self.schema_cache: Optional[SchemaInfo] = None
        self.last_sql: Optional[str] = None
        self.last_result: Optional[QueryResult] = None
        self.saved_queries: dict[str, str] = {}
        self.recent_connections: deque[dict[str, object]] = deque(maxlen=8)

    # --- Conversation -----------------------------------------------------
    def add_user_message(self, content: str) -> None:
        self.messages.append(ChatMessage(role=ChatRole.USER, content=content))
        self._trim()

    def add_assistant_message(
        self, content: str, analysis: Optional[AnalysisResult] = None
    ) -> None:
        self.messages.append(
            ChatMessage(role=ChatRole.ASSISTANT, content=content, analysis=analysis)
        )
        if analysis and analysis.result:
            self.last_sql = analysis.plan.sql
            self.last_result = analysis.result
        self._trim()

    def _trim(self) -> None:
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history :]

    def recent_dialogue(self, turns: int = 6) -> str:
        """Return the last few turns as plain text for prompt context."""
        recent = self.messages[-turns:]
        lines = []
        for msg in recent:
            who = "User" if msg.role == ChatRole.USER else "Assistant"
            lines.append(f"{who}: {msg.content}")
        return "\n".join(lines)

    def clear_conversation(self) -> None:
        self.messages.clear()
        self.last_sql = None
        self.last_result = None

    # --- Schema cache -----------------------------------------------------
    def set_schema(self, schema: SchemaInfo) -> None:
        self.schema_cache = schema

    def get_schema(self) -> Optional[SchemaInfo]:
        return self.schema_cache

    def invalidate_schema(self) -> None:
        self.schema_cache = None

    # --- Saved queries ----------------------------------------------------
    def save_query(self, name: str, sql: str) -> None:
        if name.strip() and sql.strip():
            self.saved_queries[name.strip()] = sql.strip()

    def delete_saved_query(self, name: str) -> None:
        self.saved_queries.pop(name, None)

    # --- Recent connections ----------------------------------------------
    def remember_connection(self, summary: dict[str, object]) -> None:
        # De-duplicate by display tuple.
        for existing in self.recent_connections:
            if existing == summary:
                return
        self.recent_connections.appendleft(summary)
