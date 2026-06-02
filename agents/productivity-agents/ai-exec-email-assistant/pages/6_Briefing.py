"""📋 Daily Executive Briefing."""
from __future__ import annotations

import streamlit as st

from config.settings import get_settings
from database.models import get_latest_briefing
from utils.components import export_buttons
from utils.theme import hero
from utils.ui import (
    bootstrap,
    gmail_service,
    page_config,
    render_sidebar,
    require_auth,
    safe_ai,
)

bootstrap()
page_config("Briefing", "📋")
render_sidebar()
if not require_auth():
    st.stop()

settings = get_settings()
hero(
    "Daily Executive Briefing",
    "Your important mail and follow-ups, synthesised into one focused brief.",
    eyebrow="Morning Brief",
)

ai = safe_ai()
if ai is None:
    st.stop()
gmail = gmail_service()

profile = st.session_state.get("profile", {})
owner = profile.get("name") or settings.owner_name

if st.button("🚀 Generate today's briefing", type="primary"):
    with st.spinner("Reading inbox, triaging, and writing your briefing…"):
        try:
            from services.briefing_service import BriefingService

            service = BriefingService(gmail, ai)
            st.session_state["briefing"] = service.generate(owner=owner)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to generate briefing: {exc}")

content = st.session_state.get("briefing")
if not content:
    latest = get_latest_briefing()
    if latest:
        st.caption(f"Showing last saved briefing from {latest['created_at']}.")
        content = latest["content"]

if content:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown(content)
    st.markdown("</div>", unsafe_allow_html=True)
    st.write("")
    export_buttons("Executive Briefing", content, "brief")
else:
    st.info("Click **Generate today's briefing** to create your first brief.")
