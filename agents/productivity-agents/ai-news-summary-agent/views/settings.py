"""
views/settings.py
-----------------
Configuration page (rendered by app.py's navigation router).

A user can paste their OpenAI key, test it, choose a model, and name the Google
Sheet — no file editing or restart needed. Saved values live in SQLite and take
precedence over .env (see src/settings.py).
"""

from __future__ import annotations

import os

import streamlit as st

import config
from src import settings

st.title("⚙️ Settings")
st.caption("Configure your API key and model here. Saved once, used everywhere.")

source = settings.get_openai_key_source()
active_key = settings.get_openai_key()
google_ok = os.path.exists(config.CREDENTIALS_FILE)

# --- status panel ------------------------------------------------------------
with st.container(border=True):
    s1, s2, s3 = st.columns(3)
    with s1:
        if source == "missing":
            st.markdown("**OpenAI key**")
            st.markdown("⚠️ not set")
        elif source == "settings":
            st.markdown("**OpenAI key**")
            st.markdown(f"✅ `{settings.mask_key(active_key)}` · saved here")
        else:
            st.markdown("**OpenAI key**")
            st.markdown(f"✅ `{settings.mask_key(active_key)}` · from .env")
    with s2:
        st.markdown("**Model**")
        st.markdown(f"`{settings.get_model()}`")
    with s3:
        st.markdown("**Google**")
        if not google_ok:
            st.markdown("⚠️ no credentials")
        elif settings.google_token_present():
            st.markdown("✅ connected")
        else:
            st.markdown("🔌 credentials set")

st.divider()

# --- OpenAI configuration ----------------------------------------------------
st.subheader("OpenAI")

key_input = st.text_input(
    "API key",
    type="password",
    placeholder="sk-…" if source == "missing" else "Leave blank to keep the current key",
    help="Get one at platform.openai.com/api-keys. Stored locally in data/emails.db.",
)

model_input = st.selectbox(
    "Model",
    options=["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1", "o4-mini"],
    index=0 if settings.get_model() not in
    {"gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1", "o4-mini"}
    else ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1", "o4-mini"].index(settings.get_model()),
    help="gpt-4o-mini is cheap and fast. Larger models give stronger analysis.",
)

# --- Google account (OAuth credentials) --------------------------------------
st.subheader("Google account")
st.caption(
    "Upload the OAuth client file (`credentials.json`) from Google Cloud Console "
    "— create one of type **Desktop app**."
)

cred_present = settings.google_credentials_present()
token_present = settings.google_token_present()

if cred_present:
    cid = settings.get_google_client_id() or ""
    short = f"…{cid[-26:]}" if cid else ""
    st.markdown(f"✅ **Credentials loaded** {('· `' + short + '`') if short else ''}")
    if token_present:
        st.markdown("🔗 **Authorized** — Gmail & Sheets access is active.")
    else:
        st.markdown("🔌 Not yet authorized — you'll approve access on your next scan.")
else:
    st.markdown("⚠️ **No credentials uploaded yet.**")

uploaded = st.file_uploader("Upload credentials.json", type=["json"], key="gcreds")
if uploaded is not None:
    raw = uploaded.getvalue()
    sig = (uploaded.name, len(raw))
    ok, detail = settings.validate_google_credentials(raw)
    if not ok:
        st.error(f"Invalid file: {detail}")
    elif st.session_state.get("_gcreds_sig") != sig:
        # Save once per uploaded file. A new client invalidates any old token.
        settings.save_google_credentials(raw)
        settings.disconnect_google()
        st.session_state["_gcreds_sig"] = sig
        st.toast("Google credentials saved.", icon="✅")
        st.rerun()
    else:
        st.success(f"Saved · client `…{detail[-26:]}`")

g1, g2 = st.columns(2)
with g1:
    if st.button("🔄 Re-authorize", use_container_width=True, disabled=not token_present):
        settings.disconnect_google()
        st.toast("Sign-in cleared — you'll re-authorize on the next scan.", icon="🔄")
        st.rerun()
with g2:
    if st.button("🗑️ Remove credentials", use_container_width=True, disabled=not cred_present):
        settings.clear_google_credentials()
        st.session_state.pop("_gcreds_sig", None)
        st.toast("Google credentials removed.", icon="🗑️")
        st.rerun()

# --- Google Sheet configuration ----------------------------------------------
st.subheader("Google Sheet")
sheet_title_input = st.text_input(
    "Sheet title",
    value=settings.get_sheet_title(),
    help="Used when the sheet is first created. Renaming later won't move existing data.",
)

st.write("")

# --- actions -----------------------------------------------------------------
save_col, test_col, clear_col, back_col = st.columns(4)

with save_col:
    if st.button("💾 Save", type="primary", use_container_width=True):
        changed = []
        if key_input.strip():
            settings.set_openai_key(key_input)
            changed.append("API key")
        if model_input != settings.get_model():
            settings.set_model(model_input)
            changed.append("model")
        if sheet_title_input.strip() and sheet_title_input.strip() != settings.get_sheet_title():
            settings.set_sheet_title(sheet_title_input)
            changed.append("sheet title")
        if changed:
            st.toast(f"Saved: {', '.join(changed)}.", icon="✅")
            st.rerun()
        else:
            st.toast("Nothing to save.", icon="ℹ️")

with test_col:
    if st.button("🔍 Test key", use_container_width=True):
        test_key = key_input.strip() or active_key
        if not test_key:
            st.warning("Enter a key first.")
        else:
            with st.spinner("Checking…"):
                try:
                    from openai import OpenAI

                    # models.list() validates the key without spending tokens.
                    OpenAI(api_key=test_key).models.list()
                    st.success("Key is valid ✅")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Key check failed: {exc}")

with clear_col:
    if st.button("🗑️ Clear key", use_container_width=True):
        settings.clear_openai_key()
        st.toast("Saved key removed — falling back to .env.", icon="🗑️")
        st.rerun()

with back_col:
    if st.button("← Dashboard", use_container_width=True):
        st.switch_page("views/dashboard.py")

# --- security note -----------------------------------------------------------
st.divider()
st.warning(
    "🔒 **Where your key is stored:** locally and unencrypted in `data/emails.db` "
    "(git-ignored). Fine for a personal machine. For shared or deployed apps, "
    "leave this blank and set `OPENAI_API_KEY` via `.env` or Streamlit secrets."
)
