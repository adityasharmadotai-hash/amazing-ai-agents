"""Streamlit Cloud entry point.

This thin wrapper lets you deploy by pointing Streamlit Cloud's "Main file path"
at:  agents/mcp-agents/ai-database-analyst-mcp/streamlit_app.py

It simply runs the real application in app/main.py. Keeping this file next to
requirements.txt ensures the host installs the correct dependencies.
"""

from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Importing app.main executes the Streamlit application (it calls main() on import).
import app.main  # noqa: E402,F401
