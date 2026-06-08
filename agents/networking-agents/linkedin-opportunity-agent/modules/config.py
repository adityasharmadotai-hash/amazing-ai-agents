"""
config.py — Centralised configuration & secret resolution.

Resolution order for every value: Streamlit session (user typed it on the
Settings page) → Streamlit secrets (cloud deploy) → environment variable / .env
→ sensible default. This keeps the app fully runnable on Streamlit Cloud while
never hard-coding a secret.
"""

from __future__ import annotations

import os
import tempfile

try:
    from dotenv import load_dotenv

    load_dotenv()  # load a local .env if present (no-op on Streamlit Cloud)
except Exception:  # python-dotenv not installed yet
    pass

import streamlit as st

# ── Model catalogue (OpenAI) ─────────────────────────────────────────────────────
MODELS = {
    "gpt-4o": "GPT-4o — most capable (best quality)",
    "gpt-4o-mini": "GPT-4o mini — fast / cheap (bulk scanning)",
    "gpt-4.1-mini": "GPT-4.1 mini — balanced speed / cost",
}
DEFAULT_MODEL = "gpt-4o-mini"

# Where the SQLite database lives. Defaults to a writable temp directory so it
# works on Streamlit Cloud, where the mounted repo path is not a reliable place
# to write. Override with the LINKEDIN_AGENT_DB env var if you want it elsewhere.
DB_PATH = os.environ.get(
    "LINKEDIN_AGENT_DB",
    os.path.join(tempfile.gettempdir(), "linkedin_opportunity_agent", "linkedin_agent.db"),
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
    """Resolve the OpenAI API key (session → secrets → env).

    Accepts either OPENAI_API_KEY (preferred) or the legacy ANTHROPIC_API_KEY
    secret name so existing deployments keep working.
    """
    sk = st.session_state.get("api_key", "").strip()
    if sk:
        return sk
    return (_secret("OPENAI_API_KEY", "") or _secret("ANTHROPIC_API_KEY", "")).strip()


def get_model() -> str:
    """Resolve the OpenAI model to use for analysis."""
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
