"""Settings page — configure API keys and OAuth credentials from the UI.

Values entered here are saved to a local JSON file and applied immediately,
so the app can be configured without editing `.env` or Streamlit secrets.
"""
from __future__ import annotations

import os

import streamlit as st

from config.settings import (
    RUNTIME_KEYS,
    SECRET_KEYS,
    clear_overrides,
    get_settings,
    load_overrides,
    overrides_path,
    save_overrides,
)
from utils.ui import bootstrap, detect_app_url, page_config, render_sidebar

page_config("Settings", icon="⚙️")
bootstrap()
render_sidebar()

st.title("⚙️ Settings")
st.caption(
    "Configure your API keys and Google OAuth credentials here. "
    "Saved settings are applied immediately — no redeploy needed."
)


def _current(key: str, default: str = "") -> str:
    """Current effective value for a managed key (env wins, then saved override)."""
    return os.getenv(key, load_overrides().get(key, default))


def _mask(value: str) -> str:
    if not value:
        return "—"
    if len(value) <= 8:
        return "•" * len(value)
    return f"{value[:4]}…{value[-4:]}"


settings = get_settings()

# --- Status banner -----------------------------------------------------------
c1, c2 = st.columns(2)
with c1:
    if settings.has_openai:
        st.success("OpenAI: configured")
    else:
        st.error("OpenAI: not configured")
with c2:
    if settings.has_google_credentials:
        st.success("Google OAuth: configured")
    else:
        st.error("Google OAuth: not configured")

st.divider()

# --- Form --------------------------------------------------------------------
with st.form("settings_form"):
    st.subheader("🤖 OpenAI")
    openai_api_key = st.text_input(
        "API key",
        value=_current("OPENAI_API_KEY"),
        type="password",
        help="From platform.openai.com → API keys. Stored locally.",
        placeholder="sk-...",
    )
    oc1, oc2 = st.columns(2)
    with oc1:
        openai_model = st.text_input(
            "Chat model", value=_current("OPENAI_MODEL", "gpt-4o-mini")
        )
        openai_transcribe_model = st.text_input(
            "Transcription model", value=_current("OPENAI_TRANSCRIBE_MODEL", "whisper-1")
        )
    with oc2:
        openai_reasoning_model = st.text_input(
            "Reasoning model", value=_current("OPENAI_REASONING_MODEL", "gpt-4o")
        )
        openai_tts_model = st.text_input(
            "Text-to-speech model", value=_current("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
        )
    openai_tts_voice = st.text_input(
        "TTS voice", value=_current("OPENAI_TTS_VOICE", "alloy")
    )

    st.subheader("🔐 Google OAuth")
    google_client_id = st.text_input(
        "Client ID",
        value=_current("GOOGLE_CLIENT_ID"),
        placeholder="xxxxxx.apps.googleusercontent.com",
    )
    google_client_secret = st.text_input(
        "Client secret",
        value=_current("GOOGLE_CLIENT_SECRET"),
        type="password",
        placeholder="GOCSPX-...",
    )

    # Detect this app's public URL so the redirect URI defaults correctly
    # instead of localhost when running on a host like Streamlit Cloud.
    _detected = detect_app_url()
    _saved_redirect = _current("GOOGLE_REDIRECT_URI", "")
    if _saved_redirect and "localhost" not in _saved_redirect and "127.0.0.1" not in _saved_redirect:
        _redirect_default = _saved_redirect
    elif _detected and "localhost" not in _detected and "127.0.0.1" not in _detected:
        _redirect_default = _detected
    else:
        _redirect_default = _saved_redirect or _detected or "http://localhost:8501"

    if _detected:
        st.info(f"Detected this app's URL: **{_detected}**", icon="🌐")
    google_redirect_uri = st.text_input(
        "Redirect URI",
        value=_redirect_default,
        help=(
            "Must EXACTLY match an Authorized redirect URI in Google Cloud "
            "Console (including https:// and any trailing slash). For Streamlit "
            "Cloud use your app URL, e.g. https://your-app.streamlit.app/"
        ),
    )
    st.caption(
        "After changing the redirect URI, add the same value under "
        "**APIs & Services → Credentials → your OAuth client → Authorized "
        "redirect URIs** in Google Cloud Console — otherwise Google will reject "
        "the sign-in or bounce you to a dead URL. See docs/OAUTH_SETUP.md."
    )

    st.subheader("👤 Personalization")
    pc1, pc2 = st.columns(2)
    with pc1:
        owner_name = st.text_input("Your name", value=_current("OWNER_NAME"))
        timezone = st.text_input(
            "Timezone", value=_current("TIMEZONE", "Asia/Kolkata")
        )
    with pc2:
        max_emails_fetch = st.number_input(
            "Max emails to fetch",
            min_value=10,
            max_value=200,
            step=10,
            value=int(_current("MAX_EMAILS_FETCH", "50") or 50),
        )
        enable_voice = st.toggle(
            "Enable voice features",
            value=str(_current("ENABLE_VOICE", "true")).lower()
            in {"1", "true", "yes", "on"},
        )

    submitted = st.form_submit_button("💾 Save settings", type="primary", use_container_width=True)

if submitted:
    values = {
        "OPENAI_API_KEY": openai_api_key,
        "OPENAI_MODEL": openai_model,
        "OPENAI_REASONING_MODEL": openai_reasoning_model,
        "OPENAI_TRANSCRIBE_MODEL": openai_transcribe_model,
        "OPENAI_TTS_MODEL": openai_tts_model,
        "OPENAI_TTS_VOICE": openai_tts_voice,
        "GOOGLE_CLIENT_ID": google_client_id,
        "GOOGLE_CLIENT_SECRET": google_client_secret,
        "GOOGLE_REDIRECT_URI": google_redirect_uri,
        "OWNER_NAME": owner_name,
        "TIMEZONE": timezone,
        "MAX_EMAILS_FETCH": str(int(max_emails_fetch)),
        "ENABLE_VOICE": "true" if enable_voice else "false",
    }
    save_overrides(values)
    # Drop cached services (e.g. AIService) so they rebuild with new keys.
    try:
        st.cache_resource.clear()
    except Exception:  # noqa: BLE001
        pass
    st.success("Settings saved and applied. Head to any page to sign in / use the assistant.")
    st.rerun()

st.divider()

# --- Current effective config (masked) --------------------------------------
with st.expander("View current configuration"):
    rows = []
    for key in RUNTIME_KEYS:
        val = _current(key)
        shown = _mask(val) if key in SECRET_KEYS else (val or "—")
        source = "environment / secrets" if os.environ.get(key) and key not in load_overrides() else (
            "saved in app" if key in load_overrides() else "default"
        )
        rows.append({"Setting": key, "Value": shown, "Source": source})
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.caption(f"Saved settings file: `{overrides_path()}`")

with st.expander("⚠️ Reset"):
    st.write(
        "Clear all settings entered in this app. Values supplied via environment "
        "variables or Streamlit secrets are not affected."
    )
    if st.button("Clear saved settings", type="secondary"):
        clear_overrides()
        try:
            st.cache_resource.clear()
        except Exception:  # noqa: BLE001
            pass
        st.success("Cleared saved settings.")
        st.rerun()

st.info(
    "🔒 Settings are stored in plaintext JSON on the server's disk. On hosts with "
    "an ephemeral filesystem (e.g. Streamlit Community Cloud) they reset when the "
    "app restarts — for permanent config there, use Streamlit secrets instead.",
    icon="🔒",
)
