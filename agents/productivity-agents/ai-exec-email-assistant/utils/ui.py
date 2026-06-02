"""Shared Streamlit helpers: auth gate, service factory, common UI.

Imported by `app.py` and every page so service construction and the auth
gate live in exactly one place.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import streamlit as st

from config.settings import get_settings
from database.db import init_db
from services.auth_service import (
    exchange_code_for_credentials,
    get_authorization_url,
    get_user_profile,
    load_saved_credentials,
)
from utils.logging_config import setup_logging

if TYPE_CHECKING:  # imports for type hints only — not evaluated at runtime
    from services.ai_service import AIService
    from services.analytics_service import AnalyticsService
    from services.gmail_service import GmailService

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
    from utils.theme import inject_global_css

    inject_global_css()


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
            st.session_state.pop("_oauth_auth_url", None)
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
    detected = detect_app_url()
    redirect = settings.google_redirect_uri

    st.markdown("<div class='signin-wrap'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='signin-card'>"
        "<div class='signin-logo'>📧</div>"
        f"<div class='section-eyebrow'>{settings.app_title}</div>"
        "<h1 style='margin:.1rem 0 .4rem;font-size:1.7rem'>Sign in</h1>"
        "<p style='color:var(--muted);margin:0 0 18px'>Connect your Google account "
        "to let the assistant read, triage, and draft your email.</p>",
        unsafe_allow_html=True,
    )

    if not settings.has_google_credentials:
        st.error(
            "Google OAuth isn't configured yet. Open **⚙️ Settings** to add your "
            "Client ID and Client Secret (or set them via Streamlit secrets)."
        )
        try:
            st.page_link("pages/9_Settings.py", label="Go to Settings", icon="⚙️")
        except Exception:  # noqa: BLE001
            pass
        st.markdown("</div></div>", unsafe_allow_html=True)
        return None

    if (
        detected
        and "localhost" not in detected
        and "127.0.0.1" not in detected
        and ("localhost" in redirect or "127.0.0.1" in redirect)
    ):
        st.warning(
            f"Redirect URI is localhost but the app runs at **{detected}**. "
            "Update it in ⚙️ Settings and register the same URL in Google Cloud Console.",
            icon="⚠️",
        )
        try:
            st.page_link("pages/9_Settings.py", label="Fix in Settings", icon="⚙️")
        except Exception:  # noqa: BLE001
            pass

    try:
        auth_url = st.session_state.get("_oauth_auth_url")
        if not auth_url:
            auth_url, _ = get_authorization_url()
            st.session_state["_oauth_auth_url"] = auth_url
        st.link_button("Continue with Google", auth_url, type="primary", use_container_width=True)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not start OAuth flow: {exc}")

    st.markdown(
        "<p style='color:var(--muted);font-size:.8rem;margin:14px 0 0;text-align:center'>"
        "Gmail access · draft creation · nothing sent without your explicit action.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Advanced · redirect URI being sent to Google"):
        st.caption(
            "This exact value must be registered (including any trailing slash) "
            "under your OAuth client's Authorized redirect URIs:"
        )
        st.code(redirect or "(not set)", language=None)
    st.markdown("</div>", unsafe_allow_html=True)
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
def gmail_service() -> "GmailService":
    from services.gmail_service import GmailService

    creds = require_auth()
    if not creds:
        st.stop()
    return GmailService(creds)


@st.cache_resource(show_spinner=False)
def ai_service() -> "AIService":
    from services.ai_service import AIService

    return AIService()


def analytics_service() -> "AnalyticsService":
    from services.analytics_service import AnalyticsService
    from services.gmail_service import GmailService

    creds = st.session_state.get("credentials")
    return AnalyticsService(GmailService(creds) if creds else None)


def safe_ai() -> Optional["AIService"]:
    """Return AIService or show a friendly error if OpenAI isn't configured."""
    try:
        return ai_service()
    except Exception as exc:  # noqa: BLE001
        st.warning(f"AI features unavailable: {exc}")
        return None


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def _nav_link(path: str, label: str, icon: str) -> None:
    try:
        st.page_link(path, label=label, icon=icon)
    except Exception:  # noqa: BLE001 - older Streamlit without page_link
        st.markdown(f"<div style='padding:6px 10px;color:var(--muted)'>{icon} {label}</div>",
                    unsafe_allow_html=True)


def render_sidebar() -> None:
    settings = get_settings()
    with st.sidebar:
        st.markdown(
            f"<div class='brand'><span class='dot'></span>{settings.app_title}</div>"
            "<div class='brand-sub'>Voice-First Inbox</div>",
            unsafe_allow_html=True,
        )

        profile = st.session_state.get("profile")
        if profile and profile.get("email"):
            name = profile.get("name") or profile["email"]
            initial = (name[:1] or "?").upper()
            st.markdown(
                f"<div class='user-chip'><div class='avatar'>{initial}</div>"
                f"<div><div class='u-name'>{name}</div>"
                f"<div class='u-mail'>{profile['email']}</div></div></div>",
                unsafe_allow_html=True,
            )

        # ---- Featured: Voice is the primary way to drive the whole app ----
        st.markdown(
            "<div class='voice-feature'>"
            "<div class='vf-top'><div class='vf-mic'>🎤</div>"
            "<div><div class='vf-title'>Voice Command</div>"
            "<span class='vf-badge'>Primary Control</span></div></div>"
            "<p class='vf-desc'>Run the entire assistant hands-free — "
            "read, search, draft, and brief by just speaking.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div></div>", unsafe_allow_html=True)  # CSS anchor for the link below
        _nav_link("pages/4_Voice.py", "Start Voice Command", "🎙️")

        # ---- Workspace ----
        st.markdown("<div class='nav-group'>Workspace</div>", unsafe_allow_html=True)
        _nav_link("app.py", "Home", "🏠")
        _nav_link("pages/1_Inbox.py", "Inbox", "📥")
        _nav_link("pages/2_AI_Assistant.py", "AI Assistant", "🤖")
        _nav_link("pages/3_Drafting.py", "Drafting", "✍️")
        _nav_link("pages/6_Briefing.py", "Briefing", "📋")

        # ---- Insights ----
        st.markdown("<div class='nav-group'>Insights & Tools</div>", unsafe_allow_html=True)
        _nav_link("pages/7_Analytics.py", "Analytics", "📊")
        _nav_link("pages/8_Export.py", "Export", "📤")
        _nav_link("pages/9_Settings.py", "Settings", "⚙️")

        st.markdown("<div class='nav-group'>Account</div>", unsafe_allow_html=True)
        if profile and profile.get("email"):
            if st.button("Sign out", use_container_width=True):
                logout()
        st.markdown(
            "<div style='color:var(--muted);font-size:.72rem;margin-top:12px'>"
            "Built with OpenAI + Gmail API</div>",
            unsafe_allow_html=True,
        )
