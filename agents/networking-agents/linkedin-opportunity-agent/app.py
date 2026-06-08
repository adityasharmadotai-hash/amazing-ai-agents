"""
app.py — LinkedIn Opportunity Agent

An AI agent that monitors LinkedIn activity and surfaces high-value opportunities
— hiring signals, buying intent, partnerships, funding, leads, and networking —
then scores them, drafts outreach, and tracks analytics.

Run locally:   streamlit run app.py
Deploy:        Streamlit Cloud (add ANTHROPIC_API_KEY in Settings → Secrets)

Pages live in pages/ (home, opportunities, outreach, analytics, settings) and are
wired up via st.navigation for a single, clean sidebar.
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from modules import bootstrap, config  # noqa: E402
from modules import ui  # noqa: E402

st.set_page_config(
    page_title="LinkedIn Opportunity Agent",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Global styles + one-time initialisation / demo seeding.
ui.inject_css()
bootstrap.ensure_ready()

# ── Sidebar branding + status ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='padding:6px 4px 12px'>"
        "<div style='font-size:20px;font-weight:900;color:#fff'>🛰️ Opportunity Agent</div>"
        "<div style='font-size:12px;color:#9fb2c9'>LinkedIn signal radar</div></div>",
        unsafe_allow_html=True,
    )
    if config.ai_enabled():
        st.success(f"AI: {config.get_model()}", icon="✅")
    else:
        st.warning("AI off — using keyword engine. Add an API key in Settings.", icon="🔑")

# ── Navigation (pages/) ──────────────────────────────────────────────────────────
pages = [
    st.Page("pages/home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/opportunities.py", title="Opportunities", icon="🎯"),
    st.Page("pages/outreach.py", title="Outreach", icon="✍️"),
    st.Page("pages/analytics.py", title="Analytics", icon="📊"),
    st.Page("pages/settings.py", title="Settings", icon="⚙️"),
]

st.navigation(pages, position="sidebar").run()
