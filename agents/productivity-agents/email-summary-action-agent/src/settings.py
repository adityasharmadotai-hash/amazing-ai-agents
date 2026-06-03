"""
src/settings.py
---------------
Runtime settings that can be changed from the UI Settings page.

Precedence for every setting is:  saved value (SQLite)  ->  .env default.

Why store them in SQLite? So a user can run the app, paste their OpenAI key
into the Settings page, and start working — without ever touching a .env file
or restarting the server. The .env values remain the fallback, which is what
you want for headless / deployed runs.

Security note: the key is stored locally, unencrypted, in the same SQLite file
as your email data (data/emails.db, which is git-ignored). For shared or
deployed environments, prefer environment variables / Streamlit secrets and
leave the UI field blank.
"""

from __future__ import annotations

from typing import Optional

import config
from src import database

# app_meta keys (namespaced so they never collide with internal meta like sheet_id)
_KEY_OPENAI = "setting:openai_api_key"
_KEY_MODEL = "setting:openai_model"
_KEY_SHEET_TITLE = "setting:sheet_title"


# --- OpenAI API key ----------------------------------------------------------
def get_openai_key() -> Optional[str]:
    """Effective key: UI-saved value, else the .env value, else None."""
    database.init_db()
    return database.get_meta(_KEY_OPENAI) or config.OPENAI_API_KEY or None


def get_openai_key_source() -> str:
    """Where the active key comes from: 'settings', 'env', or 'missing'."""
    if database.get_meta(_KEY_OPENAI):
        return "settings"
    if config.OPENAI_API_KEY:
        return "env"
    return "missing"


def set_openai_key(key: str) -> None:
    database.set_meta(_KEY_OPENAI, key.strip())


def clear_openai_key() -> None:
    """Remove the UI-saved key so the app falls back to the .env value."""
    database.delete_meta(_KEY_OPENAI)


# --- Model -------------------------------------------------------------------
def get_model() -> str:
    return database.get_meta(_KEY_MODEL) or config.OPENAI_MODEL


def set_model(model: str) -> None:
    database.set_meta(_KEY_MODEL, model.strip())


# --- Sheet title -------------------------------------------------------------
def get_sheet_title() -> str:
    return database.get_meta(_KEY_SHEET_TITLE) or config.SHEET_TITLE


def set_sheet_title(title: str) -> None:
    database.set_meta(_KEY_SHEET_TITLE, title.strip())


# --- Helpers -----------------------------------------------------------------
def mask_key(key: Optional[str]) -> str:
    """Show a key safely: 'sk-...AbCd' (only the last 4 chars)."""
    if not key:
        return "—"
    if len(key) <= 8:
        return "•" * len(key)
    return f"{key[:3]}…{key[-4:]}"
