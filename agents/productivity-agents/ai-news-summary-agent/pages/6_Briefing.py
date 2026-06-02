"""📋 Daily Executive Briefing."""
from __future__ import annotations

import streamlit as st

from config.settings import get_settings
from database.models import get_latest_briefing
from services.briefing_service import BriefingService
from utils.components import export_buttons
from utils.ui import (
    bootstrap,
    calendar_service,
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
st.title("📋 Daily Executive Briefing")
st.caption("Synthesises important mail, follow-ups, and today's meetings into one brief.")

ai = safe_ai()
if ai is None:
    st.stop()
gmail = gmail_service()
cal = calendar_service()

profile = st.session_state.get("profile", {})
owner = profile.get("name") or settings.owner_name

if st.button("🚀 Generate today's briefing", type="primary"):
    with st.spinner("Reading inbox, triaging, checking calendar, writing briefing…"):
        try:
            service = BriefingService(gmail, cal, ai)
            st.session_state["briefing"] = service.generate(owner=owner)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to generate briefing: {exc}")

content = st.session_state.get("briefing")
if not content:
    latest = get_latest_briefing()
    if latest:
        st.info(f"Showing last saved briefing from {latest['created_at']}.")
        content = latest["content"]

if content:
    st.markdown(content)
    st.divider()
    export_buttons("Executive Briefing", content, "brief")
