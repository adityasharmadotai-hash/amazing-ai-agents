"""📅 Calendar — upcoming meetings with AI prep briefs."""
from __future__ import annotations

import streamlit as st

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
page_config("Calendar", "📅")
render_sidebar()
if not require_auth():
    st.stop()

st.title("📅 Calendar & Meeting Prep")
cal = calendar_service()
gmail = gmail_service()
ai = safe_ai()

days = st.sidebar.slider("Look ahead (days)", 1, 30, 7)

with st.spinner("Loading events…"):
    try:
        events = cal.upcoming_events(days_ahead=days, max_results=20)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not load calendar: {exc}")
        events = []

if not events:
    st.info("No upcoming events in this window.")
    st.stop()

st.caption(f"{len(events)} upcoming events in the next {days} day(s).")

for ev in events:
    with st.container(border=True):
        st.markdown(f"### {ev.title}")
        st.caption(f"🕒 {ev.when_str}" + (f" · 📍 {ev.location}" if ev.location else ""))
        if ev.attendees:
            st.write("**Attendees:** " + ", ".join(ev.attendees))
        if ev.hangout_link:
            st.markdown(f"[Join meeting]({ev.hangout_link})")

        if ai and st.button("🧠 Prepare meeting brief", key=f"brief_{ev.id}"):
            with st.spinner("Gathering context & writing brief…"):
                # Pull prior email history with each attendee.
                context_parts = []
                for attendee in ev.attendees[:5]:
                    try:
                        history = gmail.from_sender(attendee, max_results=3)
                        for h in history:
                            context_parts.append(
                                f"[{attendee}] {h.subject}: {h.snippet}"
                            )
                    except Exception:  # noqa: BLE001
                        continue
                brief = ai.meeting_brief(
                    title=ev.title,
                    when=ev.when_str,
                    attendees=ev.attendees,
                    email_context="\n".join(context_parts),
                )
                st.session_state[f"brief_out_{ev.id}"] = brief

        if f"brief_out_{ev.id}" in st.session_state:
            st.markdown(st.session_state[f"brief_out_{ev.id}"])
            export_buttons(f"Brief - {ev.title}",
                           st.session_state[f"brief_out_{ev.id}"], f"brief_{ev.id}")
