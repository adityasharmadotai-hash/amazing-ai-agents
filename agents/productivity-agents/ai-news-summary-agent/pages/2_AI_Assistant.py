"""🤖 AI Assistant — summaries, digests, follow-up detection."""
from __future__ import annotations

import streamlit as st

from database.models import update_email_ai_fields
from utils.components import export_buttons
from utils.helpers import run_async
from utils.ui import bootstrap, gmail_service, page_config, render_sidebar, require_auth, safe_ai

bootstrap()
page_config("AI Assistant", "🤖")
render_sidebar()
if not require_auth():
    st.stop()

st.title("🤖 AI Email Assistant")
gmail = gmail_service()
ai = safe_ai()
if ai is None:
    st.stop()

n = st.sidebar.slider("Emails to analyse", 5, 50, 20, step=5)

tab_sum, tab_digest, tab_week, tab_follow = st.tabs(
    ["Inbox Summary", "Daily Digest", "Weekly Summary", "Follow-ups & Importance"]
)

with tab_sum:
    if st.button("✨ Summarise inbox", key="sum_inbox"):
        with st.spinner("Reading and summarising…"):
            emails = gmail.read_inbox(max_results=n)
            st.session_state["inbox_summary"] = ai.summarize_inbox(emails)
    if "inbox_summary" in st.session_state:
        st.markdown(st.session_state["inbox_summary"])
        export_buttons("Inbox Summary", st.session_state["inbox_summary"], "sum")

with tab_digest:
    if st.button("📰 Generate daily digest", key="gen_digest"):
        with st.spinner("Building digest…"):
            emails = gmail.search("newer_than:1d in:inbox", max_results=n)
            st.session_state["digest"] = ai.daily_digest(emails)
    if "digest" in st.session_state:
        st.markdown(st.session_state["digest"])
        export_buttons("Daily Digest", st.session_state["digest"], "dig")

with tab_week:
    if st.button("🗓️ Generate weekly summary", key="gen_week"):
        with st.spinner("Analysing the week…"):
            emails = gmail.search("newer_than:7d in:inbox", max_results=n)
            st.session_state["weekly"] = ai.weekly_summary(emails)
    if "weekly" in st.session_state:
        st.markdown(st.session_state["weekly"])
        export_buttons("Weekly Summary", st.session_state["weekly"], "wk")

with tab_follow:
    st.caption("Classifies each email for importance and follow-up needs (runs concurrently).")
    if st.button("🔎 Triage inbox", key="triage"):
        with st.spinner("Classifying emails with AI…"):
            emails = gmail.read_inbox(max_results=n)
            results = run_async(ai.classify_batch(emails))
            triaged = []
            for e in emails:
                r = results.get(e.id, {})
                e.ai_summary = r.get("reason", "")
                e.priority_score = float(r.get("priority_score", 0) or 0)
                e.needs_followup = bool(r.get("needs_followup"))
                e.is_important = bool(r.get("is_important")) or e.is_important
                update_email_ai_fields(e.id, e.ai_summary, e.needs_followup, e.priority_score)
                triaged.append(e)
            triaged.sort(key=lambda x: x.priority_score, reverse=True)
            st.session_state["triaged"] = triaged

    triaged = st.session_state.get("triaged", [])
    if triaged:
        followups = [e for e in triaged if e.needs_followup]
        important = [e for e in triaged if e.is_important]
        c1, c2 = st.columns(2)
        c1.metric("Need follow-up", len(followups))
        c2.metric("Important", len(important))

        st.subheader("↩️ Emails needing follow-up")
        for e in followups[:15]:
            with st.container(border=True):
                st.markdown(f"**{e.subject}** — {e.sender}")
                st.caption(f"Priority {e.priority_score:.2f} · {e.ai_summary}")
                if st.button("Draft follow-up", key=f"sf_{e.id}"):
                    with st.spinner("Drafting…"):
                        st.session_state[f"fu_{e.id}"] = ai.suggest_followup(e)
                if f"fu_{e.id}" in st.session_state:
                    st.text_area("Suggested follow-up", st.session_state[f"fu_{e.id}"],
                                 height=160, key=f"fa_{e.id}")

        st.subheader("❗ Most important")
        for e in important[:10]:
            st.markdown(f"- **{e.subject}** — {e.sender} _(priority {e.priority_score:.2f})_")
