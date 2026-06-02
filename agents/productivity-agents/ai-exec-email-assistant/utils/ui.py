"""Shared Streamlit helpers: auth gate, service factory, common UI.

Imported by `app.py` and every page so service construction and the auth
gate live in exactly one place.
"""
from __future__ import annotations

from typing import Optional

import streamlit as st

from config.settings import get_settings
from database.db import init_db
from services.ai_service import AIService
from services.analytics_service import AnalyticsService
from services.auth_service import (
    exchange_code_for_credentials,
    get_authorization_url,
    get_user_profile,
    load_saved_credentials,
)
from services.calendar_service import CalendarService
from services.gmail_service import GmailService
from utils.logging_config import setup_logging

# ---------------------------------------------------------------------------
# One-time process setup
# ---------------------------------------------------------------------------
def bootstrap() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    init_db()


def page_config(page_title: str, icon: str = "📧") -> None:
    st.set_page_config(
        page_title=f"{page_title} · {get_settings().app_title}",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )


# ---------------------------------------------------------------------------
# Credentials / auth gate
# ---------------------------------------------------------------------------
def _store_creds(creds) -> None:
    st.session_state["credentials"] = creds
    profile = get_user_profile(creds)
    st.session_state["profile"] = profile


def get_credentials():
    """Return valid credentials or None. Handles redirect code exchange."""
    if "credentials" in st.session_state and st.session_state["credentials"]:
        return st.session_state["credentials"]

    # Handle the OAuth redirect (?code=...).
    code = st.query_params.get("code")
    if code:
        try:
            creds = exchange_code_for_credentials(code)
            _store_creds(creds)
            st.query_params.clear()
            return creds
        except Exception as exc:  # noqa: BLE001
            st.error(f"Authentication failed: {exc}")
            return None

    # Try disk-cached credentials.
    creds = load_saved_credentials()
    if creds:
        _store_creds(creds)
        return creds
    return None


def require_auth() -> Optional[object]:
    """Render the sign-in screen if needed. Returns credentials or None."""
    creds = get_credentials()
    if creds:
        return creds

    settings = get_settings()
    st.title("🔐 Sign in")
    if not settings.has_google_credentials:
        st.error(
            "Google OAuth credentials are not configured. "
            "Set GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET (or GOOGLE_CLIENT_SECRETS_FILE) "
            "in your `.env`. See docs/OAUTH_SETUP.md."
        )
        return None
    st.write("Connect your Google account to let the assistant manage your inbox and calendar.")
    try:
        auth_url, _ = get_authorization_url()
        st.link_button("Continue with Google", auth_url, type="primary")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not start OAuth flow: {exc}")
    st.caption("Read-only calendar access · draft creation · no emails sent without your action.")
    return None


def logout() -> None:
    from services.auth_service import clear_credentials

    clear_credentials()
    for key in ("credentials", "profile"):
        st.session_state.pop(key, None)
    st.rerun()


# ---------------------------------------------------------------------------
# Service factory (cached per session where possible)
# ---------------------------------------------------------------------------
def gmail_service() -> GmailService:
    creds = require_auth()
    if not creds:
        st.stop()
    return GmailService(creds)


def calendar_service() -> CalendarService:
    creds = require_auth()
    if not creds:
        st.stop()
    return CalendarService(creds)


@st.cache_resource(show_spinner=False)
def ai_service() -> AIService:
    return AIService()


def analytics_service() -> AnalyticsService:
    creds = st.session_state.get("credentials")
    return AnalyticsService(GmailService(creds) if creds else None)


def safe_ai() -> Optional[AIService]:
    """Return AIService or show a friendly error if OpenAI isn't configured."""
    try:
        return ai_service()
    except Exception as exc:  # noqa: BLE001
        st.warning(f"AI features unavailable: {exc}")
        return None


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def render_sidebar() -> None:
    settings = get_settings()
    with st.sidebar:
        st.markdown(f"### 🤖 {settings.app_title}")
        profile = st.session_state.get("profile")
        if profile and profile.get("email"):
            st.success(f"Signed in as **{profile.get('name') or profile['email']}**")
            st.caption(profile["email"])
            if st.button("Sign out", use_container_width=True):
                logout()
        st.divider()
        st.caption("Navigate using the pages above ☝️")
