"""Streamlit Cloud entry point.

Deploy by pointing Streamlit Cloud's "Main file path" at:
    agents/mcp-agents/ai-database-analyst-mcp/streamlit_app.py

Streamlit re-executes this file on every interaction, so we import ``main`` and
CALL it on each run (importing for its side effects would only render once, then
show a blank page on the next rerun). Keeping this file next to requirements.txt
also ensures the host installs the correct dependencies.
"""

from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.main import main  # noqa: E402

main()
