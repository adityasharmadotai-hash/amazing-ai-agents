"""LayoffScout AI — Streamlit Cloud entry point / router.

Uses st.navigation with CALLABLE pages (functions), not file paths. File-path
pages resolve relative to the entrypoint and are unreliable when the app lives
in a repo subdirectory (Streamlit Cloud reported "dashboard.py could not be
found"); callables sidestep path resolution entirely.

  streamlit_app.py     -> this router (page config, CSS, navigation)
  views/dashboard.py   -> render() for the dashboard
  views/settings.py    -> render() for the settings page
"""
from __future__ import annotations

import streamlit as st

import st_common

st.set_page_config(page_title="LayoffScout AI", page_icon="🎯", layout="wide")
st_common.apply_brand()
st_common.bootstrap_env()

# Import views AFTER bootstrap so their `from agent import config` sees the keys.
from views import dashboard, settings  # noqa: E402

# Branded block at the very top of the sidebar, above the nav.
with st.sidebar:
    st_common.sidebar_brand()

pages = [
    st.Page(dashboard.render, title="Dashboard", icon="🎯",
            url_path="dashboard", default=True),
    st.Page(settings.render, title="Settings", icon="⚙️", url_path="settings"),
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
