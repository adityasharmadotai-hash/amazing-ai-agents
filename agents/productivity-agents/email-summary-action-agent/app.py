"""
app.py
------
Entry point + navigation router.

Streamlit's automatic `pages/` discovery can silently fail with non-ASCII
filenames, so we define navigation explicitly with `st.navigation`. This is the
modern, reliable approach: pages always appear in the sidebar with the labels
and icons we choose, in the order we choose.

Run it with:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from src import database

# Page config must be set once, here in the entry point (not in each page).
st.set_page_config(
    page_title="Email Action Agent",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="expanded",
)

database.init_db()

# Shared styling, injected once so every page looks consistent.
st.markdown(
    """
    <style>
    .metric-card {
        padding: 1.15rem 1.3rem; border-radius: 16px; color: white;
        box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    }
    .metric-card h2 { margin: 0; font-size: 2rem; line-height: 1.1; }
    .metric-card p  { margin: .15rem 0 0; opacity: .9; font-size: .8rem; }
    .block-container { padding-top: 2.2rem; }
    section[data-testid="stSidebar"] { width: 320px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Define the pages explicitly.
dashboard_page = st.Page(
    "views/dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True
)
settings_page = st.Page(
    "views/settings.py", title="Settings", icon=":material/settings:"
)

# Grouped navigation renders a labeled section in the sidebar.
nav = st.navigation({"📬 Email Action Agent": [dashboard_page, settings_page]})
nav.run()
