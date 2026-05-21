"""
app.py — ARIA: AI Voice Assistant Agent
Improved UX — clean full-width chat, clear voice panel, polished UI.
"""

import os
import sys
import uuid
import base64
from datetime import datetime

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="ARIA — AI Voice Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07090f 0%, #0d1117 55%, #0a0e1a 100%) !important;
}
[data-testid="stSidebar"] > div:first-child { background: transparent !important; }
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,[data-testid="stSidebar"] label { color: #e2e8f0 !important; }
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
    background: rgba(99,102,241,0.22) !important;
    border-color: rgba(99,102,241,0.45) !important; color: #fff !important;
}
[data-testid="stSidebar"] .stButton > button:hover p { color: #fff !important; }
[data-testid="stSidebar"] .nav-active > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border-left: 4px solid #a78bfa !important;
    border-top: 1px solid rgba(167,139,250,0.3) !important;
    border-right: 1px solid rgba(167,139,250,0.15) !important;
    border-bottom: 1px solid rgba(167,139,250,0.15) !important;
    color: #fff !important; font-weight: 700 !important;
    box-shadow: 0 4px 18px rgba(99,102,241,0.4) !important;
    transform: translateX(3px) !important;
}
[data-testid="stSidebar"] .nav-active > button p { color: #fff !important; }
.nav-div { height:1px; background:rgba(255,255,255,0.07); margin:10px 0; }

/* ── Chat bubbles ── */
.bubble-wrap-user { display:flex; justify-content:flex-end; margin:4px 0; }
.bubble-wrap-ai   { display:flex; justify-content:flex-start; margin:4px 0; }
.bubble-user {
    background: linear-gradient(135deg,#6366f1,#8b5cf6);
    color:white; border-radius:20px 20px 6px 20px;
    padding:12px 18px; max-width:72%; font-size:14px; line-height:1.65;
    box-shadow:0 3px 10px rgba(99,102,241,0.3);
    word-wrap:break-word;
}
.bubble-ai {
    background:white; color:#0f172a;
    border:1px solid #e8edf5; border-radius:20px 20px 20px 6px;
    padding:12px 18px; max-width:78%; font-size:14px; line-height:1.65;
    box-shadow:0 2px 8px rgba(0,0,0,0.07);
    word-wrap:break-word;
}
.bubble-ai-row { display:flex; align-items:flex-start; gap:10px; margin:8px 0 4px; }
.ai-avatar {
    width:34px; height:34px; border-radius:50%; flex-shrink:0;
    background:linear-gradient(135deg,#6366f1,#8b5cf6);
    display:flex; align-items:center; justify-content:center;
    font-size:16px; box-shadow:0 2px 6px rgba(99,102,241,0.35);
}
.user-avatar {
    width:30px; height:30px; border-radius:50%; flex-shrink:0;
    background:#e2e8f0; display:flex; align-items:center;
    justify-content:center; font-size:14px;
}
.msg-time { font-size:11px; color:#94a3b8; margin:2px 6px; }
.intent-tag {
    display:inline-block; padding:2px 9px; border-radius:10px;
    font-size:10px; font-weight:700; background:#ede9fe;
    color:#6d28d9; margin-left:6px; vertical-align:middle;
}
.audio-tag {
    display:inline-block; padding:2px 8px; border-radius:10px;
    font-size:10px; font-weight:600; background:#dcfce7;
    color:#16a34a; margin-left:6px;
}

/* ── Action card — shown when ARIA executes a task ── */
.action-card {
    background:linear-gradient(135deg,#f0fdf4,#dcfce7);
    border:1px solid #86efac; border-radius:10px;
    padding:9px 14px; margin:6px 0 2px 44px;
    font-size:12px; font-weight:600; color:#166534;
}

/* ── Quick action pills ── */
.qa-pill {
    display:inline-block; padding:7px 16px; border-radius:20px;
    background:white; border:1px solid #e2e8f0;
    font-size:13px; font-weight:500; color:#374151;
    cursor:pointer; margin:4px; transition:all 0.15s;
    box-shadow:0 1px 3px rgba(0,0,0,0.06);
}
.qa-pill:hover { border-color:#6366f1; color:#6366f1; background:#eff6ff; }

/* ── Voice upload area ── */
.upload-zone {
    background:linear-gradient(135deg,#1e1b4b,#1e3a5f);
    border:2px dashed rgba(99,102,241,0.5);
    border-radius:16px; padding:28px 20px; text-align:center;
    margin-bottom:16px; cursor:pointer; transition:all 0.2s;
}
.upload-zone:hover { border-color:#6366f1; background:linear-gradient(135deg,#2d2b77,#1e4a6f); }

/* ── Cards ── */
.card {
    background:white; border:1px solid #e8edf5;
    border-radius:14px; padding:18px 20px;
    box-shadow:0 2px 6px rgba(0,0,0,0.05); margin-bottom:12px;
}
.metric-card {
    background:white; border-radius:12px; padding:16px;
    box-shadow:0 1px 4px rgba(0,0,0,0.07); text-align:center;
    border-top:3px solid #6366f1;
}
.metric-card .v { font-size:26px; font-weight:800; color:#0f172a; }
.metric-card .l { font-size:11px; color:#64748b; font-weight:500;
    text-transform:uppercase; letter-spacing:0.05em; margin-top:3px; }

/* ── Section header ── */
.sec-hdr {
    background:linear-gradient(90deg,#6366f1,#8b5cf6);
    color:white; border-radius:10px; padding:10px 16px;
    margin:16px 0 12px; font-size:14px; font-weight:600;
}

/* ── Badges ── */
.badge { display:inline-block; padding:2px 9px; border-radius:20px;
    font-size:11px; font-weight:600; margin:2px; }
.b-high   { background:#fef2f2; color:#dc2626; border:1px solid #fecaca; }
.b-med    { background:#fffbeb; color:#d97706; border:1px solid #fde68a; }
.b-low    { background:#f0fdf4; color:#16a34a; border:1px solid #bbf7d0; }
.b-info   { background:#eff6ff; color:#2563eb; border:1px solid #bfdbfe; }
.b-done   { background:#f0fdf4; color:#16a34a; border:1px solid #bbf7d0; }

/* ── Chat container scroll ── */
.chat-scroll {
    max-height:500px; overflow-y:auto;
    padding:12px 4px; scroll-behavior:smooth;
}

/* ── Task item ── */
.task-item {
    background:white; border:1px solid #e2e8f0;
    border-left:4px solid #6366f1; border-radius:10px;
    padding:12px 16px; margin:6px 0;
}
.task-done-item {
    background:#f8fafc; border:1px solid #e2e8f0;
    border-left:4px solid #d1d5db; border-radius:10px;
    padding:12px 16px; margin:6px 0; opacity:0.65;
}

/* ── Status dot ── */
.dot-g { width:8px;height:8px;border-radius:50%;background:#22c55e;display:inline-block;margin-right:5px; }
.dot-r { width:8px;height:8px;border-radius:50%;background:#ef4444;display:inline-block;margin-right:5px; }

/* ── TTS audio player ── */
audio { border-radius:10px !important; }

/* ── Text area ── */
[data-testid="stTextArea"] textarea {
    background:#0f172a !important; color:#e2e8f0 !important;
    font-size:13px !important; border-radius:10px !important;
    border:1px solid #1e293b !important; font-family:'Inter',sans-serif !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background:#f1f5f9; border-radius:10px; padding:3px; gap:2px;
}
.stTabs [data-baseweb="tab"] { border-radius:8px; font-weight:500; font-size:13px; }
.stTabs [aria-selected="true"] {
    background:white !important; box-shadow:0 1px 4px rgba(0,0,0,0.1);
}

/* ── Upload widget ── */
[data-testid="stFileUploader"] {
    border:2px dashed #818cf8; border-radius:12px; background:#eef2ff; padding:4px;
}

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    background:linear-gradient(135deg,#6366f1,#8b5cf6) !important;
    border:none !important; color:white !important;
    border-radius:10px !important; font-weight:600 !important;
}

#MainMenu, footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Imports
# ─────────────────────────────────────────────────────────────────────────────
from modules.agent import is_configured, chat as ai_chat, generate_note_from_text, web_search_answer
from modules.stt import transcribe_bytes, transcribe_uploaded
from modules.tts import synthesize, audio_to_html, VOICES, VOICE_DESCRIPTIONS
from modules.tasks import (
    init_stores, add_task, complete_task, delete_task, get_tasks,
    add_note, delete_note, get_notes,
    add_reminder, dismiss_reminder, dismiss_alert, get_reminders,
    check_due_reminders, get_reminder_status,
    add_calendar_event, get_calendar_events, delete_calendar_event,
    dismiss_event_alert, check_due_events, get_event_status,
    get_analytics, local_now,
)
from modules.recorder import mic_recorder, decode_recording
from modules.database import is_configured as db_ok, save_message

init_stores()

# ─────────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────────
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
_ss("show_voice_panel", False)

# ─────────────────────────────────────────────────────────────────────────────
# API key
# ─────────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────────
# Capture browser timezone offset on every load (stores in session_state)
# ─────────────────────────────────────────────────────────────────────────────
import streamlit.components.v1 as _tz_comp

def _capture_timezone():
    """
    Inject a tiny JS snippet that reads the browser's UTC offset in minutes
    and sends it back to Python via a hidden Streamlit component.
    The offset is stored in st.session_state.user_tz_offset.
    Example: IST = UTC+5:30 → offset = +330 minutes.
    """
    tz_result = _tz_comp.html("""
    <script>
    // Get browser UTC offset in minutes (negative = east of UTC for getTimezoneOffset)
    // We negate it so IST (+5:30) = +330, not -330
    const offset = -(new Date().getTimezoneOffset());
    window.parent.postMessage({
        type: 'streamlit:setComponentValue',
        value: offset
    }, '*');
    </script>
    """, height=0)
    if tz_result is not None and isinstance(tz_result, (int, float)):
        st.session_state.user_tz_offset = int(tz_result)

_capture_timezone()

# ─────────────────────────────────────────────────────────────────────────────
# Navigation
# ─────────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    has_key = bool(_active_key())
    dot = '<span class="dot-g"></span>' if has_key else '<span class="dot-r"></span>'
    pending_tasks = len(get_tasks("pending"))
    active_reminders = len(get_reminders(active_only=True))

    st.markdown(f"""
    <div style="padding:20px 4px 16px;text-align:center;">
        <div style="width:60px;height:60px;background:linear-gradient(135deg,#6366f1,#8b5cf6);
                    border-radius:50%;margin:0 auto;display:flex;align-items:center;
                    justify-content:center;font-size:26px;
                    box-shadow:0 4px 16px rgba(99,102,241,0.45);">🤖</div>
        <div style="font-size:20px;font-weight:800;color:white;margin-top:10px;letter-spacing:-0.3px;">ARIA</div>
        <div style="font-size:11px;color:#475569;margin-top:3px;font-weight:500;">AI Voice Assistant</div>
        <div style="font-size:11px;margin-top:8px;">{dot}{"Ready" if has_key else '<span style="color:#f87171;">No API key</span>'}</div>
    </div>
    <div class="nav-div"></div>
    <div style="font-size:10px;color:#475569;text-transform:uppercase;
                letter-spacing:0.1em;font-weight:600;padding:0 4px;margin-bottom:6px;">Menu</div>
    """, unsafe_allow_html=True)

    current = st.session_state.get("page", "🎙️ Voice Chat")
    for icon, label in NAV:
        full = f"{icon} {label}"
        is_active = (current == full)

        # Badge counts
        badge = ""
        if label == "Tasks" and pending_tasks:
            badge = f" · {pending_tasks}"
        elif label == "Reminders" and active_reminders:
            badge = f" · {active_reminders}"

        if is_active:
            st.markdown('<div class="nav-active">', unsafe_allow_html=True)
        btn_label = f"✦  {icon}  {label}{badge}" if is_active else f"{icon}  {label}{badge}"
        if st.button(btn_label, key=f"nav_{label}", use_container_width=True):
            st.session_state.page = full
            st.rerun()
        if is_active:
            st.markdown('</div>', unsafe_allow_html=True)

    page = st.session_state.get("page", "🎙️ Voice Chat")

    # Mini stats
    conv_len = len(st.session_state.conversation)
    notes_count = len(get_notes())
    st.markdown(f"""
    <div class="nav-div"></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;padding:0 2px;">
        <div style="background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.25);
                    border-radius:8px;padding:8px;text-align:center;">
            <div style="font-size:18px;font-weight:700;color:white;">{conv_len}</div>
            <div style="font-size:10px;color:#64748b;">Msgs</div>
        </div>
        <div style="background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.25);
                    border-radius:8px;padding:8px;text-align:center;">
            <div style="font-size:18px;font-weight:700;color:white;">{pending_tasks}</div>
            <div style="font-size:10px;color:#64748b;">Tasks</div>
        </div>
        <div style="background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.25);
                    border-radius:8px;padding:8px;text-align:center;">
            <div style="font-size:18px;font-weight:700;color:white;">{notes_count}</div>
            <div style="font-size:10px;color:#64748b;">Notes</div>
        </div>
        <div style="background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.25);
                    border-radius:8px;padding:8px;text-align:center;">
            <div style="font-size:18px;font-weight:700;color:white;">{active_reminders}</div>
            <div style="font-size:10px;color:#64748b;">Alerts</div>
        </div>
    </div>
    <div class="nav-div"></div>
    <div style="font-size:11px;color:#334155;text-align:center;padding:2px 0 8px;">
        Built with ❤️ by
        <a href="https://www.adityasharma.ai" target="_blank"
           style="color:#818cf8;text-decoration:none;">adityasharma.ai</a>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Key guard
# ─────────────────────────────────────────────────────────────────────────────
if page != "⚙️ Settings" and not _active_key():
    st.markdown("""
    <div style="max-width:500px;margin:80px auto;text-align:center;">
        <div style="width:80px;height:80px;background:linear-gradient(135deg,#6366f1,#8b5cf6);
                    border-radius:50%;margin:0 auto;display:flex;align-items:center;
                    justify-content:center;font-size:36px;
                    box-shadow:0 8px 24px rgba(99,102,241,0.4);">🤖</div>
        <h2 style="color:#0f172a;margin:20px 0 8px;font-size:26px;">Welcome to ARIA</h2>
        <p style="color:#64748b;font-size:15px;line-height:1.7;margin-bottom:24px;">
            Your AI Voice Assistant needs an OpenAI API key to power<br>
            Whisper transcription, GPT-4o intelligence, and TTS voice.
        </p>
        <div style="background:#eff6ff;border:2px solid #bfdbfe;border-radius:14px;
                    padding:16px 20px;text-align:left;margin-bottom:20px;">
            <div style="font-weight:700;color:#1d4ed8;margin-bottom:6px;">🔑 To get started:</div>
            <div style="font-size:13px;color:#374151;line-height:2;">
                1. Get your key at <strong>platform.openai.com/api-keys</strong><br>
                2. Click <strong>⚙️ Settings</strong> in the sidebar<br>
                3. Paste your key and click Save<br>
                4. Come back here and start chatting!
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("⚙️ Go to Settings →", type="primary"):
        st.session_state.page = "⚙️ Settings"
        st.rerun()
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# ALERT SYSTEM — Reminders + Calendar Events — runs on every page load
# ─────────────────────────────────────────────────────────────────────────────
import streamlit.components.v1 as _comp

def _browser_notify(title: str, body: str, icon_url: str = ""):
    """Fire a browser push notification (requires Notification permission)."""
    t = title.replace("'", "\'").replace('"', '\"')
    b = body.replace("'", "\'").replace('"', '\"')
    _comp.html(f"""
    <script>
    (function() {{
        if (!('Notification' in window)) return;
        function send() {{
            new Notification('{t}', {{body: '{b}', icon: '{icon_url}'}});
        }}
        if (Notification.permission === 'granted') {{ send(); }}
        else if (Notification.permission !== 'denied') {{
            Notification.requestPermission().then(p => {{ if (p === 'granted') send(); }});
        }}
    }})();
    </script>
    """, height=0)


def _show_reminder_alerts():
    """Show alert banners for due reminders."""
    due_reminders = check_due_reminders()
    if not due_reminders:
        return
    for r in due_reminders:
        rid = r["id"]
        _browser_notify(
            f"⏰ ARIA Reminder",
            r["reminder"],
            "https://em-content.zobj.net/source/twitter/376/bell_1f514.png"
        )
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#fef3c7,#fde68a);
                    border:2px solid #f59e0b;border-radius:14px;
                    padding:16px 20px;margin:0 0 12px 0;
                    box-shadow:0 4px 16px rgba(245,158,11,0.25);">
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="font-size:36px;animation:ring 1s infinite;">⏰</div>
                <div>
                    <div style="font-weight:800;color:#92400e;font-size:16px;">Reminder Due!</div>
                    <div style="font-weight:600;color:#78350f;font-size:14px;margin-top:2px;">
                        {r['reminder']}
                    </div>
                    <div style="font-size:12px;color:#b45309;margin-top:3px;">
                        Set for: {r.get('due_dt', r.get('time',''))}
                    </div>
                </div>
            </div>
        </div>
        <style>
        @keyframes ring {{
            0%,100% {{ transform: rotate(0deg); }}
            25%      {{ transform: rotate(-15deg); }}
            75%      {{ transform: rotate(15deg); }}
        }}
        </style>
        """, unsafe_allow_html=True)
        ac1, ac2 = st.columns([3, 1])
        with ac2:
            if st.button("✓ Dismiss", key=f"ralert_dis_{rid}", type="primary", use_container_width=True):
                dismiss_reminder(rid)
                st.rerun()
        with ac1:
            if st.button("⏰ Snooze 10 min", key=f"ralert_snz_{rid}", use_container_width=True):
                from datetime import datetime as _dt2, timedelta as _td2
                for rem in st.session_state.reminders:
                    if rem["id"] == rid:
                        new_due = _dt2.now() + _td2(minutes=10)
                        rem["due_dt"] = new_due.strftime("%Y-%m-%d %H:%M")
                        rem["time"] = f"Snoozed until {new_due.strftime('%I:%M %p')}"
                        break
                dismiss_alert(rid)
                st.rerun()


def _show_event_alerts():
    """Show alert banners for calendar events starting soon."""
    due_events = check_due_events()
    if not due_events:
        return
    for e in due_events:
        eid = e["id"]
        evt_time = e.get("time", "")
        evt_date = e.get("date", "")
        due_str  = e.get("due_dt", "")
        diff_info = ""
        if due_str:
            try:
                from datetime import datetime as _dt3
                due_dt = _dt3.strptime(due_str, "%Y-%m-%d %H:%M")
                diff_mins = (due_dt - _dt3.now()).total_seconds() / 60
                if diff_mins < 0:
                    diff_info = f"Started {abs(int(diff_mins))} min ago"
                elif diff_mins < 1:
                    diff_info = "Starting NOW!"
                else:
                    diff_info = f"Starting in {int(diff_mins)} min"
            except Exception:
                pass

        _browser_notify(
            f"📅 {e['title']}",
            diff_info or f"{evt_date} {evt_time}",
            "https://em-content.zobj.net/source/twitter/376/calendar_1f4c5.png"
        )
        notes_html = f"<div style='font-size:12px;color:#4338ca;margin-top:2px;'>📝 {e.get('notes','')}</div>" if e.get('notes') else ""
        at_time = f"at {evt_time}" if evt_time else ""
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#eff6ff,#dbeafe);
                    border:2px solid #6366f1;border-radius:14px;
                    padding:16px 20px;margin:0 0 12px 0;
                    box-shadow:0 4px 16px rgba(99,102,241,0.2);">
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="font-size:34px;">📅</div>
                <div style="flex:1;">
                    <div style="font-weight:800;color:#1e3a8a;font-size:16px;">
                        Calendar Event Starting!
                    </div>
                    <div style="font-weight:600;color:#1d4ed8;font-size:14px;margin-top:2px;">
                        {e['title']}
                    </div>
                    <div style="font-size:12px;color:#3730a3;margin-top:3px;">
                        📅 {evt_date} {at_time} &nbsp;·&nbsp; <strong>{diff_info}</strong>
                    </div>
                    {notes_html}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        ec1, ec2 = st.columns([3, 1])
        with ec2:
            if st.button("✓ Got it", key=f"ealert_dis_{eid}", type="primary", use_container_width=True):
                dismiss_event_alert(eid)
                st.rerun()
        with ec1:
            if st.button("🗑️ Remove Event", key=f"ealert_del_{eid}", use_container_width=True):
                delete_calendar_event(eid)
                dismiss_event_alert(eid)
                st.rerun()


_show_reminder_alerts()
_show_event_alerts()

# ─────────────────────────────────────────────────────────────────────────────
# Message processor
# ─────────────────────────────────────────────────────────────────────────────
def _process_message(user_text: str, is_audio: bool = False):
    if not user_text.strip():
        return

    st.session_state.conversation.append({
        "role": "user", "content": user_text,
        "time": datetime.now().strftime("%H:%M"), "audio": is_audio,
    })

    if db_ok():
        save_message(st.session_state.session_id, "user", user_text, audio_used=is_audio)

    # Context
    tasks = get_tasks("pending")
    ctx = []
    if tasks:
        ctx.append("TASKS: " + "; ".join(t["task"] for t in tasks[:5]))
    notes = get_notes()
    if notes:
        ctx.append("NOTES: " + "; ".join(n["title"] for n in notes[:3]))
    context = "\n".join(ctx)

    result = ai_chat(user_text, st.session_state.conversation[:-1], context=context)
    response_text = result["response"]
    intent = result.get("intent", {"type": "CHAT"})
    intent_type = intent.get("type", "CHAT")
    intent_data = intent.get("data", {})
    action_msg = ""

    if intent_type == "CREATE_TASK" and intent_data.get("task"):
        t = add_task(intent_data["task"], intent_data.get("deadline",""), intent_data.get("priority","Medium"))
        action_msg = f"✅ Task added: {t['task']}"
    elif intent_type == "CREATE_NOTE" and intent_data.get("content"):
        n = add_note(intent_data.get("title","Note"), intent_data["content"])
        action_msg = f"📝 Note saved: {n['title']}"
    elif intent_type == "CREATE_REMINDER" and intent_data.get("reminder"):
        r = add_reminder(intent_data["reminder"], intent_data.get("time",""))
        action_msg = f"🔔 Reminder: {r['reminder']} — {r['time']}"
    elif intent_type == "CALENDAR_EVENT" and intent_data.get("title"):
        e = add_calendar_event(intent_data["title"], intent_data.get("date",""), intent_data.get("time",""))
        action_msg = f"📅 Event: {e['title']} on {e['date']}"
    elif intent_type == "SEARCH_WEB" and intent_data.get("query"):
        response_text += "\n\n" + web_search_answer(intent_data["query"])

    # Strip any accidental HTML from action message before storing
    safe_action_msg = action_msg.replace("<","").replace(">","") if action_msg else ""
    st.session_state.conversation.append({
        "role": "assistant", "content": response_text,
        "intent": intent_type, "action": safe_action_msg,
        "time": datetime.now().strftime("%H:%M"), "audio": False,
    })

    if db_ok():
        save_message(st.session_state.session_id, "assistant", response_text, intent_type)

    if st.session_state.tts_enabled:
        clean = response_text.replace("**","").replace("✅","").replace("📝","").replace("🔔","").replace("📅","")
        st.session_state.last_audio = synthesize(clean, st.session_state.tts_voice, st.session_state.tts_speed)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: VOICE CHAT
# ═════════════════════════════════════════════════════════════════════════════
if page == "🎙️ Voice Chat":

    # Header
    st.markdown("""
    <div style="padding:6px 0 20px;border-bottom:1px solid #e2e8f0;margin-bottom:20px;">
        <div style="display:flex;align-items:center;gap:14px;">
            <div style="width:44px;height:44px;background:linear-gradient(135deg,#6366f1,#8b5cf6);
                        border-radius:14px;display:flex;align-items:center;justify-content:center;
                        font-size:22px;box-shadow:0 4px 12px rgba(99,102,241,0.35);">🤖</div>
            <div>
                <div style="font-size:22px;font-weight:800;color:#0f172a;line-height:1;">ARIA</div>
                <div style="font-size:13px;color:#22c55e;font-weight:500;margin-top:2px;">
                    ● Online · Ready to help
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Main layout: chat left, voice right ──────────────────────────────────
    chat_col, voice_col = st.columns([3, 2], gap="large")

    # ── CHAT COLUMN ──────────────────────────────────────────────────────────
    with chat_col:

        # Empty state
        if not st.session_state.conversation:
            st.markdown("""
            <div style="background:linear-gradient(135deg,#f8faff,#f0f4ff);
                        border:1px solid #e0e7ff;border-radius:16px;
                        padding:36px 28px;text-align:center;margin-bottom:20px;">
                <div style="font-size:52px;margin-bottom:14px;">🤖</div>
                <div style="font-size:19px;font-weight:700;color:#1e1b4b;margin-bottom:8px;">
                    Hi, I'm ARIA!
                </div>
                <div style="font-size:14px;color:#4c1d95;line-height:1.8;">
                    I'm your AI voice assistant. I can help you:<br>
                    <strong>📋 Manage tasks</strong> · <strong>📝 Take notes</strong> ·
                    <strong>🔔 Set reminders</strong> · <strong>📅 Schedule events</strong>
                </div>
                <div style="margin-top:20px;padding:12px 16px;background:white;
                            border-radius:10px;border:1px solid #c7d2fe;text-align:left;">
                    <div style="font-size:12px;font-weight:700;color:#4f46e5;margin-bottom:8px;">
                        💡 Try saying:
                    </div>
                    <div style="font-size:13px;color:#374151;line-height:2.0;">
                        "Add a task to review the proposal by Friday"<br>
                        "Remind me to call Alice tomorrow at 9 AM"<br>
                        "Schedule a team meeting Thursday 2 PM"<br>
                        "Take a note about today's ideas"
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Conversation
        else:
            for msg in st.session_state.conversation:
                role = msg["role"]
                content = msg["content"]
                time_s = msg.get("time", "")
                intent = msg.get("intent", "")
                action = msg.get("action", "")
                is_aud = msg.get("audio", False)

                if role == "user":
                    safe_user = content.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
                    aud_html = '<span class="audio-tag">🎙️ voice</span>' if is_aud else ""
                    st.markdown(f"""
                    <div style="text-align:right;margin-bottom:2px;">
                        <span class="msg-time">{time_s}</span>{aud_html}
                    </div>
                    <div class="bubble-wrap-user">
                        <div class="bubble-user">{safe_user}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    intent_html = f'<span class="intent-tag">{intent}</span>' if intent and intent != "CHAT" else ""
                    safe_content = content.replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
                    st.markdown(f"""
                    <div class="bubble-ai-row">
                        <div class="ai-avatar">🤖</div>
                        <div>
                            <div style="margin-bottom:4px;">
                                <span class="msg-time">{time_s}</span>{intent_html}
                            </div>
                            <div class="bubble-ai">{safe_content}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if action:
                        safe_action = action.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                        st.markdown(f'<div class="action-card">🎯 {safe_action}</div>', unsafe_allow_html=True)

        # TTS playback
        if st.session_state.last_audio:
            st.markdown(audio_to_html(st.session_state.last_audio, autoplay=True), unsafe_allow_html=True)
            st.session_state.last_audio = None

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Chat input
        user_input = st.chat_input("Message ARIA...", key="main_chat_input")
        if user_input:
            with st.spinner("🤖 ARIA is thinking..."):
                _process_message(user_input)
            st.rerun()

        # Quick action pills
        st.markdown("""
        <div style="margin-top:10px;margin-bottom:4px;">
            <span style="font-size:12px;font-weight:600;color:#64748b;
                         text-transform:uppercase;letter-spacing:0.05em;">Quick actions</span>
        </div>
        """, unsafe_allow_html=True)

        qa_cols = st.columns(4)
        quick_actions = [
            ("📋", "My Tasks", "What are my current pending tasks?"),
            ("📝", "New Note", "I want to take a quick note"),
            ("🔔", "Reminder", "Set a reminder for me"),
            ("📅", "Schedule", "Add a calendar event"),
        ]
        for col, (icon, label, prompt) in zip(qa_cols, quick_actions):
            with col:
                if st.button(f"{icon} {label}", use_container_width=True, key=f"qa_{label}"):
                    with st.spinner("🤖 Thinking..."):
                        _process_message(prompt)
                    st.rerun()

        if st.session_state.conversation:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            if st.button("🗑️ Clear conversation", use_container_width=False):
                st.session_state.conversation = []
                st.session_state.last_audio = None
                st.rerun()

    # ── VOICE COLUMN ─────────────────────────────────────────────────────────
    with voice_col:

        st.markdown('<div class="sec-hdr">🎙️ Voice Input</div>', unsafe_allow_html=True)

        mic_tab, upload_tab = st.tabs(["🔴 Record", "📁 Upload"])

        # ── TAB 1: LIVE MIC ───────────────────────────────────────────────────
        with mic_tab:
            st.markdown("""
            <div style="background:linear-gradient(135deg,#1e1b4b,#0f2744);
                        border-radius:12px;padding:14px 16px 10px;margin-bottom:10px;">
                <div style="color:#94a3b8;font-size:12px;font-weight:500;text-align:center;
                            margin-bottom:8px;">
                    Click the mic · speak · click again to stop · Send to ARIA
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Render the JS microphone recorder
            rec_result = mic_recorder(key="live_mic", height=320)

            # Handle result from JS component
            if rec_result and isinstance(rec_result, dict) and rec_result.get("audio_b64"):
                audio_bytes, ext = decode_recording(rec_result)
                # Only process if we haven't already processed this exact recording
                rec_hash = rec_result.get("duration", 0)
                last_hash = st.session_state.get("_last_rec_hash", -1)

                if audio_bytes and rec_hash != last_hash:
                    st.session_state["_last_rec_hash"] = rec_hash
                    with st.spinner("🎙️ Transcribing with Whisper..."):
                        from modules.stt import transcribe_bytes
                        result = transcribe_bytes(audio_bytes, ext)

                    if "error" in result:
                        st.error(f"❌ {result['error']}")
                    elif result.get("text"):
                        text = result["text"]
                        st.markdown(f"""
                        <div style="background:#0f172a;border-radius:10px;padding:12px;
                                    font-family:monospace;font-size:13px;
                                    color:#a5f3fc;line-height:1.7;margin:8px 0;">
                            "{text}"
                        </div>
                        <div style="font-size:11px;color:#64748b;margin-top:4px;">
                            🌐 {result.get('language','?').upper()} ·
                            ⏱ {result.get('duration',0):.1f}s ·
                            📝 {result.get('word_count', len(text.split()))} words
                        </div>
                        """, unsafe_allow_html=True)
                        with st.spinner("🤖 ARIA is thinking..."):
                            _process_message(text, is_audio=True)
                        st.rerun()
                    else:
                        st.warning("No speech detected. Try speaking closer to your mic.")

            st.markdown("""
            <div style="background:#1e293b;border-radius:8px;padding:10px 14px;margin-top:8px;">
                <div style="font-size:11px;color:#475569;font-weight:600;
                            text-transform:uppercase;letter-spacing:0.05em;margin-bottom:5px;">
                    Browser support
                </div>
                <div style="font-size:12px;color:#64748b;line-height:1.7;">
                    ✅ Chrome · Edge (best)<br>
                    ✅ Firefox<br>
                    ✅ Safari 14.1+<br>
                    ⚠️ Requires HTTPS or localhost
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── TAB 2: FILE UPLOAD ────────────────────────────────────────────────
        with upload_tab:
            st.markdown("""
            <div style="background:linear-gradient(135deg,#1e1b4b,#1e3a5f);
                        border:2px dashed rgba(99,102,241,0.45);
                        border-radius:14px;padding:20px 16px;text-align:center;margin-bottom:10px;">
                <div style="font-size:32px;margin-bottom:6px;">📁</div>
                <div style="color:white;font-weight:600;font-size:14px;">Upload Recording</div>
                <div style="color:#94a3b8;font-size:12px;margin-top:4px;">
                    MP3 · WAV · M4A · OGG · WebM · FLAC · max 25 MB
                </div>
            </div>
            """, unsafe_allow_html=True)

            uploaded = st.file_uploader(
                "Audio file",
                type=["mp3","wav","m4a","ogg","webm","flac"],
                label_visibility="collapsed",
                key="voice_uploader",
            )

            lang = st.selectbox(
                "Language",
                ["en","auto","es","fr","de","it","pt","hi","zh","ja","ar"],
                format_func=lambda x: {
                    "en":"🇺🇸 English","auto":"🌐 Auto-detect","es":"🇪🇸 Spanish",
                    "fr":"🇫🇷 French","de":"🇩🇪 German","it":"🇮🇹 Italian",
                    "pt":"🇵🇹 Portuguese","hi":"🇮🇳 Hindi","zh":"🇨🇳 Chinese",
                    "ja":"🇯🇵 Japanese","ar":"🇸🇦 Arabic",
                }.get(x, x),
                key="stt_lang",
            )

            if uploaded:
                file_size = len(uploaded.getvalue()) / (1024*1024)
                st.markdown(f"""
                <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;
                            padding:10px 14px;margin:8px 0;">
                    <div style="font-size:13px;font-weight:600;color:#166534;">
                        📎 {uploaded.name}
                    </div>
                    <div style="font-size:11px;color:#4ade80;">
                        {file_size:.1f} MB · {uploaded.type or 'audio'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🎙️ Transcribe & Send", type="primary", use_container_width=True):
                    with st.spinner("🎙️ Transcribing with Whisper AI..."):
                        result = transcribe_uploaded(uploaded)
                    if "error" in result:
                        st.error(f"❌ {result['error']}")
                    elif result.get("text"):
                        text = result["text"]
                        st.markdown(f"""
                        <div style="background:#0f172a;border-radius:10px;padding:12px;
                                    font-family:monospace;font-size:13px;
                                    color:#a5f3fc;line-height:1.7;margin:8px 0;">
                            {text}
                        </div>
                        <div style="font-size:11px;color:#64748b;margin-top:4px;">
                            🌐 {result.get('language','?').upper()} ·
                            ⏱ {result.get('duration',0):.1f}s ·
                            📝 {result.get('word_count', len(text.split()))} words
                        </div>
                        """, unsafe_allow_html=True)
                        with st.spinner("🤖 ARIA is thinking..."):
                            _process_message(text, is_audio=True)
                        st.rerun()
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # ── TTS Settings ──
        st.markdown('<div class="sec-hdr">🔊 ARIA\'s Voice</div>', unsafe_allow_html=True)

        tts_toggle = st.toggle("Auto-speak responses", value=st.session_state.tts_enabled)
        st.session_state.tts_enabled = tts_toggle

        if tts_toggle:
            voice_names = list(VOICES.keys())
            voice_keys  = list(VOICES.values())
            cur_idx = voice_keys.index(st.session_state.tts_voice) if st.session_state.tts_voice in voice_keys else 4
            sel = st.selectbox(
                "Voice",
                voice_names,
                index=cur_idx,
                format_func=lambda v: f"{v} — {VOICE_DESCRIPTIONS[VOICES[v]]}",
            )
            st.session_state.tts_voice = VOICES[sel]

            spd = st.select_slider(
                "Speed",
                options=[0.75, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0],
                value=st.session_state.tts_speed if st.session_state.tts_speed in [0.75,0.9,1.0,1.1,1.25,1.5,1.75,2.0] else 1.0,
                format_func=lambda x: f"{x}x",
            )
            st.session_state.tts_speed = spd

            if st.button("▶ Preview Voice", use_container_width=True):
                test_audio = synthesize("Hi! I'm ARIA, your AI voice assistant. How can I help you today?",
                                       st.session_state.tts_voice, spd)
                if test_audio:
                    st.markdown(audio_to_html(test_audio, autoplay=True), unsafe_allow_html=True)
                else:
                    st.error("Could not generate audio. Check your API key.")

        # ── Active reminders ──
        active_rems = get_reminders(active_only=True)
        if active_rems:
            st.markdown('<div class="sec-hdr">🔔 Reminders</div>', unsafe_allow_html=True)
            for r in active_rems[:4]:
                rc1, rc2 = st.columns([5, 1])
                with rc1:
                    st.markdown(f"""
                    <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:9px;
                                padding:9px 12px;margin:4px 0;">
                        <div style="font-size:13px;font-weight:600;color:#92400e;">🔔 {r['reminder']}</div>
                        <div style="font-size:11px;color:#b45309;margin-top:2px;">⏰ {r['time']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with rc2:
                    if st.button("✓", key=f"rdis_{r['id']}"):
                        dismiss_reminder(r["id"])
                        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: CHAT HISTORY
# ═════════════════════════════════════════════════════════════════════════════
elif page == "💬 Chat History":
    st.markdown('<h1 style="color:#0f172a;font-size:26px;">💬 Chat History</h1>', unsafe_allow_html=True)

    conv = st.session_state.conversation
    if not conv:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;color:#94a3b8;">
            <div style="font-size:48px;margin-bottom:12px;">💬</div>
            <div style="font-size:16px;font-weight:600;color:#475569;">No messages yet</div>
            <div style="font-size:13px;margin-top:6px;">Start a conversation in Voice Chat</div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # Stats bar
    user_count = sum(1 for m in conv if m["role"] == "user")
    audio_count = sum(1 for m in conv if m.get("audio"))
    sc1, sc2, sc3, sc4 = st.columns(4)
    for col, val, lbl in [
        (sc1, len(conv), "Total Messages"),
        (sc2, user_count, "Your Messages"),
        (sc3, audio_count, "Voice Messages"),
        (sc4, len(conv) - user_count, "ARIA Responses"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card"><div class="v">{val}</div><div class="l">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    export_text = "\n\n".join(
        f"[{m.get('time','')}] {'YOU' if m['role']=='user' else 'ARIA'}: {m['content']}"
        for m in conv
    )
    col_exp, col_clr, _ = st.columns([2, 2, 6])
    with col_exp:
        st.download_button("⬇️ Export Chat", data=export_text,
                           file_name="aria_history.txt", mime="text/plain", use_container_width=True)
    with col_clr:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.conversation = []
            st.rerun()

    st.markdown("---")
    for msg in reversed(conv):
        role = msg["role"]
        icon = "👤" if role == "user" else "🤖"
        intent = msg.get("intent", "")
        action = msg.get("action", "")
        bg = "#eff6ff" if role == "user" else "#f8fafc"
        border = "#bfdbfe" if role == "user" else "#e2e8f0"
        aud_html = '<span class="audio-tag">🎙️</span>' if msg.get("audio") else ""
        intent_html = f'<span class="intent-tag">{intent}</span>' if intent and intent != "CHAT" else ""

        safe = msg["content"].replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
        st.markdown(f"""
        <div style="background:{bg};border:1px solid {border};border-radius:12px;
                    padding:14px 18px;margin:8px 0;">
            <div style="font-size:12px;color:#94a3b8;margin-bottom:6px;display:flex;align-items:center;gap:6px;">
                <span>{icon} <strong>{"You" if role=="user" else "ARIA"}</strong></span>
                <span>·</span><span>{msg.get('time','')}</span>
                {aud_html}{intent_html}
            </div>
            <div style="font-size:14px;color:#0f172a;line-height:1.65;">{safe}</div>
{"<div style='margin-top:8px;font-size:12px;font-weight:600;color:#166534;background:#f0fdf4;padding:6px 10px;border-radius:6px;'>🎯 " + action.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;") + "</div>" if action else ""}
        </div>
        """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: TASKS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "✅ Tasks":
    st.markdown('<h1 style="color:#0f172a;font-size:26px;">✅ Tasks</h1>', unsafe_allow_html=True)

    # Add task
    with st.form("add_task_form", clear_on_submit=True):
        st.markdown("**➕ Add New Task**")
        fc1, fc2, fc3 = st.columns([3, 2, 1])
        with fc1:
            new_task_text = st.text_input("Task", placeholder="What needs to be done?", label_visibility="collapsed")
        with fc2:
            new_dl = st.text_input("Deadline", placeholder="e.g. Friday, June 1", label_visibility="collapsed")
        with fc3:
            new_pri = st.selectbox("Priority", ["High","Medium","Low"], index=1, label_visibility="collapsed")
        submitted = st.form_submit_button("Add Task ➕", use_container_width=True, type="primary")
        if submitted and new_task_text:
            add_task(new_task_text, new_dl, new_pri)
            st.success("✅ Task added!")
            st.rerun()

    st.markdown("---")
    all_t = get_tasks("all")
    pending = [t for t in all_t if t["status"] == "pending"]
    done = [t for t in all_t if t["status"] == "done"]

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(f'<div class="sec-hdr">⏳ Pending — {len(pending)}</div>', unsafe_allow_html=True)
        if not pending:
            st.markdown("""
            <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
                        padding:20px;text-align:center;color:#15803d;">
                🎉 All done! No pending tasks.
            </div>
            """, unsafe_allow_html=True)
        for t in pending:
            pc = {"High":"b-high","Medium":"b-med","Low":"b-low"}.get(t.get("priority","Medium"),"b-med")
            st.markdown(f"""
            <div class="task-item">
                <div style="font-weight:600;color:#0f172a;font-size:14px;margin-bottom:6px;">
                    {t['task']}
                </div>
                <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                    <span class="badge {pc}">{t.get('priority','Medium')}</span>
                    {"<span style='font-size:12px;color:#64748b;'>📅 "+t['deadline']+"</span>" if t.get('deadline') else ""}
                    <span style="font-size:11px;color:#94a3b8;">Added {t['created_at'][:10]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            tc1, tc2 = st.columns(2)
            with tc1:
                if st.button("✓ Mark Done", key=f"done_{t['id']}", use_container_width=True, type="primary"):
                    complete_task(t["id"]); st.rerun()
            with tc2:
                if st.button("🗑️ Delete", key=f"dt_{t['id']}", use_container_width=True):
                    delete_task(t["id"]); st.rerun()

    with c2:
        st.markdown(f'<div class="sec-hdr">✅ Completed — {len(done)}</div>', unsafe_allow_html=True)
        if not done:
            st.info("No completed tasks yet.")
        for t in done:
            st.markdown(f"""
            <div class="task-done-item">
                <div style="font-weight:600;color:#374151;font-size:14px;text-decoration:line-through;">
                    ✅ {t['task']}
                </div>
                <div style="font-size:11px;color:#94a3b8;margin-top:4px;">
                    Completed {(t.get('completed_at') or '')[:16]}
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🗑️", key=f"dd_{t['id']}"):
                delete_task(t["id"]); st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: NOTES
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📝 Notes":
    st.markdown('<h1 style="color:#0f172a;font-size:26px;">📝 Notes</h1>', unsafe_allow_html=True)

    left, right = st.columns([2, 3])

    with left:
        st.markdown('<div class="sec-hdr">✍️ New Note</div>', unsafe_allow_html=True)
        with st.form("note_form", clear_on_submit=True):
            n_title = st.text_input("Title", placeholder="Note title...")
            n_tag   = st.selectbox("Tag", ["General","Meeting","Idea","Action","Research","Personal"])
            n_style = st.selectbox("AI Format Style", ["bullet","summary","action","formal"],
                                   format_func=lambda x: {"bullet":"• Bullet Points","summary":"📄 Summary","action":"✅ Action Items","formal":"📋 Formal Doc"}[x])
            n_content = st.text_area("Content", placeholder="Write your note...", height=150, label_visibility="collapsed")
            fc1, fc2 = st.columns(2)
            with fc1:
                save_btn = st.form_submit_button("💾 Save", type="primary", use_container_width=True)
            with fc2:
                fmt_btn = st.form_submit_button("✨ AI Format", use_container_width=True)

        if save_btn and n_content:
            add_note(n_title or f"Note {datetime.now().strftime('%H:%M')}", n_content, n_tag)
            st.success("✅ Note saved!")
            st.rerun()

        if fmt_btn and n_content:
            with st.spinner("✨ Formatting..."):
                formatted = generate_note_from_text(n_content, n_style)
            st.markdown('<div class="sec-hdr">✨ Formatted</div>', unsafe_allow_html=True)
            st.text_area("", value=formatted, height=200, label_visibility="collapsed", key="fmt_out")
            if st.button("💾 Save Formatted", type="primary", use_container_width=True):
                add_note(n_title or "Formatted Note", formatted, n_tag)
                st.success("✅ Saved!"); st.rerun()

    with right:
        st.markdown('<div class="sec-hdr">📋 Saved Notes</div>', unsafe_allow_html=True)
        notes = get_notes()
        if not notes:
            st.markdown("""
            <div style="text-align:center;padding:40px 20px;color:#94a3b8;">
                <div style="font-size:40px;margin-bottom:10px;">📝</div>
                <div>No notes yet. Create one or ask ARIA to take a note!</div>
            </div>
            """, unsafe_allow_html=True)
        tag_colors = {"Meeting":"#4f46e5","Idea":"#f59e0b","Action":"#dc2626",
                      "Research":"#0ea5e9","Personal":"#10b981","General":"#6b7280"}
        for n in notes:
            tc = tag_colors.get(n.get("tag","General"), "#6b7280")
            with st.expander(f"📄 {n['title']} · {n['created_at'][:10]}"):
                st.markdown(f'<span style="background:{tc};color:white;padding:2px 10px;border-radius:10px;font-size:11px;font-weight:600;">{n.get("tag","General")}</span>', unsafe_allow_html=True)
                st.text_area("", value=n["content"], height=130, key=f"nv_{n['id']}", label_visibility="collapsed")
                nc1, nc2 = st.columns([1, 1])
                with nc1:
                    st.download_button("⬇️ Download", data=n["content"], file_name=f"{n['title']}.txt", key=f"dln_{n['id']}", use_container_width=True)
                with nc2:
                    if st.button("🗑️ Delete", key=f"dn_{n['id']}", use_container_width=True):
                        delete_note(n["id"]); st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: REMINDERS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔔 Reminders":
    st.markdown('<h1 style="color:#0f172a;font-size:26px;">🔔 Reminders</h1>', unsafe_allow_html=True)

    with st.form("rem_form", clear_on_submit=True):
        st.markdown("**➕ New Reminder**")
        rc1, rc2 = st.columns([3, 2])
        with rc1:
            r_text = st.text_input("Reminder", placeholder="e.g. Call the doctor", label_visibility="collapsed")
        with rc2:
            r_time = st.text_input("When", placeholder="Tomorrow 9 AM", label_visibility="collapsed")
        if st.form_submit_button("Set Reminder 🔔", type="primary") and r_text:
            add_reminder(r_text, r_time)
            st.success("🔔 Reminder set!"); st.rerun()

    active = get_reminders(active_only=True)
    all_rems = get_reminders(active_only=False)
    dismissed = [r for r in all_rems if r["status"] == "dismissed"]

    st.markdown(f'<div class="sec-hdr">🔔 Active — {len(active)}</div>', unsafe_allow_html=True)
    if not active:
        st.markdown("""
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
                    padding:20px;text-align:center;color:#15803d;font-weight:500;">
            ✅ No active reminders — you're all set!
        </div>
        """, unsafe_allow_html=True)
    for r in active:
        status = get_reminder_status(r)
        border_color = {"overdue":"#ef4444","due-soon":"#f59e0b","upcoming":"#6366f1","no-time":"#94a3b8"}.get(status,"#94a3b8")
        status_label = {"overdue":"🔴 Overdue","due-soon":"🟡 Due Soon","upcoming":"🔵 Upcoming","no-time":"⚪ No time set"}.get(status,"")
        bg_color = {"overdue":"#fef2f2","due-soon":"#fffbeb","upcoming":"white","no-time":"#f8fafc"}.get(status,"white")
        due_info = f"⏰ {r.get('due_dt','')}" if r.get('due_dt') else f"⏰ {r['time']}"

        rc1, rc2 = st.columns([5, 1])
        with rc1:
            st.markdown(f"""
            <div style="background:{bg_color};border:1px solid {border_color};
                        border-left:4px solid {border_color};
                        border-radius:10px;padding:13px 16px;margin:6px 0;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div style="font-weight:600;color:#0f172a;font-size:14px;">🔔 {r['reminder']}</div>
                    <span style="font-size:11px;font-weight:700;color:{border_color};white-space:nowrap;margin-left:8px;">{status_label}</span>
                </div>
                <div style="font-size:12px;color:#64748b;margin-top:5px;">
                    {due_info} &nbsp;·&nbsp; Set {r['created_at']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with rc2:
            if st.button("✓ Done", key=f"rdis_{r['id']}", use_container_width=True):
                dismiss_reminder(r["id"]); st.rerun()

    if dismissed:
        with st.expander(f"✅ Dismissed ({len(dismissed)})"):
            for r in dismissed:
                st.markdown(f'<div style="font-size:13px;color:#94a3b8;padding:4px 0;text-decoration:line-through;">✓ {r["reminder"]} — {r["time"]}</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: CALENDAR
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📅 Calendar":
    st.markdown('<h1 style="color:#0f172a;font-size:26px;">📅 Calendar</h1>', unsafe_allow_html=True)

    with st.form("ev_form", clear_on_submit=True):
        st.markdown("**➕ New Event**")
        ec1, ec2, ec3 = st.columns([3, 2, 2])
        with ec1:
            ev_title = st.text_input("Event", placeholder="Team standup", label_visibility="collapsed")
        with ec2:
            ev_date = st.date_input("Date", label_visibility="collapsed")
        with ec3:
            ev_time = st.text_input("Time", placeholder="2:00 PM", label_visibility="collapsed")
        ev_notes = st.text_input("Notes (optional)", placeholder="Add details...", label_visibility="collapsed")
        if st.form_submit_button("Add Event 📅", type="primary") and ev_title:
            add_calendar_event(ev_title, str(ev_date), ev_time, ev_notes)
            st.success(f"📅 Added: {ev_title}"); st.rerun()

    events = get_calendar_events()
    today = local_now().strftime("%Y-%m-%d")
    upcoming = [e for e in events if e.get("date","") >= today]
    past = [e for e in events if e.get("date","") < today]

    st.markdown(f'<div class="sec-hdr">📅 Upcoming — {len(upcoming)}</div>', unsafe_allow_html=True)
    if not upcoming:
        st.info("No upcoming events. Ask ARIA to schedule one!")
    for e in upcoming:
        status = get_event_status(e)
        status_map = {
            "starting-now": ("🔴 Starting NOW!", "#dc2626"),
            "soon":         ("🟡 Starting Soon", "#d97706"),
            "today":        ("🔵 Today",          "#6366f1"),
            "upcoming":     ("🟢 Upcoming",        "#16a34a"),
            "past":         ("⚫ Past",            "#6b7280"),
        }
        timing, badge_color = status_map.get(status, ("📅", "#6b7280"))
        at_time = f"at {e['time']}" if e.get('time') else ""
        notes_bit = f"· {e.get('notes','')}" if e.get('notes') else ""

        st.markdown(f"""
        <div style="background:white;border:1px solid #e2e8f0;border-left:5px solid {badge_color};
                    border-radius:12px;padding:14px 18px;margin:8px 0;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
                <div>
                    <div style="font-weight:700;color:#0f172a;font-size:15px;">📅 {e['title']}</div>
                    <div style="font-size:12px;color:#64748b;margin-top:5px;">
                        {e['date']} {at_time} {notes_bit}
                    </div>
                </div>
                <span style="background:{badge_color};color:white;padding:3px 12px;
                             border-radius:12px;font-size:11px;font-weight:700;white-space:nowrap;">
                    {timing}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🗑️", key=f"dev_{e['id']}"):
            delete_calendar_event(e["id"]); st.rerun()

    if past:
        with st.expander(f"🕐 Past Events ({len(past)})"):
            for e in reversed(past[-8:]):
                st.markdown(f'<div style="font-size:13px;color:#94a3b8;padding:4px 0;">✓ {e["title"]} — {e["date"]}</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📊 Dashboard":
    import plotly.graph_objects as go

    st.markdown('<h1 style="color:#0f172a;font-size:26px;">📊 Dashboard</h1>', unsafe_allow_html=True)

    stats = get_analytics()
    conv = st.session_state.conversation
    user_msgs = sum(1 for m in conv if m["role"] == "user")
    audio_msgs = sum(1 for m in conv if m.get("audio"))

    k1, k2, k3, k4, k5 = st.columns(5)
    for col, val, lbl, color in [
        (k1, len(conv), "Messages", "#6366f1"),
        (k2, stats["total_tasks"], "Total Tasks", "#8b5cf6"),
        (k3, stats["pending_tasks"], "Pending", "#f59e0b"),
        (k4, f"{stats['completion_rate']}%", "Completion", "#10b981"),
        (k5, stats["total_notes"], "Notes", "#06b6d4"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card" style="border-color:{color};"><div class="v">{val}</div><div class="l">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    d1, d2 = st.columns(2)

    with d1:
        st.markdown('<div class="sec-hdr">🎯 Task Priorities</div>', unsafe_allow_html=True)
        pc = stats["priority_counts"]
        if any(pc.values()):
            fig = go.Figure(go.Pie(
                labels=list(pc.keys()), values=list(pc.values()),
                marker_colors=["#dc2626","#d97706","#16a34a"], hole=0.5,
                textinfo="label+percent",
            ))
            fig.update_layout(margin=dict(l=0,r=0,t=10,b=10), height=260,
                              paper_bgcolor="white", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add some tasks to see priority breakdown.")

    with d2:
        st.markdown('<div class="sec-hdr">💬 Intent Breakdown</div>', unsafe_allow_html=True)
        intent_map = {}
        for msg in conv:
            if msg["role"] == "assistant":
                it = msg.get("intent","CHAT")
                intent_map[it] = intent_map.get(it, 0) + 1
        if intent_map:
            colors_map = {"CHAT":"#6366f1","CREATE_TASK":"#f59e0b","CREATE_NOTE":"#0ea5e9",
                          "CREATE_REMINDER":"#10b981","CALENDAR_EVENT":"#8b5cf6","SEARCH_WEB":"#06b6d4"}
            fig2 = go.Figure(go.Bar(
                y=list(intent_map.keys()), x=list(intent_map.values()), orientation="h",
                marker_color=[colors_map.get(k,"#6366f1") for k in intent_map],
                marker_line_width=0,
            ))
            fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                               margin=dict(l=10,r=10,t=10,b=10), height=260,
                               xaxis=dict(showgrid=True, gridcolor="#f1f5f9"))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Start chatting to see intent analytics.")

    # Bottom summary
    sm1, sm2, sm3, sm4 = st.columns(4)
    for col, icon, lbl, val, desc in [
        (sm1, "📅", "Events", stats["total_events"], "Scheduled"),
        (sm2, "🔔", "Reminders", stats["active_reminders"], "Active"),
        (sm3, "🎙️", "Voice Msgs", audio_msgs, f"of {user_msgs} total"),
        (sm4, "⚡", "Session", st.session_state.session_id, "ID"),
    ]:
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:28px;">{icon}</div>
                <div style="font-size:22px;font-weight:800;color:#0f172a;margin:4px 0;">{val}</div>
                <div style="font-size:12px;font-weight:700;color:#374151;">{lbl}</div>
                <div style="font-size:11px;color:#94a3b8;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.markdown('<h1 style="color:#0f172a;font-size:26px;">⚙️ Settings</h1>', unsafe_allow_html=True)

    current_key = _active_key()

    if current_key:
        src = "Your key (entered below)" if st.session_state.get("user_api_key","").strip() else "Server-configured"
        st.markdown(f"""
        <div style="background:#f0fdf4;border:2px solid #86efac;border-radius:12px;
                    padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px;">
            <div style="font-size:24px;">🟢</div>
            <div>
                <div style="font-weight:700;color:#15803d;font-size:15px;">API Key Active</div>
                <div style="font-size:12px;color:#166534;">Source: {src}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#fef2f2;border:2px solid #fca5a5;border-radius:12px;
                    padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px;">
            <div style="font-size:24px;">🔴</div>
            <div>
                <div style="font-weight:700;color:#dc2626;font-size:15px;">No API Key</div>
                <div style="font-size:12px;color:#991b1b;">Enter your OpenAI key below to get started</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    s1, s2 = st.columns([3, 2])

    with s1:
        st.markdown('<div class="sec-hdr">🔑 OpenAI API Key</div>', unsafe_allow_html=True)
        entered = st.text_input("API Key", value=st.session_state.get("user_api_key",""),
                                type="password", placeholder="sk-proj-...",
                                label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Save Key", type="primary", use_container_width=True):
                if entered.strip().startswith("sk-"):
                    st.session_state.user_api_key = entered.strip()
                    os.environ["OPENAI_API_KEY"] = entered.strip()
                    st.success("✅ Key saved! Ready to use.")
                    st.rerun()
                elif entered.strip():
                    st.error("❌ Keys must start with 'sk-'")
                else:
                    st.error("Please enter an API key.")
        with c2:
            if st.button("🗑️ Clear Key", use_container_width=True):
                st.session_state.user_api_key = ""
                os.environ.pop("OPENAI_API_KEY", None)
                st.success("Key cleared."); st.rerun()

        st.markdown("""
        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;
                    padding:12px 14px;margin-top:10px;font-size:13px;color:#78350f;">
            🔒 <strong>Private:</strong> Stored only in your browser session.
            Never saved to any server or database. Cleared when you close the tab.
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sec-hdr">🎙️ Voice Settings</div>', unsafe_allow_html=True)
        tts = st.toggle("Auto-speak ARIA responses", st.session_state.tts_enabled)
        st.session_state.tts_enabled = tts

        voice_names = list(VOICES.keys())
        voice_keys  = list(VOICES.values())
        cur_i = voice_keys.index(st.session_state.tts_voice) if st.session_state.tts_voice in voice_keys else 4
        sel = st.selectbox("Voice", voice_names, index=cur_i,
                           format_func=lambda v: f"{v} — {VOICE_DESCRIPTIONS[VOICES[v]]}")
        st.session_state.tts_voice = VOICES[sel]
        spd = st.select_slider("Speed", [0.75,0.9,1.0,1.1,1.25,1.5,1.75,2.0],
                               value=st.session_state.tts_speed if st.session_state.tts_speed in [0.75,0.9,1.0,1.1,1.25,1.5,1.75,2.0] else 1.0,
                               format_func=lambda x: f"{x}x")
        st.session_state.tts_speed = spd

        st.markdown('<div class="sec-hdr">🗄️ Data</div>', unsafe_allow_html=True)
        db_status = "🟢 Connected" if db_ok() else "🔴 Not configured"
        st.markdown(f"**Database:** {db_status}")
        if st.button("🗑️ Clear All Session Data", use_container_width=True):
            for k in ["conversation","tasks","notes","reminders","calendar_events","last_audio"]:
                if k in st.session_state:
                    del st.session_state[k]
            init_stores()
            st.session_state.conversation = []
            st.success("All cleared."); st.rerun()

    with s2:
        st.markdown('<div class="sec-hdr">📋 How to get an API key</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="card">
            <div style="font-size:13px;color:#374151;line-height:2.1;">
                1. Visit <a href="https://platform.openai.com/api-keys" target="_blank"
                   style="color:#6366f1;font-weight:600;">platform.openai.com/api-keys</a><br>
                2. Sign in or create an account<br>
                3. Click <strong>+ Create new secret key</strong><br>
                4. Copy the key (starts with <code>sk-</code>)<br>
                5. Paste it on the left → Save
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sec-hdr">💰 Cost Estimate</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="card">
            <div style="font-size:13px;color:#374151;line-height:2.0;">
                🎙️ Whisper: ~$0.006/min audio<br>
                🧠 GPT-4o: ~$0.005/message<br>
                🔊 TTS: ~$0.015/1K characters<br>
                <br>
                <strong style="color:#0f172a;">20-msg session ≈ $0.15 total</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if current_key:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🎙️ Start talking with ARIA →", type="primary"):
            st.session_state.page = "🎙️ Voice Chat"; st.rerun()
