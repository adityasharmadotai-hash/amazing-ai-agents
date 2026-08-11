"""
config.py — shared constants, secret access, and logging for the
WhatsApp Manager Agent.

One place for the app name, the Gemini model id, the SQLite path, and a helper
that reads secrets from either a `.env`/OS environment (webhook server) or
Streamlit `st.secrets` (dashboard) so the same modules run in both runtimes.
"""

from __future__ import annotations

import logging
import os
import sys

# Load a local .env FIRST so values below (e.g. GEMINI_MODEL) can be overridden by
# it. In the Streamlit runtime secrets come from st.secrets (see get_secret()).
try:  # pragma: no cover - convenience only
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
except Exception:
    pass

APP_NAME = "WhatsApp Manager Agent"
APP_TAGLINE = "24/7 AI first-responder for your WhatsApp leads"

# Default is fast + snappy; override with GEMINI_MODEL in .env (e.g. gemini-2.5-pro).
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Graph API version for the WhatsApp Cloud API endpoints.
WHATSAPP_API_VERSION = "v21.0"

# How many recent turns of a conversation to feed the model each reply.
HISTORY_TURNS = 12

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(_DATA_DIR, "whatsapp.db")


def get_secret(name: str, default: str = "") -> str:
    """Read a config value from Streamlit secrets first, then the environment.

    Works whether we're inside the Streamlit dashboard (st.secrets) or the
    FastAPI webhook / a plain script (os.environ).
    """
    try:
        import streamlit as st  # local import so non-Streamlit runtimes stay light

        val = st.secrets.get(name)  # type: ignore[attr-defined]
        if val:
            return str(val)
    except Exception:
        pass
    return os.environ.get(name, default)


def team_numbers() -> list[str]:
    """Team WhatsApp numbers to notify on escalation (E.164 digits, no '+')."""
    raw = get_secret("TEAM_WHATSAPP_NUMBERS", "")
    return [n.strip().lstrip("+") for n in raw.replace(";", ",").split(",") if n.strip()]


_BASE = "wamanager"
_LOG_CONFIGURED = False


def get_logger(name: str = _BASE) -> logging.Logger:
    """Return a configured logger; handlers live on the shared `wamanager` parent."""
    global _LOG_CONFIGURED
    base = logging.getLogger(_BASE)
    if not _LOG_CONFIGURED:
        base.setLevel(logging.INFO)
        base.propagate = False
        fmt = logging.Formatter("%(asctime)s  %(levelname)-7s %(name)s: %(message)s", "%H:%M:%S")

        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        base.addHandler(sh)

        try:
            os.makedirs(_DATA_DIR, exist_ok=True)
            fh = logging.FileHandler(os.path.join(_DATA_DIR, "wamanager.log"), encoding="utf-8")
            fh.setFormatter(fmt)
            base.addHandler(fh)
        except Exception:
            pass  # file logging is optional (read-only filesystems, etc.)

        _LOG_CONFIGURED = True

    if name == _BASE or name.startswith(_BASE + "."):
        return logging.getLogger(name)
    return logging.getLogger(f"{_BASE}.{name}")
