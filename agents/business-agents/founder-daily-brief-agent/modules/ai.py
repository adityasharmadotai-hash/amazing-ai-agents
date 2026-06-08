"""
ai.py — Thin OpenAI wrapper used across the app.

Every AI feature degrades gracefully: if no API key is configured the calling
modules fall back to deterministic, rule-based output so the dashboard is fully
usable out of the box (with richer narrative once a key is added).
"""

import json, os, re
import streamlit as st

try:
    from openai import OpenAI
except Exception:  # openai not installed yet
    OpenAI = None


# ── Key resolution ──────────────────────────────────────────────────────────────

def get_key() -> str:
    """Resolve the OpenAI key: user-entered (session) → secrets → env."""
    sk = st.session_state.get("user_api_key", "").strip()
    if sk:
        return sk
    try:
        return st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    except Exception:
        return os.environ.get("OPENAI_API_KEY", "")


def is_configured() -> bool:
    return bool(get_key()) and OpenAI is not None


def _client():
    return OpenAI(api_key=get_key())


# ── Completions ─────────────────────────────────────────────────────────────────

def complete(system: str, user: str, tokens: int = 1200, temperature: float = 0.6) -> str:
    """Plain text completion. Raises on failure — callers handle fallback."""
    r = _client().chat.completions.create(
        model="gpt-4o",
        max_tokens=tokens,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return r.choices[0].message.content.strip()


def parse_json(text: str):
    """Strip markdown fences and parse JSON."""
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    return json.loads(cleaned)


def complete_json(system: str, user: str, tokens: int = 1500, temperature: float = 0.5):
    return parse_json(complete(system, user, tokens=tokens, temperature=temperature))
