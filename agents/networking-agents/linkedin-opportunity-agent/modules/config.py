"""
config.py — Centralised configuration & secret resolution.

Resolution order for every value: Streamlit session (user typed it on the
Settings page) → Streamlit secrets (cloud deploy) → environment variable / .env
→ sensible default. This keeps the app fully runnable on Streamlit Cloud while
never hard-coding a secret.
"""

from __future__ import annotations

import os

try:
    from dotenv import load_dotenv

    load_dotenv()  # load a local .env if present (no-op on Streamlit Cloud)
except Exception:  # python-dotenv not installed yet
    pass

import streamlit as st

# ── Model catalogue (Claude) ─────────────────────────────────────────────────────
MODELS = {
    "claude-opus-4-8": "Claude Opus 4.8 — most capable (best quality)",
    "claude-sonnet-4-6": "Claude Sonnet 4.6 — balanced speed / cost",
    "claude-haiku-4-5": "Claude Haiku 4.5 — fastest / cheapest (bulk scanning)",
}
DEFAULT_MODEL = "claude-opus-4-8"

# Where the SQLite database lives. Override with LINKEDIN_AGENT_DB if needed.
DB_PATH = os.environ.get(
    "LINKEDIN_AGENT_DB",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "linkedin_agent.db"),
)


def _secret(name: str, default: str = "") -> str:
    """Read from st.secrets without crashing when no secrets file exists."""
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.environ.get(name, default)


# ── API key ──────────────────────────────────────────────────────────────────────
def get_api_key() -> str:
    """Resolve the Anthropic API key (session → secrets → env)."""
    sk = st.session_state.get("api_key", "").strip()
    if sk:
        return sk
    return _secret("ANTHROPIC_API_KEY", "").strip()


def get_model() -> str:
    """Resolve the Claude model to use for analysis."""
    m = st.session_state.get("model", "").strip()
    if m in MODELS:
        return m
    env_m = _secret("LINKEDIN_AGENT_MODEL", DEFAULT_MODEL).strip()
    return env_m if env_m in MODELS else DEFAULT_MODEL


def ai_enabled() -> bool:
    """True when an API key is configured (LLM analysis available)."""
    return bool(get_api_key())


# ── SMTP / email digest settings ─────────────────────────────────────────────────
def get_smtp_settings() -> dict:
    return {
        "host": st.session_state.get("smtp_host", "") or _secret("SMTP_HOST"),
        "port": int(st.session_state.get("smtp_port", 0) or _secret("SMTP_PORT", "587") or 587),
        "user": st.session_state.get("smtp_user", "") or _secret("SMTP_USER"),
        "password": st.session_state.get("smtp_password", "") or _secret("SMTP_PASSWORD"),
        "sender": st.session_state.get("alert_from", "") or _secret("ALERT_FROM"),
        "recipient": st.session_state.get("alert_to", "") or _secret("ALERT_TO"),
    }


def smtp_configured() -> bool:
    s = get_smtp_settings()
    return bool(s["host"] and s["user"] and s["password"] and s["recipient"])
