"""Streamlit entry point for the AI Database Analyst MCP Agent.

Run with:

    streamlit run app/main.py
"""

from __future__ import annotations

import os
import sys

# Ensure the project root is importable when launched via `streamlit run`.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st  # noqa: E402

from app.components.chat import render_chat  # noqa: E402
from app.components.settings_panel import render_settings  # noqa: E402
from app.components.sidebar import render_sidebar  # noqa: E402
from core.config import get_settings  # noqa: E402
from core.logging_config import configure_logging  # noqa: E402
from core.session import SessionMemory  # noqa: E402


def _load_css() -> None:
    css_path = os.path.join(_ROOT, "static", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as fh:
            st.markdown(f"<style>{fh.read()}</style>", unsafe_allow_html=True)


def _ensure_sample_db(settings) -> None:
    """Create the bundled SQLite sample DB on first run if it is missing.

    The sample database is git-ignored, so on a fresh deploy (e.g. Streamlit
    Cloud) it won't exist. Generate it on demand so the demo works out of the box.
    """
    if settings.db_type.lower() != "sqlite":
        return
    db_path = settings.db_name
    if not db_path or db_path == ":memory:" or os.path.exists(db_path):
        return
    try:
        from scripts.create_sample_db import create_sample_db

        create_sample_db(db_path)
    except Exception:  # noqa: BLE001 - never block startup on sample-data creation
        pass


def main() -> None:
    settings = get_settings()
    configure_logging(log_dir=settings.log_dir, level=settings.log_level)
    _ensure_sample_db(settings)

    st.set_page_config(
        page_title="AI Database Analyst",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _load_css()

    # Initialise persistent session objects.
    if "memory" not in st.session_state:
        st.session_state.memory = SessionMemory()
    st.session_state.setdefault("write_mode_enabled", False)

    # Header
    st.markdown(
        '<div class="app-header">'
        "<h1>🧠 AI Database Analyst</h1>"
        "<p>Chat with your SQL database using natural language — powered by Gemini & MCP.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    render_sidebar(settings)
    render_settings(settings)
    render_chat()

    st.divider()
    st.caption(
        "Read-only by default · Parameterised & sanitised SQL · "
        "MCP tools: schema, tables, columns, indexes, relationships, statistics, "
        "execution, charts, exports."
    )


if __name__ == "__main__":
    # Runs when launched via `streamlit run app/main.py`. The streamlit_app.py
    # wrapper imports and calls main() directly instead.
    main()
