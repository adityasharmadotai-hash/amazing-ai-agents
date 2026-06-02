"""✍️ Smart Drafting — generate drafts, contextual replies, tone rewriting."""
from __future__ import annotations

import streamlit as st

from database.models import save_draft
from prompts.templates import TONE_GUIDE
from utils.components import export_buttons
from utils.ui import bootstrap, gmail_service, page_config, render_sidebar, require_auth, safe_ai

bootstrap()
page_config("Drafting", "✍️")
render_sidebar()
if not require_auth():
    st.stop()

st.title("✍️ Smart Drafting")
gmail = gmail_service()
ai = safe_ai()
if ai is None:
    st.stop()

TONES = list(TONE_GUIDE.keys())

tab_new, tab_reply, tab_rewrite = st.tabs(["New Draft", "Reply with Context", "Rewrite Tone"])

# ----------------------------- New draft -----------------------------
with tab_new:
    instructions = st.text_area(
        "What should this email say?",
        placeholder="Email to the board summarising Q2 results and proposing a Q3 hiring plan.",
        height=140, key="new_instr",
    )
    tone = st.selectbox("Tone", TONES, key="new_tone")
    recipient = st.text_input("To (optional)", key="new_to")
    if st.button("✨ Generate draft", key="gen_new") and instructions:
        with st.spinner("Writing…"):
            draft = ai.generate_draft(instructions, tone)
            st.session_state["new_draft"] = draft
    if "new_draft" in st.session_state:
        d = st.session_state["new_draft"]
        subject = st.text_input("Subject", d["subject"], key="new_subj")
        body = st.text_area("Body", d["body"], height=260, key="new_body")
        c1, c2 = st.columns(2)
        if c1.button("💾 Save draft locally", key="save_new"):
            save_draft(recipient, tone, subject, body)
            st.success("Saved to local drafts.")
        if c2.button("📧 Create Gmail draft", key="gmail_new"):
            if not recipient:
                st.warning("Add a recipient to create a Gmail draft.")
            else:
                try:
                    gmail.create_draft(recipient, subject, body)
                    st.success("Draft created in Gmail.")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Failed: {exc}")
        export_buttons(subject or "Draft", body, "newdraft")

# -------------------------- Reply w/ context -------------------------
with tab_reply:
    st.caption("Finds a thread, then replies using the full conversation as context.")
    search_q = st.text_input("Find the email to reply to", placeholder="from:Rahul proposal",
                             key="reply_search")
    if st.button("🔍 Find threads", key="find_reply") and search_q:
        with st.spinner("Searching…"):
            st.session_state["reply_candidates"] = gmail.search(search_q, max_results=10)

    candidates = st.session_state.get("reply_candidates", [])
    if candidates:
        labels = {f"{e.subject} — {e.sender}": e for e in candidates}
        choice = st.selectbox("Choose a thread", list(labels.keys()), key="reply_choice")
        selected = labels[choice]
        tone = st.selectbox("Tone", TONES, key="reply_tone")
        extra = st.text_input("Extra instructions (optional)", key="reply_extra")
        if st.button("✨ Draft contextual reply", key="gen_reply"):
            with st.spinner("Reading thread & drafting…"):
                thread = gmail.get_thread(selected.thread_id) or [selected]
                st.session_state["reply_body"] = ai.reply_with_context(thread, tone, extra)
                st.session_state["reply_target"] = selected
        if "reply_body" in st.session_state:
            body = st.text_area("Reply", st.session_state["reply_body"], height=240, key="reply_ta")
            tgt = st.session_state["reply_target"]
            if st.button("📧 Create Gmail draft reply", key="gmail_reply"):
                try:
                    gmail.create_draft(tgt.sender_email, f"Re: {tgt.subject}", body, tgt.thread_id)
                    st.success("Reply draft created in Gmail.")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Failed: {exc}")
            export_buttons(f"Reply to {tgt.subject}", body, "replydraft")

# ----------------------------- Rewrite -------------------------------
with tab_rewrite:
    original = st.text_area("Paste an email to rewrite", height=200, key="rw_orig")
    tone = st.selectbox("Rewrite in tone", TONES, key="rw_tone")
    if st.button("🔁 Rewrite", key="do_rewrite") and original:
        with st.spinner("Rewriting…"):
            st.session_state["rewritten"] = ai.rewrite_tone(original, tone)
    if "rewritten" in st.session_state:
        st.text_area("Rewritten", st.session_state["rewritten"], height=220, key="rw_out")
        export_buttons(f"Rewrite ({tone})", st.session_state["rewritten"], "rewrite")
