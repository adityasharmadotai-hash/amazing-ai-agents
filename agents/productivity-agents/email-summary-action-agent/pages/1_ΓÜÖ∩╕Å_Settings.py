"""
pages/1_⚙️_Settings.py
----------------------
Configuration page for the agent.

Streamlit automatically turns any file inside a `pages/` folder into a page in
the sidebar navigation, so this shows up as "⚙️ Settings" next to the main
dashboard. Here a user can paste their OpenAI API key, pick a model, name the
Google Sheet, and test the key — all without editing files or restarting.

Saved values live in SQLite and take precedence over .env (see src/settings.py).
"""

from __future__ import annotations

import streamlit as st

from src import database, settings

st.set_page_config(page_title="Settings · Email Action Agent", page_icon="⚙️", layout="centered")
database.init_db()

st.title("⚙️ Settings")
st.caption("Configure your OpenAI API key and model. Saved here, used everywhere.")

# --- current status ----------------------------------------------------------
source = settings.get_openai_key_source()
active_key = settings.get_openai_key()

status_col, model_col = st.columns(2)
with status_col:
    if source == "missing":
        st.error("**API key:** not set")
    elif source == "settings":
        st.success(f"**API key:** {settings.mask_key(active_key)}  ·  saved here")
    else:
        st.info(f"**API key:** {settings.mask_key(active_key)}  ·  from .env")
with model_col:
    st.info(f"**Active model:** `{settings.get_model()}`")

st.divider()

# --- the configuration form --------------------------------------------------
st.subheader("OpenAI")

key_input = st.text_input(
    "API key",
    type="password",
    placeholder="sk-..." if source == "missing" else "Leave blank to keep the current key",
    help="Get one at platform.openai.com/api-keys. Stored locally in data/emails.db.",
)

model_input = st.text_input(
    "Model",
    value=settings.get_model(),
    help="e.g. gpt-4o-mini (cheap, fast), gpt-4o (stronger). Any chat model works.",
)

st.subheader("Google Sheet")
sheet_title_input = st.text_input(
    "Sheet title (used when the sheet is first created)",
    value=settings.get_sheet_title(),
)

# --- actions -----------------------------------------------------------------
save_col, test_col, clear_col = st.columns(3)

with save_col:
    if st.button("💾 Save", type="primary", use_container_width=True):
        changed = []
        if key_input.strip():
            settings.set_openai_key(key_input)
            changed.append("API key")
        if model_input.strip() and model_input.strip() != settings.get_model():
            settings.set_model(model_input)
            changed.append("model")
        if sheet_title_input.strip() and sheet_title_input.strip() != settings.get_sheet_title():
            settings.set_sheet_title(sheet_title_input)
            changed.append("sheet title")
        if changed:
            st.success(f"Saved: {', '.join(changed)}.")
            st.rerun()
        else:
            st.info("Nothing to save.")

with test_col:
    if st.button("🔍 Test key", use_container_width=True):
        # Prefer the freshly typed key; otherwise test the active one.
        test_key = key_input.strip() or active_key
        if not test_key:
            st.warning("Enter a key first.")
        else:
            with st.spinner("Checking..."):
                try:
                    from openai import OpenAI

                    # models.list() validates the key without spending any tokens.
                    OpenAI(api_key=test_key).models.list()
                    st.success("Key is valid ✅")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Key check failed: {exc}")

with clear_col:
    if st.button("🗑️ Clear saved key", use_container_width=True):
        settings.clear_openai_key()
        st.success("Saved key removed. Falling back to .env (if set).")
        st.rerun()

# --- security note -----------------------------------------------------------
st.divider()
st.warning(
    "🔒 **Where your key is stored:** locally and unencrypted in `data/emails.db`, "
    "which is git-ignored. That's fine for a personal machine. For shared or "
    "deployed environments, leave this blank and use `OPENAI_API_KEY` via your "
    "`.env` file or Streamlit secrets instead."
)
