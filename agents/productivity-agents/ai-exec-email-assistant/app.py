"""AI Executive Email Assistant — main entry point (Home dashboard).

Run with:  streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from config.settings import get_settings
from utils.theme import hero, metric_card, section_eyebrow
from utils.ui import (
    analytics_service,
    bootstrap,
    page_config,
    render_sidebar,
    require_auth,
)

bootstrap()
page_config("Home", "🏠")

settings = get_settings()
render_sidebar()

creds = require_auth()
if not creds:
    st.stop()

profile = st.session_state.get("profile", {})
name = profile.get("name") or settings.owner_name or "there"
first = name.split()[0] if name else "there"

hero(
    f"Welcome back, {first}",
    "Your AI-powered command center for email — triage, draft, and brief in one place.",
    eyebrow="Executive Dashboard",
)

# ---- Quick metrics ----
with st.spinner("Loading inbox snapshot…"):
    try:
        analytics = analytics_service().compute()
    except Exception as exc:  # noqa: BLE001
        st.warning(f"Couldn't load analytics yet: {exc}")
        analytics = None

if analytics:
    health = analytics.health_score
    hkind = "good" if health >= 70 else "warn" if health >= 40 else "bad"
    c1, c2, c3, c4 = st.columns(4)
    metric_card(c1, health, "Inbox Health", analytics.health_label, hkind)
    metric_card(c2, analytics.unread_count, "Unread")
    metric_card(c3, analytics.followup_count, "Need Follow-up")
    metric_card(c4, analytics.important_count, "Important")
    st.caption(f"{analytics.total_cached} emails cached · status **{analytics.health_label}**")
else:
    st.info("Open the **Inbox** page to fetch your email and populate the dashboard.")

st.write("")

# ---- Feature grid ----
section_eyebrow("Capabilities")
st.markdown("#### What you can do")

features = [
    ("📥", "Inbox", "Read, search, filter by label, view starred & important mail."),
    ("🤖", "AI Assistant", "Summaries, daily digest, weekly review, follow-up detection."),
    ("✍️", "Drafting", "Generate drafts, context-aware replies, tone rewriting."),
    ("🎤", "Voice", "Speak commands → transcribe → act on Gmail."),
    ("📋", "Briefing", "One-click morning executive briefing."),
    ("📊", "Analytics", "Inbox health, response time, volume, top contacts."),
    ("📤", "Export", "Download anything as PDF, DOCX, or Markdown."),
    ("⚙️", "Settings", "Configure keys, models, and personalization in-app."),
]
cols = st.columns(4)
for i, (icon, title, desc) in enumerate(features):
    with cols[i % 4]:
        st.markdown(
            f"<div class='feature'><div class='ficon'>{icon}</div>"
            f"<h4>{title}</h4><p>{desc}</p></div>",
            unsafe_allow_html=True,
        )
        st.write("")

st.divider()
st.caption(
    "⚡ Built with Streamlit + OpenAI + the Gmail API. "
    "Nothing is sent without your explicit action."
)
