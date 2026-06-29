"""Launcher / entry point for the AI Database Analyst.

Works in two modes:

1. **As a Streamlit entry point** — when this file is the "Main file path" on
   Streamlit Cloud (or run via ``streamlit run run.py``), it renders the app
   directly. (It does NOT spawn a second Streamlit process — doing that on the
   cloud is what causes a blank screen.)

2. **As a CLI launcher** — when run with plain ``python run.py`` locally, it
   ensures the sample database exists and then starts Streamlit for you.
"""

from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _in_streamlit_runtime() -> bool:
    """True when this module is being executed inside a Streamlit script run."""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        return get_script_run_ctx() is not None
    except Exception:  # noqa: BLE001 - streamlit missing or internal API moved
        return False


def _launch_cli() -> None:
    """Start Streamlit as a subprocess (local convenience)."""
    app_path = os.path.join(ROOT, "app", "main.py")
    cmd = [sys.executable, "-m", "streamlit", "run", app_path]
    print("Launching:", " ".join(cmd))
    raise SystemExit(subprocess.call(cmd))


if _in_streamlit_runtime():
    # Rendered by Streamlit — run the real app on every rerun.
    from app.main import main

    main()
elif __name__ == "__main__":
    _launch_cli()
