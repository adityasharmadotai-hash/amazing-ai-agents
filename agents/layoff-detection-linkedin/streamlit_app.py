"""LayoffScout AI — Streamlit Cloud entry point / router.

Uses st.navigation so the sidebar shows clean, branded page names ("Dashboard",
"Settings") instead of raw filenames. Page config, the brand design system, and
the secrets→env bridge are set up here, once, before either page runs.

  streamlit_app.py     -> this router (page config, CSS, navigation)
  views/dashboard.py   -> the dashboard (scan, leads, cost, enrich)
  views/settings.py    -> all API keys + how to generate each one
"""
from __future__ import annotations

import streamlit as st

import st_common

st.set_page_config(page_title="LayoffScout AI", page_icon="🎯", layout="wide")
st_common.apply_brand()
st_common.bootstrap_env()

# Branded block at the very top of the sidebar, above the nav.
with st.sidebar:
    st_common.sidebar_brand()

pages = [
    st.Page("views/dashboard.py", title="Dashboard", icon="🎯", default=True),
    st.Page("views/settings.py", title="Settings", icon="⚙️"),
]
st.navigation(pages).run()

# Sidebar footer — brand links (rendered under the nav).
with st.sidebar:
    st.divider()
    st.markdown(
        "<div style='font-size:12px;line-height:1.9'>"
        "⭐ <a href='https://github.com/adityasharmadotai-hash/amazing-ai-agents' "
        "target='_blank'>Star the repo</a><br>"
        "💼 <a href='https://www.linkedin.com/in/aditya-hicounselor/' "
        "target='_blank'>Follow on LinkedIn</a><br>"
        "📺 <a href='https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ' "
        "target='_blank'>YouTube</a></div>",
        unsafe_allow_html=True,
    )
