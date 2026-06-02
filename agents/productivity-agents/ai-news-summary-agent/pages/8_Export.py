"""📤 Export Center — turn any saved content into PDF / DOCX / Markdown."""
from __future__ import annotations

import streamlit as st

from database.models import get_latest_briefing, list_drafts
from utils.components import export_buttons
from utils.ui import bootstrap, page_config, render_sidebar, require_auth

bootstrap()
page_config("Export", "📤")
render_sidebar()
if not require_auth():
    st.stop()

st.title("📤 Export Center")
st.caption("Export briefings, drafts, or any custom text to PDF, DOCX, or Markdown.")

source = st.radio(
    "What do you want to export?",
    ["Custom text", "Latest briefing", "A saved draft"],
    horizontal=True,
)

title, content = "Export", ""

if source == "Custom text":
    title = st.text_input("Title", "My Document")
    content = st.text_area("Content (Markdown supported)", height=300)

elif source == "Latest briefing":
    latest = get_latest_briefing()
    if latest:
        title = f"Briefing {latest['brief_date']}"
        content = latest["content"]
        st.markdown(content)
    else:
        st.info("No briefing saved yet — generate one on the Briefing page.")

else:  # saved draft
    drafts = list_drafts(limit=30)
    if drafts:
        labels = {f"#{d['id']} · {d['subject'] or '(no subject)'} ({d['tone']})": d for d in drafts}
        choice = st.selectbox("Choose a draft", list(labels.keys()))
        d = labels[choice]
        title = d["subject"] or "Draft"
        content = d["body"]
        st.text_area("Preview", content, height=240, disabled=True)
    else:
        st.info("No saved drafts yet — create one on the Drafting page.")

if content:
    st.divider()
    export_buttons(title, content, "export_center")
