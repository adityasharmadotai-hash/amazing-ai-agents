"""Sidebar: database connection, recent connections and saved queries."""

from __future__ import annotations

from typing import Optional

import streamlit as st

from app.context import AnalystContext, create_context
from core.config import AppSettings, ConnectionConfig, DatabaseType
from core.exceptions import DatabaseAnalystError
from core.session import SessionMemory
from utils.validators import validate_connection_input

_DB_OPTIONS = [t.value for t in DatabaseType]


def render_sidebar(settings: AppSettings) -> None:
    """Render the connection sidebar and manage connection lifecycle."""
    with st.sidebar:
        st.markdown("### 🔌 Database Connection")

        default_conn = settings.default_connection()
        db_type = st.selectbox(
            "Database Type",
            _DB_OPTIONS,
            index=_DB_OPTIONS.index(default_conn.db_type.value),
            help="Choose the backend you want to connect to.",
        )
        dbt = DatabaseType.from_str(db_type)
        is_file = dbt in (DatabaseType.SQLITE, DatabaseType.DUCKDB)

        host = port = username = password = ""
        if is_file:
            database = st.text_input(
                "Database File Path",
                value=default_conn.database if default_conn.is_file_based else "sample_data/northwind.db",
                help="Path to the SQLite/DuckDB file (use ':memory:' for in-memory).",
            )
        else:
            host = st.text_input("Host", value=default_conn.host or "localhost")
            default_port = default_conn.port or (3306 if dbt == DatabaseType.MYSQL else 5432)
            port = st.number_input("Port", value=int(default_port), min_value=1, max_value=65535, step=1)
            username = st.text_input("Username", value=default_conn.username)
            password = st.text_input("Password", type="password", value="")
            database = st.text_input("Database Name", value=default_conn.database)

        col_a, col_b = st.columns(2)
        connect_clicked = col_a.button("Connect", type="primary", use_container_width=True)
        disconnect_clicked = col_b.button("Disconnect", use_container_width=True)

        if connect_clicked:
            _handle_connect(
                settings,
                db_type=db_type,
                host=host,
                port=port if not is_file else None,
                username=username,
                password=password,
                database=database,
            )

        if disconnect_clicked:
            _handle_disconnect()

        _render_status()
        st.divider()
        _render_recent_connections(settings)
        st.divider()
        _render_saved_queries()


def _memory() -> SessionMemory:
    if "memory" not in st.session_state:
        st.session_state.memory = SessionMemory()
    return st.session_state.memory


def _handle_connect(
    settings: AppSettings,
    *,
    db_type: str,
    host: str,
    port: Optional[int],
    username: str,
    password: str,
    database: str,
) -> None:
    errors = validate_connection_input(db_type, host, port, username, database)
    if errors:
        for err in errors:
            st.error(err)
        return

    config = ConnectionConfig(
        db_type=DatabaseType.from_str(db_type),
        host=host or "localhost",
        port=port,
        username=username,
        password=password,
        database=database,
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
        pool_timeout=settings.pool_timeout,
        connect_timeout=settings.connect_timeout,
        query_timeout=settings.query_timeout,
    )

    # Dispose previous context.
    old: Optional[AnalystContext] = st.session_state.get("ctx")
    if old is not None:
        old.dispose()

    memory = _memory()
    api_key = st.session_state.get("gemini_api_key_override")
    try:
        with st.spinner("Connecting and inspecting schema…"):
            ctx = create_context(config, settings, api_key=api_key, memory=memory)
            schema = ctx.repository.get_schema(include_row_counts=True)
            memory.set_schema(schema)
        st.session_state.ctx = ctx
        memory.remember_connection(config.safe_summary())
        st.success(f"Connected to {config.display_name()} — {len(schema.tables)} tables.")
    except DatabaseAnalystError as exc:
        st.session_state.pop("ctx", None)
        st.error(f"Connection failed: {exc}")
    except Exception as exc:  # noqa: BLE001
        st.session_state.pop("ctx", None)
        st.error(f"Unexpected error: {exc}")


def _handle_disconnect() -> None:
    ctx: Optional[AnalystContext] = st.session_state.get("ctx")
    if ctx is not None:
        ctx.dispose()
    st.session_state.pop("ctx", None)
    _memory().invalidate_schema()
    st.info("Disconnected.")


def _render_status() -> None:
    ctx: Optional[AnalystContext] = st.session_state.get("ctx")
    if ctx is None:
        st.markdown(
            '<span class="pill pill-warn">● Not connected</span>',
            unsafe_allow_html=True,
        )
        return
    mode = "Write" if not ctx.guard.read_only else "Read-only"
    mode_class = "pill-err" if not ctx.guard.read_only else "pill-ok"
    ai_class = "pill-ok" if ctx.llm is not None else "pill-warn"
    ai_text = "AI ready" if ctx.llm is not None else "AI off (no key)"
    st.markdown(
        f'<span class="pill pill-ok">● Connected</span>'
        f'<span class="pill {mode_class}">{mode}</span>'
        f'<span class="pill {ai_class}">{ai_text}</span>',
        unsafe_allow_html=True,
    )
    st.caption(f"{ctx.config.display_name()} · {ctx.dialect}")


def _render_recent_connections(settings: AppSettings) -> None:
    st.markdown("### 🕘 Recent Connections")
    memory = _memory()
    if not memory.recent_connections:
        st.caption("No recent connections yet.")
        return
    for i, conn in enumerate(list(memory.recent_connections)):
        label = f"{conn['db_type']} · {conn.get('database', '')}"
        if st.button(label, key=f"recent_{i}", use_container_width=True):
            _handle_connect(
                settings,
                db_type=str(conn["db_type"]),
                host=str(conn.get("host", "localhost")),
                port=conn.get("port"),
                username=str(conn.get("username", "")),
                password="",
                database=str(conn.get("database", "")),
            )


def _render_saved_queries() -> None:
    st.markdown("### 💾 Saved Queries")
    memory = _memory()
    if not memory.saved_queries:
        st.caption("Save a query from the results panel to see it here.")
        return
    for name in list(memory.saved_queries):
        with st.expander(name):
            st.code(memory.saved_queries[name], language="sql")
            cols = st.columns(2)
            if cols[0].button("Run", key=f"run_saved_{name}", use_container_width=True):
                st.session_state.pending_sql = memory.saved_queries[name]
                st.rerun()
            if cols[1].button("Delete", key=f"del_saved_{name}", use_container_width=True):
                memory.delete_saved_query(name)
                st.rerun()
