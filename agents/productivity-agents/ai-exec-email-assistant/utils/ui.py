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


def detect_app_url() -> Optional[str]:
    """Best-effort detection of this app's public base URL (with trailing slash).

    Reads the incoming request headers that Streamlit exposes via
    ``st.context.headers``. Behind Streamlit Community Cloud's proxy the
    ``Host`` header carries the public hostname and ``X-Forwarded-Proto`` the
    scheme, so we can reconstruct e.g. ``https://my-app.streamlit.app/``.
    Returns None if it can't be determined (older Streamlit, local run, etc.).
    """
    try:
        raw = getattr(st.context, "headers", None)
        if not raw:
            return None
        headers = {str(k).lower(): v for k, v in dict(raw).items()}
        host = headers.get("host")
        proto = headers.get("x-forwarded-proto") or "https"
        if host:
            # If a local dev server, prefer http.
            if host.startswith("localhost") or host.startswith("127.0.0.1"):
                proto = headers.get("x-forwarded-proto") or "http"
            return f"{proto}://{host}/"
        origin = headers.get("origin")
        if origin:
            return origin.rstrip("/") + "/"
    except Exception:  # noqa: BLE001 - detection is best-effort only
        return None
    return None


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
            "Google OAuth credentials are not configured yet. "
            "Open **⚙️ Settings** to add your GOOGLE_CLIENT_ID and "
            "GOOGLE_CLIENT_SECRET (or set them via environment / Streamlit "
            "secrets). See docs/OAUTH_SETUP.md."
        )
        try:
            st.page_link("pages/9_Settings.py", label="Go to Settings", icon="⚙️")
        except Exception:  # noqa: BLE001 - older Streamlit without page_link
            pass
        return None
    st.write("Connect your Google account to let the assistant manage your inbox and calendar.")
    detected = detect_app_url()
    redirect = settings.google_redirect_uri
    if (
        detected
        and "localhost" not in detected
        and "127.0.0.1" not in detected
        and ("localhost" in redirect or "127.0.0.1" in redirect)
    ):
        st.warning(
            "Your Redirect URI is set to localhost, but this app is running at "
            f"**{detected}**. Google will send you to a dead localhost page after "
            "sign-in. Open ⚙️ Settings and set the Redirect URI to this app's URL "
            "(and register the same URL in Google Cloud Console).",
            icon="⚠️",
        )
        try:
            st.page_link("pages/9_Settings.py", label="Fix in Settings", icon="⚙️")
        except Exception:  # noqa: BLE001
            pass
    try:
        auth_url, _ = get_authorization_url()
        st.link_button("Continue with Google", auth_url, type="primary")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not start OAuth flow: {exc}")
    st.caption(
        "Read-only calendar access · draft creation · no emails sent without your action."
    )
    st.divider()
    st.caption(
        "🔎 This app will send the following **redirect URI** to Google. It must be "
        "registered **exactly** (including the trailing slash) under your OAuth "
        "client's Authorized redirect URIs:"
    )
    st.code(redirect or "(not set)", language=None)
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
        try:
            st.page_link("pages/9_Settings.py", label="Settings", icon="⚙️")
        except Exception:  # noqa: BLE001 - older Streamlit without page_link
            pass
        st.caption("Navigate using the pages above ☝️")
