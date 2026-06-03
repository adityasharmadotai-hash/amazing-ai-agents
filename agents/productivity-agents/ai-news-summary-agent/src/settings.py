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

import json
import os
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


# --- Google OAuth credentials ------------------------------------------------
# The OAuth "client secrets" file (credentials.json) and the saved sign-in
# token live on disk at the paths in config. These helpers let the Settings
# page upload, inspect, re-authorize, and remove them — no manual file copying.
def google_credentials_present() -> bool:
    return os.path.exists(config.CREDENTIALS_FILE)


def google_token_present() -> bool:
    """True once the user has authorized (a token.json exists)."""
    return os.path.exists(config.TOKEN_FILE)


def validate_google_credentials(raw: bytes) -> tuple[bool, str]:
    """Check an uploaded file is a usable OAuth client JSON.

    Returns (ok, detail). On success `detail` is the client_id; on failure it's
    a human-readable reason.
    """
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return False, "This isn't valid JSON."
    block = data.get("installed") or data.get("web")
    if not block:
        return False, (
            "No 'installed'/'web' section found. Download an OAuth client of "
            "type **Desktop app** from Google Cloud Console."
        )
    if not block.get("client_id"):
        return False, "No client_id in the file — it may be the wrong download."
    return True, block["client_id"]


def save_google_credentials(raw: bytes) -> None:
    """Write the uploaded credentials to the path the OAuth flow reads."""
    os.makedirs(os.path.dirname(config.CREDENTIALS_FILE) or ".", exist_ok=True)
    with open(config.CREDENTIALS_FILE, "wb") as f:
        f.write(raw)


def get_google_client_id() -> Optional[str]:
    if not google_credentials_present():
        return None
    try:
        with open(config.CREDENTIALS_FILE) as f:
            data = json.load(f)
        block = data.get("installed") or data.get("web") or {}
        return block.get("client_id")
    except Exception:  # noqa: BLE001
        return None


def disconnect_google() -> None:
    """Delete the saved sign-in token so the next scan re-authorizes."""
    if os.path.exists(config.TOKEN_FILE):
        os.remove(config.TOKEN_FILE)


def clear_google_credentials() -> None:
    """Remove both the credentials file and any saved token."""
    for path in (config.CREDENTIALS_FILE, config.TOKEN_FILE):
        if os.path.exists(path):
            os.remove(path)


# --- Helpers -----------------------------------------------------------------
def mask_key(key: Optional[str]) -> str:
    """Show a key safely: 'sk-...AbCd' (only the last 4 chars)."""
    if not key:
        return "—"
    if len(key) <= 8:
        return "•" * len(key)
    return f"{key[:3]}…{key[-4:]}"
