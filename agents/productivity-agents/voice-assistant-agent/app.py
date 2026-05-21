"""
app.py — AI Voice Assistant Agent (ARIA)
Full Streamlit application with voice input, AI chat, task management, and dashboard.
"""

import os
import sys
import uuid
import base64
from datetime import datetime

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ARIA — AI Voice Assistant",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #070b14 0%, #0d1117 50%, #0a0f1e 100%) !important;
}
[data-testid="stSidebar"] > div:first-child { background: transparent !important; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] div { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important; color: #cbd5e1 !important;
    font-size: 14px !important; font-weight: 500 !important;
    padding: 10px 14px !important; width: 100% !important;
    margin: 2px 0 !important; transition: all 0.18s !important;
    text-align: left !important; box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button p { color: #cbd5e1 !important; }
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(99,102,241,0.25) !important;
    border-color: rgba(99,102,241,0.5) !important; color: #fff !important;
}
[data-testid="stSidebar"] .stButton > button:hover p { color: #fff !important; }
[data-testid="stSidebar"] .nav-active > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border-left: 4px solid #a78bfa !important;
    border-top: 1px solid rgba(167,139,250,0.3) !important;
    border-right: 1px solid rgba(167,139,250,0.15) !important;
    border-bottom: 1px solid rgba(167,139,250,0.15) !important;
    color: #fff !important; font-weight: 700 !important;
    box-shadow: 0 4px 18px rgba(99,102,241,0.45) !important;
    transform: translateX(3px) !important;
}
[data-testid="stSidebar"] .nav-active > button p { color: #fff !important; }

/* ── Chat bubbles ── */
.bubble-user {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white; border-radius: 18px 18px 4px 18px;
    padding: 12px 18px; margin: 6px 0 6px 60px;
    font-size: 14px; line-height: 1.6;
    box-shadow: 0 2px 8px rgba(99,102,241,0.3);
}
.bubble-assistant {
    background: white; color: #0f172a;
    border: 1px solid #e2e8f0;
    border-radius: 18px 18px 18px 4px;
    padding: 12px 18px; margin: 6px 60px 6px 0;
    font-size: 14px; line-height: 1.6;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.bubble-meta {
    font-size: 11px; color: #94a3b8; margin: 2px 4px;
}
.bubble-meta-right { text-align: right; }

/* ── Voice button ── */
.voice-ring {
    display: flex; align-items: center; justify-content: center;
    width: 80px; height: 80px; border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    box-shadow: 0 0 0 8px rgba(99,102,241,0.15), 0 8px 24px rgba(99,102,241,0.4);
    margin: 0 auto; cursor: pointer; font-size: 32px;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 8px rgba(99,102,241,0.15), 0 8px 24px rgba(99,102,241,0.4); }
    50% { box-shadow: 0 0 0 16px rgba(99,102,241,0.08), 0 8px 32px rgba(99,102,241,0.5); }
}

/* ── Cards ── */
.glass-card {
    background: white; border: 1px solid #e2e8f0;
    border-radius: 14px; padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 12px;
}
.metric-card {
    background: white; border-radius: 14px; padding: 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    border-top: 4px solid #6366f1; text-align: center;
}
.metric-card .val { font-size: 28px; font-weight: 800; color: #0f172a; }
.metric-card .lbl { font-size: 11px; color: #64748b; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }

/* ── Section header ── */
.section-hdr {
    background: linear-gradient(90deg, #6366f1, #8b5cf6);
    color: white; border-radius: 10px; padding: 11px 18px;
    margin: 18px 0 14px; font-size: 15px; font-weight: 600;
}

/* ── Badges ── */
.badge { display:inline-block; padding:3px 10px; border-radius:20px;
    font-size:11px; font-weight:600; margin:2px; }
.badge-high   { background:#fef2f2; color:#dc2626; border:1px solid #fecaca; }
.badge-medium { background:#fffbeb; color:#d97706; border:1px solid #fde68a; }
.badge-low    { background:#f0fdf4; color:#16a34a; border:1px solid #bbf7d0; }
.badge-info   { background:#eff6ff; color:#2563eb; border:1px solid #bfdbfe; }
.badge-done   { background:#f0fdf4; color:#16a34a; border:1px solid #bbf7d0; }
.badge-pending{ background:#fafafa; color:#6b7280; border:1px solid #d1d5db; }

/* ── Intent chip ── */
.intent-chip {
    display:inline-block; padding:2px 8px; border-radius:12px;
    font-size:10px; font-weight:600; background:#eff6ff;
    color:#3730a3; border:1px solid #c7d2fe; margin-left:6px;
}

/* ── Task row ── */
.task-row {
    background:white; border:1px solid #e2e8f0; border-radius:10px;
    padding:12px 16px; margin:6px 0; display:flex;
    align-items:center; gap:10px;
}
.task-done { opacity:0.55; }

/* ── Transcript box ── */
.transcript-box {
    background:#0f172a; color:#a5f3fc; border-radius:12px;
    padding:16px; font-family:monospace; font-size:14px;
    line-height:1.7; min-height:60px; white-space:pre-wrap;
}

/* ── Input bar ── */
[data-testid="stChatInput"] { border-radius: 14px !important; }

/* ── Text area ── */
[data-testid="stTextArea"] textarea {
    background:#0f172a !important; color:#e2e8f0 !important;
    font-size:13px !important; border-radius:10px !important;
    border:1px solid #1e293b !important;
}

/* ── Nav divider ── */
.nav-div { height:1px; background:rgba(255,255,255,0.08); margin:10px 0; }

/* ── Status dot ── */
.dot-green { width:8px;height:8px;border-radius:50%;background:#22c55e;
    display:inline-block;margin-right:6px; }
.dot-red   { width:8px;height:8px;border-radius:50%;background:#ef4444;
    display:inline-block;margin-right:6px; }

/* ── Recorder area ── */
.rec-area {
    background:linear-gradient(135deg,#1e1b4b,#312e81);
    border-radius:16px; padding:32px; text-align:center; margin:16px 0;
}

#MainMenu, footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ── Imports ───────────────────────────────────────────────────────────────────
from modules.agent import is_configured, chat as ai_chat, generate_note_from_text, web_search_answer
from modules.stt import transcribe_bytes, transcribe_uploaded
from modules.tts import synthesize, audio_to_html, VOICES, VOICE_DESCRIPTIONS
from modules.tasks import (
    init_stores, add_task, complete_task, delete_task, get_tasks,
    add_note, delete_note, get_notes,
    add_reminder, dismiss_reminder, get_reminders,
    add_calendar_event, get_calendar_events, delete_calendar_event,
    get_analytics,
)
from modules.database import is_configured as db_ok, save_message, get_analytics_from_db

init_stores()

# ── Session state ─────────────────────────────────────────────────────────────
def _ss(k, v=None):
    if k not in st.session_state:
        st.session_state[k] = v

_ss("page", "🎙️ Voice Chat")
_ss("conversation", [])
_ss("session_id", str(uuid.uuid4())[:8])
_ss("user_api_key", "")
_ss("tts_enabled", True)
_ss("tts_voice", "nova")
_ss("tts_speed", 1.0)
_ss("last_audio", None)
_ss("pending_transcript", "")

# ── API key helpers ───────────────────────────────────────────────────────────
def _active_key() -> str:
    sk = st.session_state.get("user_api_key", "").strip()
    if sk:
        return sk
    try:
        return st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    except Exception:
        return os.environ.get("OPENAI_API_KEY", "")

def _sync_key():
    k = _active_key()
    if k:
        os.environ["OPENAI_API_KEY"] = k

_sync_key()

# ── Nav ───────────────────────────────────────────────────────────────────────
NAV = [
    ("🎙️", "Voice Chat"),
    ("💬", "Chat History"),
    ("✅", "Tasks"),
    ("📝", "Notes"),
    ("🔔", "Reminders"),
    ("📅", "Calendar"),
    ("📊", "Dashboard"),
    ("⚙️", "Settings"),
]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    has_key = bool(_active_key())
    status_dot = '<span class="dot-green"></span>' if has_key else '<span class="dot-red"></span>'

    st.markdown(f"""
    <div style="padding:20px 4px 16px;text-align:center;">
        <div style="font-size:48px;">🤖</div>
        <div style="font-size:18px;font-weight:800;color:white;margin-top:8px;letter-spacing:-0.3px;">
            ARIA
        </div>
        <div style="font-size:11px;color:#475569;margin-top:3px;">AI Voice Assistant</div>
        <div style="font-size:11px;margin-top:8px;color:#94a3b8;">
            {status_dot}{"Ready" if has_key else "No API key — Settings"}
        </div>
    </div>
    <div class="nav-div"></div>
    <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:0.1em;
                font-weight:600;padding:0 4px;margin-bottom:6px;">Navigation</div>
    """, unsafe_allow_html=True)

    current = st.session_state.get("page", "🎙️ Voice Chat")
    for icon, label in NAV:
        full = f"{icon} {label}"
        is_active = (current == full)
        if is_active:
            st.markdown('<div class="nav-active">', unsafe_allow_html=True)
        lbl = f"✦  {icon}  {label}" if is_active else f"{icon}  {label}"
        if st.button(lbl, key=f"nav_{label}", use_container_width=True):
            st.session_state.page = full
            st.rerun()
        if is_active:
            st.markdown('</div>', unsafe_allow_html=True)

    page = st.session_state.get("page", "🎙️ Voice Chat")

    # Session stats
    conv_len = len(st.session_state.conversation)
    task_count = len(get_tasks("pending"))
    st.markdown(f"""
    <div class="nav-div"></div>
    <div style="display:flex;gap:8px;padding:0 2px;">
        <div style="flex:1;background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.3);
                    border-radius:8px;padding:8px;text-align:center;">
            <div style="font-size:16px;font-weight:700;color:white;">{conv_len}</div>
            <div style="font-size:10px;color:#64748b;">Messages</div>
        </div>
        <div style="flex:1;background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.3);
                    border-radius:8px;padding:8px;text-align:center;">
            <div style="font-size:16px;font-weight:700;color:white;">{task_count}</div>
            <div style="font-size:10px;color:#64748b;">Tasks</div>
        </div>
    </div>
    <div class="nav-div"></div>
    <div style="font-size:11px;color:#334155;text-align:center;padding:4px 0 8px;">
        Built with ❤️ by
        <a href="https://www.adityasharma.ai" target="_blank"
           style="color:#818cf8;text-decoration:none;">adityasharma.ai</a>
    </div>
    """, unsafe_allow_html=True)


# ── Guard: require key for all pages except Settings ─────────────────────────
if page != "⚙️ Settings" and not _active_key():
    st.markdown("""
    <div style="background:#fef2f2;border:2px solid #fca5a5;border-radius:16px;
                padding:36px;max-width:540px;margin:80px auto;text-align:center;">
        <div style="font-size:52px;">🔑</div>
        <h2 style="color:#dc2626;margin:12px 0 8px;">API Key Required</h2>
        <p style="color:#7f1d1d;font-size:15px;">
            Go to <strong>⚙️ Settings</strong> in the sidebar<br>
            to enter your OpenAI API key.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.info("👈 Click **⚙️ Settings** in the sidebar")
    st.stop()


# ── Helper: process message ───────────────────────────────────────────────────
def _process_message(user_text: str, is_audio: bool = False):
    """Send user message to AI, handle intent, update session state."""
    if not user_text.strip():
        return

    # Add to conversation
    st.session_state.conversation.append({
        "role": "user",
        "content": user_text,
        "time": datetime.now().strftime("%H:%M"),
        "audio": is_audio,
    })

    # Save to DB
    if db_ok():
        save_message(st.session_state.session_id, "user", user_text, audio_used=is_audio)

    # Build context from tasks/notes for the AI
    tasks = get_tasks("pending")
    context_parts = []
    if tasks:
        context_parts.append("CURRENT TASKS: " + "; ".join(t["task"] for t in tasks[:5]))
    notes = get_notes()
    if notes:
        context_parts.append("RECENT NOTES: " + "; ".join(n["title"] for n in notes[:3]))
    context = "\n".join(context_parts)

    # AI response
    result = ai_chat(
        user_text,
        st.session_state.conversation[:-1],
        context=context,
    )
    response_text = result["response"]
    intent = result.get("intent", {"type": "CHAT"})
    intent_type = intent.get("type", "CHAT")
    intent_data = intent.get("data", {})

    # ── Execute intent ──
    action_msg = ""
    if intent_type == "CREATE_TASK" and intent_data.get("task"):
        task = add_task(
            intent_data["task"],
            intent_data.get("deadline", ""),
            intent_data.get("priority", "Medium"),
        )
        action_msg = f"✅ Task added: **{task['task']}**"

    elif intent_type == "CREATE_NOTE" and intent_data.get("content"):
        note = add_note(
            intent_data.get("title", "Note"),
            intent_data["content"],
        )
        action_msg = f"📝 Note saved: **{note['title']}**"

    elif intent_type == "CREATE_REMINDER" and intent_data.get("reminder"):
        rem = add_reminder(intent_data["reminder"], intent_data.get("time", ""))
        action_msg = f"🔔 Reminder set: **{rem['reminder']}**"

    elif intent_type == "CALENDAR_EVENT" and intent_data.get("title"):
        evt = add_calendar_event(
            intent_data["title"],
            intent_data.get("date", ""),
            intent_data.get("time", ""),
        )
        action_msg = f"📅 Event added: **{evt['title']}** on {evt['date']}"

    elif intent_type == "SEARCH_WEB" and intent_data.get("query"):
        search_result = web_search_answer(intent_data["query"])
        response_text = response_text + "\n\n" + search_result

    # Append action confirmation to response
    if action_msg:
        response_text = response_text + f"\n\n{action_msg}"

    # Add assistant response
    st.session_state.conversation.append({
        "role": "assistant",
        "content": response_text,
        "intent": intent_type,
        "time": datetime.now().strftime("%H:%M"),
        "audio": False,
    })

    if db_ok():
        save_message(st.session_state.session_id, "assistant", response_text, intent_type)

    # TTS
    if st.session_state.tts_enabled:
        clean_for_tts = response_text.replace("**", "").replace("✅", "").replace("📝", "").replace("🔔", "").replace("📅", "")
        audio_bytes = synthesize(clean_for_tts, st.session_state.tts_voice, st.session_state.tts_speed)
        st.session_state.last_audio = audio_bytes

    st.session_state.pending_transcript = ""


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: VOICE CHAT
# ═════════════════════════════════════════════════════════════════════════════
if page == "🎙️ Voice Chat":
    st.markdown("""
    <div style="padding:4px 0 20px;">
        <h1 style="font-size:28px;font-weight:800;color:#0f172a;margin:0;">
            🤖 ARIA — AI Voice Assistant
        </h1>
        <p style="color:#64748b;font-size:14px;margin-top:4px;">
            Talk or type • ARIA creates tasks, notes, reminders, and calendar events automatically
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_chat, col_voice = st.columns([3, 2])

    # ── Left: Chat interface ──
    with col_chat:
        # Conversation display
        chat_container = st.container()
        with chat_container:
            if not st.session_state.conversation:
                st.markdown("""
                <div style="text-align:center;padding:40px 20px;color:#94a3b8;">
                    <div style="font-size:48px;margin-bottom:16px;">🤖</div>
                    <div style="font-size:16px;font-weight:600;color:#475569;">Hi! I'm ARIA.</div>
                    <div style="font-size:13px;margin-top:8px;line-height:1.7;">
                        I can help you manage tasks, take notes,<br>
                        set reminders, schedule events, and answer questions.<br><br>
                        <strong>Try saying:</strong> "Add a task to review the proposal by Friday"
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                for msg in st.session_state.conversation:
                    role = msg["role"]
                    content = msg["content"]
                    time_str = msg.get("time", "")
                    intent = msg.get("intent", "")
                    is_audio_msg = msg.get("audio", False)

                    if role == "user":
                        audio_icon = "🎙️ " if is_audio_msg else ""
                        st.markdown(f"""
                        <div class="bubble-meta bubble-meta-right">
                            {audio_icon}{time_str}
                        </div>
                        <div class="bubble-user">{content}</div>
                        """, unsafe_allow_html=True)
                    else:
                        intent_html = f'<span class="intent-chip">{intent}</span>' if intent and intent != "CHAT" else ""
                        st.markdown(f"""
                        <div class="bubble-meta">🤖 ARIA {time_str} {intent_html}</div>
                        <div class="bubble-assistant">{content.replace(chr(10), "<br>")}</div>
                        """, unsafe_allow_html=True)

        # TTS playback
        if st.session_state.last_audio:
            st.markdown(audio_to_html(st.session_state.last_audio, autoplay=True), unsafe_allow_html=True)
            st.session_state.last_audio = None

        # Pre-filled from voice
        prefill = st.session_state.get("pending_transcript", "")

        # Text input
        user_input = st.chat_input("Type a message or use voice input →", key="chat_in")
        if user_input:
            _process_message(user_input, is_audio=False)
            st.rerun()

        # Quick actions
        st.markdown("**Quick actions:**")
        qa1, qa2, qa3, qa4 = st.columns(4)
        quick_map = {
            "📋 My Tasks": "What are my current tasks?",
            "📝 New Note": "I want to create a new note",
            "🔔 Remind Me": "Set a reminder for me",
            "📅 Schedule": "Add a calendar event",
        }
        for col, (label, prompt) in zip([qa1, qa2, qa3, qa4], quick_map.items()):
            with col:
                if st.button(label, use_container_width=True, key=f"qa_{label}"):
                    _process_message(prompt)
                    st.rerun()

        if st.session_state.conversation:
            if st.button("🗑️ Clear Chat", use_container_width=False):
                st.session_state.conversation = []
                st.session_state.last_audio = None
                st.rerun()

    # ── Right: Voice Input ──
    with col_voice:
        st.markdown('<div class="section-hdr">🎙️ Voice Input</div>', unsafe_allow_html=True)

        tab_upload, tab_type = st.tabs(["📁 Upload Audio", "⌨️ Type & Convert"])

        with tab_upload:
            st.markdown("""
            <div class="rec-area">
                <div style="font-size:40px;margin-bottom:10px;">🎙️</div>
                <div style="color:white;font-weight:600;font-size:15px;">Upload Audio Recording</div>
                <div style="color:#94a3b8;font-size:12px;margin-top:6px;">
                    MP3 · WAV · M4A · OGG · WebM · FLAC
                </div>
            </div>
            """, unsafe_allow_html=True)

            uploaded = st.file_uploader(
                "Drop audio file",
                type=["mp3", "wav", "m4a", "ogg", "webm", "flac"],
                label_visibility="collapsed",
            )

            lang_opt = st.selectbox(
                "Language",
                ["auto", "en", "es", "fr", "de", "it", "pt", "hi", "zh", "ja", "ar"],
                index=1,
                key="stt_lang",
            )

            if uploaded and st.button("🎙️ Transcribe & Send", type="primary", use_container_width=True):
                with st.spinner("🎙️ Transcribing with Whisper..."):
                    result = transcribe_uploaded(uploaded)
                if "error" in result:
                    st.error(result["error"])
                elif result.get("text"):
                    text = result["text"]
                    st.markdown(f'<div class="transcript-box">{text}</div>', unsafe_allow_html=True)
                    st.caption(f"Detected: {result.get('language','?').upper()} · {result.get('duration',0):.1f}s")
                    _process_message(text, is_audio=True)
                    st.rerun()
                else:
                    st.warning("No speech detected in the audio.")

        with tab_type:
            st.markdown("Type text and convert to voice or send as message:")
            typed_voice = st.text_area(
                "Text",
                placeholder="Type what you want to say...",
                height=120,
                label_visibility="collapsed",
                key="typed_voice_input",
            )
            tv1, tv2 = st.columns(2)
            with tv1:
                if st.button("💬 Send", type="primary", use_container_width=True) and typed_voice:
                    _process_message(typed_voice)
                    st.rerun()
            with tv2:
                if st.button("🔊 Speak", use_container_width=True) and typed_voice:
                    audio = synthesize(typed_voice, st.session_state.tts_voice, st.session_state.tts_speed)
                    if audio:
                        st.markdown(audio_to_html(audio, autoplay=True), unsafe_allow_html=True)

        # ── TTS Settings ──
        st.markdown('<div class="section-hdr">🔊 Voice Settings</div>', unsafe_allow_html=True)
        tts_on = st.toggle("Auto-speak responses", value=st.session_state.tts_enabled)
        st.session_state.tts_enabled = tts_on

        if tts_on:
            voice_names = list(VOICES.keys())
            voice_keys = list(VOICES.values())
            current_voice_idx = voice_keys.index(st.session_state.tts_voice) if st.session_state.tts_voice in voice_keys else 4
            sel_voice = st.selectbox(
                "Voice",
                voice_names,
                index=current_voice_idx,
                format_func=lambda v: f"{v} — {VOICE_DESCRIPTIONS[VOICES[v]]}",
            )
            st.session_state.tts_voice = VOICES[sel_voice]
            speed = st.slider("Speed", 0.5, 2.0, st.session_state.tts_speed, 0.1)
            st.session_state.tts_speed = speed

            if st.button("▶ Test Voice", use_container_width=True):
                test_audio = synthesize(f"Hi! I'm ARIA, your AI voice assistant. Ready to help!", st.session_state.tts_voice, speed)
                if test_audio:
                    st.markdown(audio_to_html(test_audio, autoplay=True), unsafe_allow_html=True)

        # Active reminders
        active_reminders = get_reminders(active_only=True)
        if active_reminders:
            st.markdown('<div class="section-hdr">🔔 Active Reminders</div>', unsafe_allow_html=True)
            for r in active_reminders[:3]:
                rc1, rc2 = st.columns([3, 1])
                with rc1:
                    st.markdown(f'<div style="font-size:13px;color:#374151;">🔔 {r["reminder"]}<br><small style="color:#94a3b8;">{r["time"]}</small></div>', unsafe_allow_html=True)
                with rc2:
                    if st.button("✓", key=f"dis_{r['id']}"):
                        dismiss_reminder(r["id"])
                        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: CHAT HISTORY
# ═════════════════════════════════════════════════════════════════════════════
elif page == "💬 Chat History":
    st.markdown('<h1 style="color:#0f172a;">💬 Chat History</h1>', unsafe_allow_html=True)

    conversation = st.session_state.conversation
    if not conversation:
        st.info("No messages yet. Start a conversation in Voice Chat!")
        st.stop()

    st.markdown(f"**{len(conversation)} messages** in current session")

    # Export
    export_text = "\n\n".join(
        f"[{msg.get('time','')}] {msg['role'].upper()}: {msg['content']}"
        for msg in conversation
    )
    st.download_button("⬇️ Export Chat (.txt)", data=export_text,
                       file_name="aria_chat_history.txt", mime="text/plain")

    st.markdown("---")
    for msg in reversed(conversation):
        role = msg["role"]
        icon = "👤" if role == "user" else "🤖"
        intent = msg.get("intent", "")
        bg = "#eff6ff" if role == "user" else "#f8fafc"
        border = "#bfdbfe" if role == "user" else "#e2e8f0"
        intent_html = f'<span class="intent-chip">{intent}</span>' if intent and intent != "CHAT" else ""
        audio_icon = "🎙️" if msg.get("audio") else ""

        st.markdown(f"""
        <div style="background:{bg};border:1px solid {border};border-radius:12px;
                    padding:14px 18px;margin:8px 0;">
            <div style="font-size:12px;color:#94a3b8;margin-bottom:6px;">
                {icon} {role.upper()} · {msg.get('time','')} {audio_icon} {intent_html}
            </div>
            <div style="font-size:14px;color:#0f172a;line-height:1.6;">
                {msg['content'].replace(chr(10),'<br>')}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: TASKS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "✅ Tasks":
    st.markdown('<h1 style="color:#0f172a;">✅ Task Manager</h1>', unsafe_allow_html=True)

    # Add task form
    with st.expander("➕ Add New Task", expanded=False):
        tc1, tc2, tc3 = st.columns([3, 2, 1])
        with tc1:
            new_task = st.text_input("Task", placeholder="What needs to be done?", key="new_task_input")
        with tc2:
            new_deadline = st.text_input("Deadline", placeholder="e.g. Friday, 2025-06-01", key="new_task_dl")
        with tc3:
            new_priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1, key="new_task_pri")
        if st.button("Add Task", type="primary") and new_task:
            add_task(new_task, new_deadline, new_priority)
            st.success(f"✅ Added: {new_task}")
            st.rerun()

    # Task list
    all_tasks = get_tasks("all")
    pending = [t for t in all_tasks if t["status"] == "pending"]
    done = [t for t in all_tasks if t["status"] == "done"]

    col_p, col_d = st.columns(2)

    with col_p:
        st.markdown(f'<div class="section-hdr">⏳ Pending ({len(pending)})</div>', unsafe_allow_html=True)
        if not pending:
            st.success("All caught up! No pending tasks.")
        for t in pending:
            p_class = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(t.get("priority","Medium"), "badge-medium")
            st.markdown(f"""
            <div style="background:white;border:1px solid #e2e8f0;border-left:4px solid #6366f1;
                        border-radius:10px;padding:12px 16px;margin:6px 0;">
                <div style="font-weight:600;color:#0f172a;font-size:14px;">{t['task']}</div>
                <div style="font-size:12px;color:#64748b;margin-top:4px;display:flex;gap:10px;">
                    <span class="badge {p_class}">{t.get('priority','Medium')}</span>
                    {"<span>📅 " + t['deadline'] + "</span>" if t.get('deadline') else ""}
                    <span>🕐 {t['created_at']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            pc1, pc2 = st.columns(2)
            with pc1:
                if st.button("✓ Done", key=f"done_{t['id']}", use_container_width=True):
                    complete_task(t["id"])
                    st.rerun()
            with pc2:
                if st.button("🗑️", key=f"deltask_{t['id']}", use_container_width=True):
                    delete_task(t["id"])
                    st.rerun()

    with col_d:
        st.markdown(f'<div class="section-hdr">✅ Completed ({len(done)})</div>', unsafe_allow_html=True)
        if not done:
            st.info("No completed tasks yet.")
        for t in done:
            st.markdown(f"""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;
                        padding:12px 16px;margin:6px 0;opacity:0.7;">
                <div style="font-weight:600;color:#374151;font-size:14px;
                            text-decoration:line-through;">✅ {t['task']}</div>
                <div style="font-size:11px;color:#94a3b8;margin-top:4px;">
                    Done: {t.get('completed_at','')[:16]}
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🗑️", key=f"deldone_{t['id']}", use_container_width=False):
                delete_task(t["id"])
                st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: NOTES
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📝 Notes":
    st.markdown('<h1 style="color:#0f172a;">📝 Notes</h1>', unsafe_allow_html=True)

    col_new, col_list = st.columns([2, 3])

    with col_new:
        st.markdown('<div class="section-hdr">✍️ New Note</div>', unsafe_allow_html=True)
        note_title = st.text_input("Title", placeholder="Note title...", key="note_title")
        note_tag = st.selectbox("Tag", ["General", "Meeting", "Idea", "Action", "Research", "Personal"])
        note_style = st.selectbox("Format from voice", ["bullet", "summary", "action", "formal"])
        note_content = st.text_area("Content", placeholder="Start typing or paste text to auto-format...", height=180, label_visibility="collapsed", key="note_content")

        nc1, nc2 = st.columns(2)
        with nc1:
            if st.button("💾 Save Note", type="primary", use_container_width=True) and note_content:
                add_note(note_title or f"Note {datetime.now().strftime('%H:%M')}", note_content, note_tag)
                st.success("✅ Saved!")
                st.rerun()
        with nc2:
            if st.button("✨ AI Format", use_container_width=True) and note_content:
                with st.spinner("Formatting..."):
                    formatted = generate_note_from_text(note_content, note_style)
                st.text_area("Formatted:", value=formatted, height=200, key="formatted_note")

    with col_list:
        st.markdown('<div class="section-hdr">📋 Saved Notes</div>', unsafe_allow_html=True)
        notes = get_notes()
        if not notes:
            st.info("No notes yet. Create one or ask ARIA to take a note!")
        for n in notes:
            tag_colors = {"Meeting":"#4f46e5","Idea":"#f59e0b","Action":"#dc2626","Research":"#0ea5e9","Personal":"#10b981","General":"#6b7280"}
            tc = tag_colors.get(n.get("tag","General"), "#6b7280")
            with st.expander(f"📄 {n['title']} — {n['created_at']}"):
                st.markdown(f'<span style="background:{tc};color:white;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;">{n.get("tag","General")}</span>', unsafe_allow_html=True)
                st.text_area("", value=n["content"], height=150, key=f"note_view_{n['id']}", label_visibility="collapsed")
                nc1, nc2, nc3 = st.columns(3)
                with nc1:
                    st.download_button("⬇️ TXT", data=n["content"], file_name=f"{n['title']}.txt", key=f"dln_{n['id']}", use_container_width=True)
                with nc3:
                    if st.button("🗑️ Delete", key=f"delnote_{n['id']}", use_container_width=True):
                        delete_note(n["id"])
                        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: REMINDERS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔔 Reminders":
    st.markdown('<h1 style="color:#0f172a;">🔔 Reminders</h1>', unsafe_allow_html=True)

    with st.expander("➕ Add Reminder", expanded=True):
        rc1, rc2 = st.columns([3, 2])
        with rc1:
            rem_text = st.text_input("Reminder", placeholder="e.g. Call the doctor", key="rem_text")
        with rc2:
            rem_time = st.text_input("Time / Date", placeholder="e.g. Tomorrow 9 AM, 2025-06-01", key="rem_time")
        if st.button("Set Reminder", type="primary") and rem_text:
            add_reminder(rem_text, rem_time)
            st.success(f"🔔 Reminder set!")
            st.rerun()

    active = get_reminders(active_only=True)
    dismissed = get_reminders(active_only=False)
    dismissed = [r for r in dismissed if r["status"] == "dismissed"]

    st.markdown(f'<div class="section-hdr">🔔 Active Reminders ({len(active)})</div>', unsafe_allow_html=True)
    if not active:
        st.success("No active reminders. You're all set!")
    for r in active:
        st.markdown(f"""
        <div style="background:white;border:1px solid #fde68a;border-left:4px solid #f59e0b;
                    border-radius:10px;padding:14px 18px;margin:8px 0;">
            <div style="font-weight:600;color:#0f172a;font-size:14px;">🔔 {r['reminder']}</div>
            <div style="font-size:12px;color:#64748b;margin-top:4px;">
                ⏰ {r['time']} &nbsp;·&nbsp; Set: {r['created_at']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"✓ Dismiss", key=f"rem_dis_{r['id']}"):
            dismiss_reminder(r["id"])
            st.rerun()

    if dismissed:
        st.markdown(f'<div class="section-hdr">✅ Dismissed ({len(dismissed)})</div>', unsafe_allow_html=True)
        for r in dismissed:
            st.markdown(f'<div style="opacity:0.5;font-size:13px;padding:6px 0;">✓ {r["reminder"]} — {r["time"]}</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: CALENDAR
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📅 Calendar":
    st.markdown('<h1 style="color:#0f172a;">📅 Calendar</h1>', unsafe_allow_html=True)

    with st.expander("➕ Add Event", expanded=False):
        ev1, ev2, ev3 = st.columns([3, 2, 2])
        with ev1:
            ev_title = st.text_input("Event", placeholder="Meeting with team", key="ev_title")
        with ev2:
            ev_date = st.date_input("Date", key="ev_date")
        with ev3:
            ev_time = st.text_input("Time", placeholder="2:00 PM", key="ev_time")
        ev_notes = st.text_input("Notes (optional)", key="ev_notes")
        if st.button("Add Event", type="primary") and ev_title:
            add_calendar_event(ev_title, str(ev_date), ev_time, ev_notes)
            st.success(f"📅 Added: {ev_title}")
            st.rerun()

    events = get_calendar_events()
    today = datetime.now().strftime("%Y-%m-%d")
    upcoming = [e for e in events if e.get("date", "") >= today]
    past = [e for e in events if e.get("date", "") < today]

    st.markdown(f'<div class="section-hdr">📅 Upcoming Events ({len(upcoming)})</div>', unsafe_allow_html=True)
    if not upcoming:
        st.info("No upcoming events. Ask ARIA to schedule one!")
    for e in upcoming:
        diff_days = (datetime.strptime(e["date"], "%Y-%m-%d") - datetime.now()).days if e.get("date") else 0
        timing = "Today! 🎯" if diff_days == 0 else f"In {diff_days} day{'s' if diff_days != 1 else ''}"
        st.markdown(f"""
        <div style="background:white;border:1px solid #e2e8f0;border-left:4px solid #6366f1;
                    border-radius:10px;padding:14px 18px;margin:8px 0;display:flex;
                    justify-content:space-between;align-items:center;">
            <div>
                <div style="font-weight:700;color:#0f172a;font-size:14px;">📅 {e['title']}</div>
                <div style="font-size:12px;color:#64748b;margin-top:4px;">
                    {e['date']} {"at " + e['time'] if e.get('time') else ""} &nbsp;·&nbsp; {timing}
                </div>
                {"<div style='font-size:12px;color:#94a3b8;'>" + e.get('notes','') + "</div>" if e.get('notes') else ""}
            </div>
            <span class="badge badge-info">{timing}</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🗑️", key=f"delev_{e['id']}"):
            delete_calendar_event(e["id"])
            st.rerun()

    if past:
        st.markdown(f'<div class="section-hdr">🕐 Past Events ({len(past)})</div>', unsafe_allow_html=True)
        for e in reversed(past[-5:]):
            st.markdown(f'<div style="opacity:0.5;font-size:13px;padding:5px 0;">✓ {e["title"]} — {e["date"]}</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📊 Dashboard":
    import plotly.graph_objects as go

    st.markdown('<h1 style="color:#0f172a;">📊 Dashboard</h1>', unsafe_allow_html=True)

    stats = get_analytics()
    conv = st.session_state.conversation

    # KPIs
    k1, k2, k3, k4, k5 = st.columns(5)
    for col, val, lbl, color in [
        (k1, len(conv), "Messages", "#6366f1"),
        (k2, stats["total_tasks"], "Tasks", "#8b5cf6"),
        (k3, stats["pending_tasks"], "Pending", "#f59e0b"),
        (k4, f"{stats['completion_rate']}%", "Done Rate", "#10b981"),
        (k5, stats["total_notes"], "Notes", "#06b6d4"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card" style="border-color:{color};"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    d1, d2 = st.columns(2)

    with d1:
        st.markdown('<div class="section-hdr">🎯 Task Priority Split</div>', unsafe_allow_html=True)
        pc = stats["priority_counts"]
        if any(pc.values()):
            fig = go.Figure(go.Pie(
                labels=list(pc.keys()),
                values=list(pc.values()),
                marker_colors=["#dc2626", "#d97706", "#16a34a"],
                hole=0.45,
            ))
            fig.update_layout(margin=dict(l=0,r=0,t=10,b=10), height=260, paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tasks yet.")

    with d2:
        st.markdown('<div class="section-hdr">💬 Conversation Intent Types</div>', unsafe_allow_html=True)
        if conv:
            intent_counts = {}
            for msg in conv:
                if msg["role"] == "assistant":
                    it = msg.get("intent", "CHAT")
                    intent_counts[it] = intent_counts.get(it, 0) + 1
            if intent_counts:
                colors_map = {
                    "CHAT": "#6366f1", "CREATE_TASK": "#f59e0b",
                    "CREATE_NOTE": "#0ea5e9", "CREATE_REMINDER": "#10b981",
                    "CALENDAR_EVENT": "#8b5cf6", "SEARCH_WEB": "#06b6d4",
                }
                fig2 = go.Figure(go.Bar(
                    x=list(intent_counts.values()),
                    y=list(intent_counts.keys()),
                    orientation="h",
                    marker_color=[colors_map.get(k, "#6366f1") for k in intent_counts],
                ))
                fig2.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=10,r=20,t=10,b=20), height=260,
                    xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                )
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Start chatting to see intent analytics.")

    # Summary cards
    st.markdown('<div class="section-hdr">📋 Session Summary</div>', unsafe_allow_html=True)
    sm1, sm2, sm3 = st.columns(3)
    with sm1:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-weight:700;color:#0f172a;margin-bottom:10px;">🗓️ Calendar</div>
            <div style="font-size:24px;font-weight:800;color:#6366f1;">{stats['total_events']}</div>
            <div style="font-size:12px;color:#64748b;">Events scheduled</div>
        </div>
        """, unsafe_allow_html=True)
    with sm2:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-weight:700;color:#0f172a;margin-bottom:10px;">🔔 Reminders</div>
            <div style="font-size:24px;font-weight:800;color:#f59e0b;">{stats['active_reminders']}</div>
            <div style="font-size:12px;color:#64748b;">Active reminders</div>
        </div>
        """, unsafe_allow_html=True)
    with sm3:
        user_msgs = sum(1 for m in conv if m["role"] == "user")
        audio_msgs = sum(1 for m in conv if m.get("audio"))
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-weight:700;color:#0f172a;margin-bottom:10px;">🎙️ Voice Usage</div>
            <div style="font-size:24px;font-weight:800;color:#10b981;">{audio_msgs}</div>
            <div style="font-size:12px;color:#64748b;">Voice messages of {user_msgs} total</div>
        </div>
        """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.markdown('<h1 style="color:#0f172a;">⚙️ Settings</h1>', unsafe_allow_html=True)

    current_key = _active_key()
    if current_key:
        src = "Your key (entered below)" if st.session_state.get("user_api_key","").strip() else "Server-configured"
        st.markdown(f"""
        <div style="background:#f0fdf4;border:2px solid #86efac;border-radius:14px;
                    padding:14px 20px;margin-bottom:20px;">
            <strong style="color:#15803d;">🟢 API Key Active</strong>
            <span style="font-size:12px;color:#166534;margin-left:8px;">Source: {src}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#fef2f2;border:2px solid #fca5a5;border-radius:14px;
                    padding:14px 20px;margin-bottom:20px;">
            <strong style="color:#dc2626;">🔴 No API Key — Enter below to get started</strong>
        </div>
        """, unsafe_allow_html=True)

    col_key, col_info = st.columns([3, 2])

    with col_key:
        st.markdown('<div class="section-hdr">🔑 OpenAI API Key</div>', unsafe_allow_html=True)
        entered = st.text_input("API Key", value=st.session_state.get("user_api_key",""),
                                type="password", placeholder="sk-proj-...",
                                label_visibility="collapsed")
        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button("💾 Save Key", type="primary", use_container_width=True):
                if entered.strip().startswith("sk-"):
                    st.session_state.user_api_key = entered.strip()
                    os.environ["OPENAI_API_KEY"] = entered.strip()
                    st.success("✅ Saved! Ready to use.")
                    st.rerun()
                elif entered.strip():
                    st.error("Keys must start with 'sk-'")
                else:
                    st.error("Please enter a key.")
        with sc2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.user_api_key = ""
                if "OPENAI_API_KEY" in os.environ:
                    del os.environ["OPENAI_API_KEY"]
                st.rerun()

        st.markdown("""
        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;
                    padding:12px 16px;margin-top:12px;">
            <strong style="color:#92400e;font-size:13px;">🔒 Privacy</strong><br>
            <span style="font-size:12px;color:#78350f;">
                Your key is stored in browser session memory only.<br>
                Never saved to any database. Cleared on tab close.
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-hdr">🎙️ Assistant Settings</div>', unsafe_allow_html=True)
        st.markdown("**Default Voice:**")
        voice_names = list(VOICES.keys())
        voice_keys = list(VOICES.values())
        cur_idx = voice_keys.index(st.session_state.tts_voice) if st.session_state.tts_voice in voice_keys else 4
        sel = st.selectbox("Voice", voice_names, index=cur_idx,
                           format_func=lambda v: f"{v} — {VOICE_DESCRIPTIONS[VOICES[v]]}",
                           key="settings_voice")
        st.session_state.tts_voice = VOICES[sel]
        spd = st.slider("Speech Speed", 0.5, 2.0, st.session_state.tts_speed, 0.1, key="settings_speed")
        st.session_state.tts_speed = spd
        tts = st.toggle("Auto-speak responses", st.session_state.tts_enabled, key="settings_tts")
        st.session_state.tts_enabled = tts

        st.markdown('<div class="section-hdr">🗑️ Data Management</div>', unsafe_allow_html=True)
        if st.button("🗑️ Clear All Session Data", type="secondary", use_container_width=True):
            for key in ["conversation", "tasks", "notes", "reminders", "calendar_events", "last_audio"]:
                if key in st.session_state:
                    del st.session_state[key]
            init_stores()
            st.session_state.conversation = []
            st.success("All session data cleared.")
            st.rerun()

    with col_info:
        st.markdown('<div class="section-hdr">📋 Get Your API Key</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-card">
            <div style="font-size:13px;color:#374151;line-height:2;">
                1. Go to <a href="https://platform.openai.com/api-keys"
                   target="_blank" style="color:#6366f1;font-weight:600;">
                   platform.openai.com/api-keys</a><br>
                2. Sign in or create an account<br>
                3. Click <strong>+ Create new secret key</strong><br>
                4. Copy the key (starts with <code>sk-</code>)<br>
                5. Paste it on the left and save
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-hdr">💰 Cost Estimate</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-card">
            <div style="font-size:13px;color:#374151;line-height:1.9;">
                🎙️ Whisper: ~$0.006/min audio<br>
                🧠 GPT-4o chat: ~$0.005/message<br>
                🔊 TTS: ~$0.015/1K characters<br><br>
                <strong>Typical session (~20 messages): ~$0.15</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        db_status = "🟢 Connected" if db_ok() else "🔴 Not configured"
        st.markdown(f'<div class="section-hdr">🗄️ Database</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size:13px;color:#374151;">
                Status: <strong>{db_status}</strong><br><br>
                Supabase enables persistent conversation history across sessions.
                Without it, data is session-only.
            </div>
        </div>
        """, unsafe_allow_html=True)

    if current_key:
        st.markdown('<div class="section-hdr">🚀 Ready!</div>', unsafe_allow_html=True)
        if st.button("→ Start Chatting with ARIA", type="primary"):
            st.session_state.page = "🎙️ Voice Chat"
            st.rerun()
