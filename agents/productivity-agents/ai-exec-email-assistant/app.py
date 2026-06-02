"""AI Executive Email Assistant — main entry point (Home dashboard).

Run with:  streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from config.settings import get_settings
from utils.ui import (
    analytics_service,
    bootstrap,
    page_config,
    render_sidebar,
    require_auth,
)

bootstrap()
page_config("Home", "🏠")

CARD_CSS = """
<style>
.metric-card {
    background: linear-gradient(145deg, #1A1F2B 0%, #161A24 100%);
    border: 1px solid #2A3140; border-radius: 16px;
    padding: 18px 20px; box-shadow: 0 4px 18px rgba(0,0,0,0.25);
}
.metric-card h2 { margin: 0; font-size: 2.0rem; color: #4F8DFD; }
.metric-card p { margin: 4px 0 0; color: #9AA4B2; font-size: 0.85rem;
                 text-transform: uppercase; letter-spacing: 0.05em; }
.hero { padding: 6px 0 18px; }
.hero h1 { margin-bottom: 0; }
.feature { background:#161A24; border:1px solid #2A3140; border-radius:14px;
           padding:16px; height:100%; }
.feature h4 { margin:0 0 6px; color:#E6EAF1; }
.feature p { margin:0; color:#9AA4B2; font-size:0.88rem; }
</style>
"""

st.markdown(CARD_CSS, unsafe_allow_html=True)

settings = get_settings()
render_sidebar()

creds = require_auth()
if not creds:
    st.stop()

profile = st.session_state.get("profile", {})
name = profile.get("name") or settings.owner_name or "there"

st.markdown(
    f"<div class='hero'><h1>👋 Welcome back, {name}</h1>"
    f"<p style='color:#9AA4B2'>Your AI-powered executive command center.</p></div>",
    unsafe_allow_html=True,
)

# ---- Quick metrics ----
with st.spinner("Loading inbox snapshot…"):
    try:
        analytics = analytics_service().compute()
    except Exception as exc:  # noqa: BLE001
        st.warning(f"Couldn't load analytics yet: {exc}")
        analytics = None


def metric_card(col, value, label):
    col.markdown(
        f"<div class='metric-card'><h2>{value}</h2><p>{label}</p></div>",
        unsafe_allow_html=True,
    )


if analytics:
    c1, c2, c3, c4 = st.columns(4)
    metric_card(c1, f"{analytics.health_score}", "Inbox Health")
    metric_card(c2, analytics.unread_count, "Unread")
    metric_card(c3, analytics.followup_count, "Need Follow-up")
    metric_card(c4, analytics.important_count, "Important")
    st.caption(f"Inbox status: **{analytics.health_label}** · {analytics.total_cached} emails cached")
else:
    st.info("Open the **Inbox** page to fetch your email and populate the dashboard.")

st.divider()

# ---- Feature grid ----
st.subheader("What you can do")
features = [
    ("📥 Inbox", "Read, search, filter by label, view starred & important mail."),
    ("🤖 AI Assistant", "Summaries, daily digest, weekly review, follow-up detection."),
    ("✍️ Drafting", "Generate drafts, context-aware replies, tone rewriting."),
    ("🎤 Voice", "Speak commands → transcribe → act on Gmail."),
    ("📅 Calendar", "Upcoming meetings with prep briefs and talking points."),
    ("📋 Briefing", "One-click morning executive briefing."),
    ("📊 Analytics", "Inbox health, response time, volume, top contacts."),
    ("📤 Export", "Download anything as PDF, DOCX, or Markdown."),
]
cols = st.columns(4)
for i, (title, desc) in enumerate(features):
    with cols[i % 4]:
        st.markdown(
            f"<div class='feature'><h4>{title}</h4><p>{desc}</p></div>",
            unsafe_allow_html=True,
        )
        st.write("")

st.divider()
st.caption(
    "⚡ Built with Streamlit + OpenAI + Gmail & Calendar APIs. "
    "Use the sidebar to navigate. Nothing is sent without your explicit action."
)
