"""📥 Inbox — read, search, filter, starred & important."""
from __future__ import annotations

import streamlit as st

from config.settings import get_settings
from utils.components import email_list
from utils.theme import hero
from utils.ui import bootstrap, gmail_service, page_config, render_sidebar, require_auth

bootstrap()
page_config("Inbox", "📥")
render_sidebar()
if not require_auth():
    st.stop()

settings = get_settings()
hero("Inbox", "Read, search, and filter your mail — all in one view.", eyebrow="Gmail")

gmail = gmail_service()
max_n = st.sidebar.slider("Emails to fetch", 5, settings.max_emails_fetch, 25, step=5)

tabs = st.tabs(["Inbox", "Unread", "Search", "Labels", "Starred", "Important"])

with tabs[0]:
    if st.button("🔄 Refresh inbox", key="refresh_inbox"):
        st.session_state.pop("inbox_cache", None)
    if "inbox_cache" not in st.session_state:
        with st.spinner("Fetching inbox…"):
            st.session_state["inbox_cache"] = gmail.read_inbox(max_results=max_n)
    email_list(st.session_state["inbox_cache"], "Inbox is empty.", "inbox")

with tabs[1]:
    if st.button("🔄 Load unread", key="load_unread"):
        with st.spinner("Fetching unread…"):
            st.session_state["unread_cache"] = gmail.read_unread(max_results=max_n)
    email_list(st.session_state.get("unread_cache", []), "No unread emails 🎉", "unread")

with tabs[2]:
    st.caption("Use Gmail search syntax, e.g. `from:rahul newer_than:7d has:attachment`")
    query = st.text_input("Search query", placeholder="from:Rahul", key="search_q")
    if st.button("🔍 Search", key="do_search") and query:
        with st.spinner("Searching…"):
            st.session_state["search_results"] = gmail.search(query, max_results=max_n)
    email_list(st.session_state.get("search_results", []), "Run a search to see results.", "search")

with tabs[3]:
    with st.spinner("Loading labels…"):
        try:
            labels = gmail.list_labels()
        except Exception as exc:  # noqa: BLE001
            labels = []
            st.error(f"Could not load labels: {exc}")
    label = st.selectbox("Filter by label", options=labels or ["INBOX"], key="label_sel")
    if st.button("Apply label filter", key="do_label") and label:
        with st.spinner(f"Loading '{label}'…"):
            st.session_state["label_results"] = gmail.by_label(label, max_results=max_n)
    email_list(st.session_state.get("label_results", []), "Select a label and apply.", "label")

with tabs[4]:
    if st.button("⭐ Load starred", key="load_starred"):
        with st.spinner("Fetching starred…"):
            st.session_state["starred_cache"] = gmail.starred(max_results=max_n)
    email_list(st.session_state.get("starred_cache", []), "No starred emails.", "starred")

with tabs[5]:
    if st.button("❗ Load important", key="load_important"):
        with st.spinner("Fetching important…"):
            st.session_state["important_cache"] = gmail.important(max_results=max_n)
    email_list(st.session_state.get("important_cache", []), "No important emails.", "important")
