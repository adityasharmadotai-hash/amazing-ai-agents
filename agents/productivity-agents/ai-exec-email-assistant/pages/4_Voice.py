"""🎤 Voice Commands — speak → transcribe → route → act."""
from __future__ import annotations

import streamlit as st

from config.settings import get_settings
from utils.components import email_list
from utils.theme import hero
from utils.ui import bootstrap, gmail_service, page_config, render_sidebar, require_auth, safe_ai

bootstrap()
page_config("Voice", "🎤")
render_sidebar()
if not require_auth():
    st.stop()

settings = get_settings()
hero("Voice Commands", "Speak a command — the assistant transcribes and acts on Gmail.", eyebrow="Hands-free")

if not settings.enable_voice:
    st.warning("Voice is disabled. Set ENABLE_VOICE=true in your .env to use it.")
    st.stop()

ai = safe_ai()
if ai is None:
    st.stop()
gmail = gmail_service()

try:
    from services.voice_service import VoiceService

    voice = VoiceService()
except Exception as exc:  # noqa: BLE001
    st.error(f"Voice service unavailable: {exc}")
    st.stop()

st.markdown(
    "Try: *“Read my inbox”*, *“Show unread emails”*, *“Find emails from Rahul”*, "
    "*“What needs follow-up?”*, *“Draft a reply to the latest email.”*"
)

col_audio, col_text = st.columns(2)
transcript = None

with col_audio:
    st.caption("🎙️ Record a command")
    audio = st.audio_input("Speak now", key="voice_audio")
    if audio is not None and st.button("Transcribe & run", key="run_audio"):
        with st.spinner("Transcribing…"):
            transcript = voice.transcribe(audio.getvalue(), "command.wav")

with col_text:
    st.caption("⌨️ …or type a command")
    typed = st.text_input("Command", placeholder="Find emails from Rahul", key="voice_text")
    if st.button("Run command", key="run_text") and typed:
        transcript = typed

if transcript:
    st.success(f"📝 Heard: *{transcript}*")
    with st.spinner("Understanding…"):
        route = ai.route_voice_intent(transcript)
    intent = route.get("intent", "unknown")
    params = route.get("params", {})
    spoken = route.get("spoken_response", "")
    st.info(f"**Intent:** `{intent}` — {spoken}")

    # Optional spoken reply
    if spoken:
        audio_bytes = voice.synthesize(spoken)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3")

    # ---- Act on the intent ----
    n = settings.max_emails_fetch
    if intent == "read_inbox":
        email_list(gmail.read_inbox(max_results=20), "Inbox empty.", "v_inbox")
    elif intent == "read_unread":
        email_list(gmail.read_unread(max_results=20), "No unread mail.", "v_unread")
    elif intent == "search_emails":
        q = params.get("query", transcript)
        email_list(gmail.search(q, max_results=20), f"No results for '{q}'.", "v_search")
    elif intent == "summarize_inbox":
        st.markdown(ai.summarize_inbox(gmail.read_inbox(max_results=20)))
    elif intent == "followups":
        from utils.helpers import run_async
        emails = gmail.read_inbox(max_results=20)
        results = run_async(ai.classify_batch(emails))
        flagged = [e for e in emails if results.get(e.id, {}).get("needs_followup")]
        for e in flagged:
            e.needs_followup = True
            e.ai_summary = results.get(e.id, {}).get("reason", "")
        email_list(flagged, "Nothing needs follow-up 🎉", "v_follow")
    elif intent == "draft_reply":
        target = params.get("target", "")
        st.write(f"Searching for a thread matching: **{target or 'latest'}**")
        results = gmail.search(target or "in:inbox", max_results=5)
        if results:
            thread = gmail.get_thread(results[0].thread_id) or results[:1]
            st.text_area("Suggested reply", ai.reply_with_context(thread), height=200, key="v_reply")
        else:
            st.info("Couldn't find a matching thread.")
    elif intent == "daily_briefing":
        st.switch_page("pages/6_Briefing.py")
    else:
        st.warning("I didn't recognise that command. Try rephrasing.")
