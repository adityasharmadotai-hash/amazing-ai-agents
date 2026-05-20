"""
app.py — AI Meeting Notes Agent
Streamlit application — upload audio/video, transcribe, analyze, export.
"""

import os
import sys
import json

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Meeting Notes Agent",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f1e 0%, #111827 60%, #0d1b2a 100%) !important;
}
[data-testid="stSidebar"] > div:first-child { background: transparent !important; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] div, [data-testid="stSidebar"] label { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important; color: #e2e8f0 !important;
    font-size: 14px !important; font-weight: 500 !important;
    padding: 11px 16px !important; text-align: left !important;
    width: 100% !important; margin: 2px 0 !important;
    transition: all 0.18s !important; box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(79,70,229,0.3) !important;
    border-color: rgba(79,70,229,0.55) !important; color: #fff !important;
}
[data-testid="stSidebar"] .stButton > button:hover p { color: #fff !important; }

/* ── Active nav button — current page indicator ── */
[data-testid="stSidebar"] .nav-active > button,
[data-testid="stSidebar"] .nav-active > button:hover {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
    border-left: 4px solid #a78bfa !important;
    border-top: 1px solid rgba(167,139,250,0.4) !important;
    border-right: 1px solid rgba(167,139,250,0.2) !important;
    border-bottom: 1px solid rgba(167,139,250,0.2) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 20px rgba(79,70,229,0.5), inset 0 1px 0 rgba(255,255,255,0.15) !important;
    transform: translateX(3px) !important;
}
[data-testid="stSidebar"] .nav-active > button p,
[data-testid="stSidebar"] .nav-active > button span {
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* ── Cards ── */
.glass-card {
    background: white; border: 1px solid #e2e8f0;
    border-radius: 16px; padding: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 16px;
}
.metric-card {
    background: white; border-radius: 14px; padding: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    border-top: 4px solid #4f46e5; text-align: center;
}
.metric-card .val { font-size: 30px; font-weight: 800; color: #0f172a; }
.metric-card .lbl { font-size: 12px; color: #64748b; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }

/* ── Section header ── */
.section-header {
    background: linear-gradient(90deg, #4f46e5, #7c3aed);
    color: white; border-radius: 12px; padding: 13px 20px;
    margin: 20px 0 16px; font-size: 16px; font-weight: 600;
}

/* ── Priority badges ── */
.badge { display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 600; margin: 2px; }
.badge-high   { background:#fef2f2; color:#dc2626; border:1px solid #fecaca; }
.badge-medium { background:#fffbeb; color:#d97706; border:1px solid #fde68a; }
.badge-low    { background:#f0fdf4; color:#16a34a; border:1px solid #bbf7d0; }
.badge-info   { background:#eff6ff; color:#2563eb; border:1px solid #bfdbfe; }

/* ── Sentiment chips ── */
.sent-positive { background:#f0fdf4; color:#16a34a; border:1px solid #bbf7d0;
    padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
.sent-neutral  { background:#f8fafc; color:#475569; border:1px solid #e2e8f0;
    padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
.sent-mixed    { background:#fffbeb; color:#d97706; border:1px solid #fde68a;
    padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
.sent-tense    { background:#fef2f2; color:#dc2626; border:1px solid #fecaca;
    padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }

/* ── Upload area ── */
[data-testid="stFileUploader"] {
    border: 2px dashed #818cf8; border-radius: 14px;
    background: #eef2ff; padding: 8px;
}

/* ── Text areas (content display) ── */
[data-testid="stTextArea"] textarea {
    background: #0f172a !important; color: #e2e8f0 !important;
    font-family: 'Inter', monospace !important; font-size: 13px !important;
    line-height: 1.75 !important; border: 1px solid #1e293b !important;
    border-radius: 10px !important; padding: 16px !important;
}
[data-testid="stTextArea"] textarea:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 2px rgba(79,70,229,0.15) !important;
}

/* ── Person task cards ── */
.person-card {
    background: #f8fafc; border-left: 4px solid #4f46e5;
    border-radius: 10px; padding: 14px 18px; margin: 8px 0;
}

/* ── Action item row ── */
.action-row {
    background: white; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 12px 16px; margin: 6px 0;
    display: flex; gap: 12px; align-items: flex-start;
}

/* ── Divider ── */
.nav-divider { height: 1px; background: rgba(255,255,255,0.08); margin: 10px 0; }

/* ── Progress ── */
.stProgress > div > div { border-radius: 8px; background: #4f46e5; }

/* ── Buttons ── */
.stButton button { border-radius: 10px; font-weight: 600; transition: all 0.2s; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #f1f5f9; border-radius: 12px; padding: 4px; gap: 2px;
}
.stTabs [data-baseweb="tab"] { border-radius: 9px; font-weight: 500; }
.stTabs [aria-selected="true"] {
    background: white !important; box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}

/* Hide branding */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Imports ───────────────────────────────────────────────────────────────────
from modules.agent import is_configured, analyze_meeting, generate_follow_up_email, ask_about_meeting, extract_meeting_title
from modules.database import init_db, is_configured as db_ok, save_meeting, get_all_meetings, get_meeting_by_id, search_meetings, get_analytics, delete_meeting
from modules.transcriber import transcribe_audio, format_duration
from modules.exporter import export_markdown, export_pdf, export_docx

# Inject user-provided API key into env so all modules pick it up
def _sync_api_key():
    user_key = st.session_state.get("user_api_key", "").strip()
    if user_key:
        os.environ["OPENAI_API_KEY"] = user_key

_sync_api_key()
init_db()

# ── Credential check — allow user key from Settings page ─────────────────────
def _get_active_api_key() -> str:
    """Return user-provided key from session, or key from secrets/env."""
    session_key = st.session_state.get("user_api_key", "").strip()
    if session_key:
        return session_key
    try:
        return st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    except Exception:
        return os.environ.get("OPENAI_API_KEY", "")

def _check_creds():
    if not _get_active_api_key():
        st.markdown("""
        <div style="background:#fef2f2;border:2px solid #fecaca;border-radius:16px;
                    padding:36px;max-width:560px;margin:60px auto;text-align:center;">
            <div style="font-size:52px;">🔑</div>
            <h2 style="color:#dc2626;margin:12px 0 8px;">API Key Required</h2>
            <p style="color:#7f1d1d;font-size:15px;">
                Go to <strong>⚙️ Settings</strong> in the sidebar<br>
                and enter your OpenAI API key to get started.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.info("👈 Click **⚙️ Settings** in the sidebar to add your API key")
        st.stop()

# ── Session state ─────────────────────────────────────────────────────────────
def _ss(key, default=None):
    if key not in st.session_state:
        st.session_state[key] = default

_ss("page", "🏠 Home")
_ss("transcript_data", None)
_ss("analysis", None)
_ss("follow_up_email", None)
_ss("meeting_title", "")
_ss("saved_meeting_id", None)
_ss("user_api_key", "")

# ── Nav pages ─────────────────────────────────────────────────────────────────
NAV = [
    ("🏠", "Home"), ("🎙️", "Upload & Transcribe"),
    ("📋", "Meeting Analysis"), ("✉️", "Follow-up Email"),
    ("🔍", "Search Meetings"), ("📊", "Analytics"), ("📁", "History"),
    ("⚙️", "Settings"),
]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # API key status indicator
    has_key = bool(_get_active_api_key())
    key_source = "session" if st.session_state.get("user_api_key","").strip() else "env"
    key_indicator = "🟢" if has_key else "🔴"

    st.markdown(f"""
    <div style="padding:22px 4px 18px;text-align:center;">
        <div style="font-size:52px;">🎙️</div>
        <div style="font-size:17px;font-weight:800;color:white;margin-top:10px;">
            Meeting Notes AI</div>
        <div style="font-size:11px;color:#475569;margin-top:5px;">
            ✦ Powered by OpenAI GPT-4o</div>
        <div style="font-size:11px;margin-top:8px;">
            {key_indicator} {"API key active" if has_key else "No API key — go to Settings"}
        </div>
    </div>
    <div class="nav-divider"></div>
    <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:0.1em;
                font-weight:600;padding:0 4px;margin-bottom:6px;">Navigation</div>
    """, unsafe_allow_html=True)

    current_page = st.session_state.get("page", "🏠 Home")

    for icon, label in NAV:
        full = f"{icon} {label}"
        is_active = (current_page == full)
        # Wrap in a div with class nav-active when this page is selected
        if is_active:
            st.markdown('<div class="nav-active">', unsafe_allow_html=True)
        if st.button(
            f"{'✦  ' if is_active else ''}{icon}  {label}",
            key=f"nav_{label}",
            use_container_width=True,
        ):
            st.session_state.page = full
            st.rerun()
        if is_active:
            st.markdown('</div>', unsafe_allow_html=True)

    page = st.session_state.get("page", "🏠 Home")

    # Active meeting indicator
    if st.session_state.analysis:
        title = st.session_state.analysis.get("title", "Meeting")[:35]
        st.markdown(f"""
        <div class="nav-divider"></div>
        <div style="background:rgba(79,70,229,0.18);border:1px solid rgba(79,70,229,0.35);
                    border-radius:10px;padding:11px 13px;margin:4px 0;">
            <div style="font-size:10px;color:#818cf8;text-transform:uppercase;
                        letter-spacing:0.08em;font-weight:600;">🎙️ Active Meeting</div>
            <div style="font-size:12px;font-weight:600;color:white;margin-top:5px;
                        line-height:1.35;">{title}</div>
            <div style="font-size:11px;color:#475569;margin-top:4px;">
                {len(st.session_state.analysis.get('action_items', []))} action items ·
                {len(st.session_state.analysis.get('decisions', []))} decisions
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="nav-divider"></div>
    <div style="font-size:11px;color:#334155;text-align:center;padding:4px 0 8px;">
        Built with ❤️ by
        <a href="https://www.adityasharma.ai" target="_blank"
           style="color:#818cf8;">adityasharma.ai</a>
    </div>
    """, unsafe_allow_html=True)


# ── Guard: require API key for all pages except Settings ─────────────────────
if page != "⚙️ Settings":
    _sync_api_key()
    _check_creds()

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: HOME
# ═════════════════════════════════════════════════════════════════════════════
if page == "🏠 Home":
    st.markdown("""
    <div style="padding:8px 0 28px;">
        <h1 style="font-size:34px;font-weight:800;color:#0f172a;margin:0;">
            🎙️ AI Meeting Notes Agent
        </h1>
        <p style="color:#64748b;font-size:16px;margin-top:8px;">
            Upload your meeting recording → get instant summaries, action items,
            decisions, tasks by person, and a follow-up email draft.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    f1, f2, f3, f4 = st.columns(4)
    for col, icon, title, desc in [
        (f1, "🎙️", "Upload Audio/Video", "MP3, WAV, MP4 — Whisper AI transcribes in seconds"),
        (f2, "🧠", "AI Analysis", "Summary, decisions, action items, tasks by person"),
        (f3, "✉️", "Follow-up Email", "Auto-drafted email ready to send in one click"),
        (f4, "📥", "Export", "Download as PDF, DOCX, or Markdown"),
    ]:
        with col:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center;padding:24px 16px;">
                <div style="font-size:36px;">{icon}</div>
                <div style="font-weight:700;color:#0f172a;margin:10px 0 6px;font-size:14px;">{title}</div>
                <div style="font-size:12px;color:#64748b;line-height:1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick stats if DB is connected
    if db_ok():
        stats = get_analytics()
        if stats["total_meetings"] > 0:
            st.markdown('<div class="section-header">📊 Your Meeting Stats</div>', unsafe_allow_html=True)
            s1, s2, s3, s4 = st.columns(4)
            for col, val, lbl in [
                (s1, stats["total_meetings"], "Meetings Recorded"),
                (s2, f"{stats['total_duration_mins']:.0f} min", "Total Duration"),
                (s3, f"{stats['avg_duration_mins']:.0f} min", "Avg Duration"),
                (s4, stats["avg_attendees"], "Avg Attendees"),
            ]:
                with col:
                    st.markdown(f'<div class="metric-card"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

    # How it works
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">🚀 How It Works</div>', unsafe_allow_html=True)
    h1, h2, h3, h4, h5 = st.columns(5)
    for col, num, step in [
        (h1, "1", "Upload MP3, WAV, or MP4 recording"),
        (h2, "2", "Whisper AI transcribes speech to text"),
        (h3, "3", "GPT-4o analyses and structures the meeting"),
        (h4, "4", "Review summary, actions, and decisions"),
        (h5, "5", "Export PDF/DOCX or send the email draft"),
    ]:
        with col:
            st.markdown(f"""
            <div style="text-align:center;padding:16px 8px;">
                <div style="width:36px;height:36px;background:#4f46e5;color:white;
                            border-radius:50%;font-weight:800;font-size:16px;
                            display:flex;align-items:center;justify-content:center;
                            margin:0 auto 10px;">{num}</div>
                <div style="font-size:12px;color:#374151;line-height:1.5;">{step}</div>
            </div>
            """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: UPLOAD & TRANSCRIBE
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🎙️ Upload & Transcribe":
    st.markdown('<h1 style="color:#0f172a;">🎙️ Upload & Transcribe</h1>', unsafe_allow_html=True)

    col_up, col_info = st.columns([3, 2])

    with col_up:
        st.markdown('<div class="section-header">📎 Upload Recording</div>', unsafe_allow_html=True)
        meeting_title_input = st.text_input(
            "Meeting Title (optional)",
            placeholder="e.g. Q4 Planning, Sprint Review, Client Call",
            value=st.session_state.meeting_title,
        )
        attendees_input = st.text_input(
            "Attendees (optional)",
            placeholder="e.g. Alice, Bob, Carol — or leave blank for auto-detection",
        )

        uploaded = st.file_uploader(
            "Drop your recording here",
            type=["mp3", "wav", "mp4", "m4a", "webm", "ogg"],
            help="Supports MP3, WAV, MP4, M4A, WebM, OGG · Max 25MB (Whisper API limit)",
        )

        if uploaded:
            size_mb = len(uploaded.getvalue()) / (1024 * 1024)
            st.markdown(f"""
            <div class="glass-card" style="padding:14px 18px;">
                <div style="font-weight:600;color:#0f172a;">📄 {uploaded.name}</div>
                <div style="font-size:12px;color:#64748b;margin-top:4px;">
                    {size_mb:.1f} MB · {uploaded.type or "audio file"}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🎙️ Transcribe with Whisper AI", type="primary", use_container_width=True):
                with st.spinner("🎙️ Transcribing audio... this may take 30-60 seconds for longer recordings..."):
                    result = transcribe_audio(uploaded)

                if "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.session_state.transcript_data = result
                    st.session_state.meeting_title = meeting_title_input or result.get("filename", "Meeting")
                    st.session_state.analysis = None
                    st.session_state.follow_up_email = None
                    st.session_state.saved_meeting_id = None
                    st.success(f"✅ Transcribed! {result['word_count']:,} words · {format_duration(result['duration_seconds'])}")
                    st.rerun()

    with col_info:
        st.markdown('<div class="section-header">ℹ️ Tips</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-card">
            <div style="font-weight:600;color:#0f172a;margin-bottom:10px;">📋 Supported Formats</div>
            <div style="font-size:13px;color:#374151;line-height:1.8;">
                🎵 <strong>MP3</strong> — most common, small file size<br>
                🎵 <strong>WAV</strong> — high quality, larger files<br>
                🎬 <strong>MP4</strong> — video meetings (Zoom, Teams)<br>
                🎵 <strong>M4A, WebM, OGG</strong> — also supported<br>
            </div>
            <div style="margin-top:14px;font-weight:600;color:#0f172a;">⚡ Performance Tips</div>
            <div style="font-size:13px;color:#374151;line-height:1.8;margin-top:6px;">
                • Max 25 MB per file<br>
                • Compress MP4 to MP3 for faster upload<br>
                • Clear audio = better transcription<br>
                • Works best with English (auto-detects language)<br>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.transcript_data:
            td = st.session_state.transcript_data
            st.markdown(f"""
            <div class="glass-card" style="background:#f0fdf4;border-color:#bbf7d0;">
                <div style="font-weight:700;color:#15803d;font-size:14px;margin-bottom:8px;">
                    ✅ Transcript Ready
                </div>
                <div style="font-size:12px;color:#374151;line-height:1.8;">
                    📝 {td['word_count']:,} words<br>
                    ⏱ {format_duration(td['duration_seconds'])}<br>
                    🌐 Language: {td.get('language','Unknown')}<br>
                    📁 {td['filename']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("→ Analyze Meeting", type="primary", use_container_width=True):
                st.session_state.page = "📋 Meeting Analysis"
                st.rerun()

    # Transcript viewer
    if st.session_state.transcript_data:
        st.markdown('<div class="section-header">📄 Transcript</div>', unsafe_allow_html=True)
        td = st.session_state.transcript_data
        t1, t2 = st.tabs(["📝 Full Text", "⏱️ Segments"])
        with t1:
            st.text_area(
                "transcript_full",
                value=td["text"],
                height=350,
                label_visibility="collapsed",
            )
            st.download_button(
                "⬇️ Download Transcript (.txt)",
                data=td["text"],
                file_name=f"transcript_{td['filename']}.txt",
                mime="text/plain",
            )
        with t2:
            segs = td.get("segments", [])
            if segs:
                for seg in segs:
                    m = int(seg["start"] // 60)
                    s = int(seg["start"] % 60)
                    st.markdown(
                        f'<div style="display:flex;gap:12px;padding:6px 0;border-bottom:1px solid #f1f5f9;">'
                        f'<span style="color:#4f46e5;font-weight:600;min-width:48px;font-family:monospace;">'
                        f'{m:02d}:{s:02d}</span>'
                        f'<span style="font-size:13px;color:#374151;">{seg["text"]}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("Segment timestamps not available for this file.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: MEETING ANALYSIS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📋 Meeting Analysis":
    st.markdown('<h1 style="color:#0f172a;">📋 Meeting Analysis</h1>', unsafe_allow_html=True)

    if not st.session_state.transcript_data:
        st.warning("⚠️ No transcript yet. Upload a recording first.")
        st.stop()

    td = st.session_state.transcript_data

    # Analyze button
    if not st.session_state.analysis:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size:15px;font-weight:600;color:#0f172a;">Ready to analyze</div>
            <div style="font-size:13px;color:#64748b;margin-top:4px;">
                📝 {td['word_count']:,} words · ⏱ {format_duration(td['duration_seconds'])} · 
                📁 {td['filename']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🧠 Analyze with GPT-4o", type="primary", use_container_width=False):
            with st.spinner("🧠 GPT-4o is analyzing your meeting... ~15-30 seconds..."):
                analysis = analyze_meeting(
                    td["text"],
                    st.session_state.meeting_title,
                    "",
                )
            if "error" in analysis and len(analysis) == 1:
                st.error(f"Analysis failed: {analysis['error']}")
            else:
                st.session_state.analysis = analysis

                # Auto-generate follow-up email
                with st.spinner("✉️ Drafting follow-up email..."):
                    email = generate_follow_up_email(analysis, td["text"])
                st.session_state.follow_up_email = email

                # Auto-save to DB
                if db_ok():
                    mid = save_meeting(
                        analysis.get("title", st.session_state.meeting_title or "Meeting"),
                        td["filename"],
                        td["text"],
                        analysis,
                        email,
                        td.get("duration_seconds", 0),
                        td.get("word_count", 0),
                        td.get("file_size_mb", 0),
                    )
                    st.session_state.saved_meeting_id = mid

                st.success("✅ Analysis complete!")
                st.rerun()

    else:
        analysis = st.session_state.analysis

        # ── Title & meta ──
        title = analysis.get("title", "Meeting")
        attendees = analysis.get("attendees", [])
        sentiment = analysis.get("sentiment", "Neutral")
        effectiveness = analysis.get("meeting_effectiveness", "")
        next_mtg = analysis.get("next_meeting_suggested", "")

        sent_class = {
            "Positive": "sent-positive", "Neutral": "sent-neutral",
            "Mixed": "sent-mixed", "Tense": "sent-tense",
        }.get(sentiment, "sent-neutral")

        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size:22px;font-weight:800;color:#0f172a;">{title}</div>
            <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:10px;align-items:center;">
                <span class="{sent_class}">{sentiment}</span>
                <span class="badge badge-info">⚡ {effectiveness} Effectiveness</span>
                {'<span class="badge badge-info">📅 ' + next_mtg + '</span>' if next_mtg else ''}
                <span class="badge badge-info">👥 {len(attendees)} attendees</span>
            </div>
            <div style="font-size:12px;color:#64748b;margin-top:8px;">
                Attendees: {", ".join(attendees) or "Not detected"}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Tabs ──
        tabs = st.tabs(["📝 Summary", "✅ Action Items", "⚖️ Decisions", "👤 By Person", "⚠️ Risks", "💬 Q&A", "📥 Export"])

        # ─ Summary tab ─
        with tabs[0]:
            st.markdown('<div class="section-header">📝 Executive Summary</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="glass-card">
                <p style="font-size:15px;line-height:1.8;color:#374151;margin:0;">
                    {analysis.get('summary', '')}
                </p>
            </div>
            """, unsafe_allow_html=True)

            topics = analysis.get("key_topics", [])
            if topics:
                st.markdown('<div class="section-header">🏷️ Key Topics</div>', unsafe_allow_html=True)
                pill_html = '<div style="display:flex;flex-wrap:wrap;gap:8px;">' + "".join(
                    f'<span class="badge badge-info">{t}</span>' for t in topics
                ) + '</div>'
                st.markdown(pill_html, unsafe_allow_html=True)

        # ─ Action Items tab ─
        with tabs[1]:
            st.markdown('<div class="section-header">✅ Action Items</div>', unsafe_allow_html=True)
            action_items = analysis.get("action_items", [])
            if action_items:
                for i, ai in enumerate(action_items, 1):
                    priority = ai.get("priority", "Medium")
                    p_class = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}.get(priority, "badge-medium")
                    st.markdown(f"""
                    <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;
                                padding:14px 18px;margin:8px 0;border-left:4px solid #4f46e5;">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                            <div style="font-weight:600;color:#0f172a;font-size:14px;">
                                {i}. {ai.get('task','')}
                            </div>
                            <span class="badge {p_class}">{priority}</span>
                        </div>
                        <div style="font-size:12px;color:#64748b;margin-top:6px;display:flex;gap:16px;">
                            <span>👤 {ai.get('owner','TBD')}</span>
                            <span>📅 {ai.get('deadline','TBD')}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No action items detected in this meeting.")

        # ─ Decisions tab ─
        with tabs[2]:
            st.markdown('<div class="section-header">⚖️ Decisions Made</div>', unsafe_allow_html=True)
            decisions = analysis.get("decisions", [])
            if decisions:
                for i, d in enumerate(decisions, 1):
                    st.markdown(f"""
                    <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;
                                padding:16px 18px;margin:8px 0;border-left:4px solid #7c3aed;">
                        <div style="font-weight:700;color:#0f172a;font-size:14px;">
                            {i}. {d.get('decision','')}
                        </div>
                        <div style="font-size:12px;color:#64748b;margin-top:6px;">
                            👤 Owner: <strong>{d.get('owner','TBD')}</strong>
                        </div>
                        <div style="font-size:13px;color:#374151;margin-top:6px;">
                            {d.get('context','')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No explicit decisions recorded.")

        # ─ By Person tab ─
        with tabs[3]:
            st.markdown('<div class="section-header">👤 Tasks by Person</div>', unsafe_allow_html=True)
            tasks_by_person = analysis.get("tasks_by_person", {})
            if tasks_by_person:
                cols = st.columns(min(len(tasks_by_person), 3))
                for i, (person, tasks) in enumerate(tasks_by_person.items()):
                    with cols[i % 3]:
                        st.markdown(f"""
                        <div class="person-card">
                            <div style="font-weight:700;color:#4f46e5;font-size:15px;margin-bottom:10px;">
                                👤 {person}
                            </div>
                            {''.join(f'<div style="font-size:13px;color:#374151;padding:4px 0;border-bottom:1px solid #e2e8f0;">• {t}</div>' for t in tasks)}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No per-person task assignment detected.")

        # ─ Risks tab ─
        with tabs[4]:
            st.markdown('<div class="section-header">⚠️ Risks & Blockers</div>', unsafe_allow_html=True)
            risks = analysis.get("risks_blockers", [])
            follow_ups = analysis.get("follow_up_questions", [])

            if risks:
                for r in risks:
                    st.markdown(f"""
                    <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;
                                padding:12px 16px;margin:6px 0;color:#dc2626;">
                        ⚠️ {r}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("No risks or blockers identified.")

            if follow_ups:
                st.markdown('<div class="section-header">❓ Open Questions</div>', unsafe_allow_html=True)
                for q in follow_ups:
                    st.markdown(f"""
                    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
                                padding:12px 16px;margin:6px 0;color:#1d4ed8;">
                        ❓ {q}
                    </div>
                    """, unsafe_allow_html=True)

        # ─ Q&A tab ─
        with tabs[5]:
            st.markdown('<div class="section-header">💬 Ask About This Meeting</div>', unsafe_allow_html=True)
            st.markdown("Ask any question about the meeting content:")
            question = st.text_input("Your question", placeholder="Who is responsible for the marketing budget? What did Alice say about the deadline?")
            if st.button("🔍 Ask", type="primary") and question:
                with st.spinner("Searching meeting notes..."):
                    answer = ask_about_meeting(td["text"], question, analysis)
                st.markdown(f"""
                <div class="glass-card">
                    <div style="font-weight:600;color:#4f46e5;margin-bottom:8px;">Answer:</div>
                    <div style="font-size:14px;color:#374151;line-height:1.7;">{answer}</div>
                </div>
                """, unsafe_allow_html=True)

        # ─ Export tab ─
        with tabs[6]:
            st.markdown('<div class="section-header">📥 Export Meeting Notes</div>', unsafe_allow_html=True)
            e1, e2, e3 = st.columns(3)

            with e1:
                st.markdown("""
                <div class="glass-card" style="text-align:center;">
                    <div style="font-size:36px;">📄</div>
                    <div style="font-weight:700;margin:8px 0 4px;">PDF Report</div>
                    <div style="font-size:12px;color:#64748b;">Professional, formatted, printable</div>
                </div>
                """, unsafe_allow_html=True)
                pdf_bytes = export_pdf(analysis, td["text"], st.session_state.follow_up_email or "")
                st.download_button(
                    "⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=f"meeting_{title[:30]}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

            with e2:
                st.markdown("""
                <div class="glass-card" style="text-align:center;">
                    <div style="font-size:36px;">📝</div>
                    <div style="font-weight:700;margin:8px 0 4px;">Word Document</div>
                    <div style="font-size:12px;color:#64748b;">Editable DOCX for Teams/Notion</div>
                </div>
                """, unsafe_allow_html=True)
                docx_bytes = export_docx(analysis, td["text"], st.session_state.follow_up_email or "")
                st.download_button(
                    "⬇️ Download DOCX",
                    data=docx_bytes,
                    file_name=f"meeting_{title[:30]}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )

            with e3:
                st.markdown("""
                <div class="glass-card" style="text-align:center;">
                    <div style="font-size:36px;">🗒️</div>
                    <div style="font-weight:700;margin:8px 0 4px;">Markdown</div>
                    <div style="font-size:12px;color:#64748b;">For Notion, Obsidian, GitHub</div>
                </div>
                """, unsafe_allow_html=True)
                md_text = export_markdown(analysis, td["text"], st.session_state.follow_up_email or "")
                st.download_button(
                    "⬇️ Download Markdown",
                    data=md_text,
                    file_name=f"meeting_{title[:30]}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

            if st.session_state.saved_meeting_id and st.session_state.saved_meeting_id > 0:
                st.success(f"✅ Meeting saved to database (ID: {st.session_state.saved_meeting_id})")
            elif not db_ok():
                st.info("💡 Set up Supabase to save meetings to your history database.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: FOLLOW-UP EMAIL
# ═════════════════════════════════════════════════════════════════════════════
elif page == "✉️ Follow-up Email":
    st.markdown('<h1 style="color:#0f172a;">✉️ Follow-up Email</h1>', unsafe_allow_html=True)

    if not st.session_state.analysis:
        st.warning("⚠️ No meeting analyzed yet. Go to Meeting Analysis first.")
        st.stop()

    analysis = st.session_state.analysis
    email = st.session_state.follow_up_email

    if not email:
        if st.button("✉️ Generate Follow-up Email", type="primary"):
            with st.spinner("Drafting email..."):
                email = generate_follow_up_email(analysis, st.session_state.transcript_data["text"])
            st.session_state.follow_up_email = email
            st.rerun()
    else:
        st.markdown(f"""
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;
                    padding:14px 20px;margin-bottom:20px;">
            <strong>📧 Meeting:</strong> {analysis.get('title','')} &nbsp;·&nbsp;
            <strong>Attendees:</strong> {", ".join(analysis.get('attendees', []))}
        </div>
        """, unsafe_allow_html=True)

        edited_email = st.text_area(
            "Edit your email:",
            value=email,
            height=500,
            label_visibility="collapsed",
        )
        st.session_state.follow_up_email = edited_email

        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            st.download_button(
                "⬇️ Download (.txt)",
                data=edited_email,
                file_name=f"followup_{analysis.get('title','meeting')[:30]}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with ec2:
            if st.button("🔄 Regenerate", use_container_width=True):
                with st.spinner("Regenerating..."):
                    new_email = generate_follow_up_email(analysis, st.session_state.transcript_data["text"])
                st.session_state.follow_up_email = new_email
                st.rerun()
        with ec3:
            st.info(f"📊 {len(edited_email):,} characters")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: SEARCH
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Search Meetings":
    st.markdown('<h1 style="color:#0f172a;">🔍 Search Meetings</h1>', unsafe_allow_html=True)

    if not db_ok():
        st.warning("⚠️ Database not configured. Set SUPABASE_URL and SUPABASE_KEY to enable search.")
        st.stop()

    query = st.text_input("Search meetings by title", placeholder="e.g. Sprint, Q4, Budget, Client")
    if query:
        results = search_meetings(query)
        st.markdown(f"**{len(results)} results** for '{query}'")
        if not results:
            st.info("No meetings found. Try a different search term.")
        for r in results:
            sentiment = r.get("sentiment", "Neutral")
            sc = {"Positive":"#16a34a","Neutral":"#475569","Mixed":"#d97706","Tense":"#dc2626"}.get(sentiment,"#475569")
            dur = format_duration(r.get("duration_secs", 0))
            with st.expander(f"📋 {r['title']} · {r['created_at']}"):
                st.markdown(f"""
                <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px;">
                    <span class="badge badge-info">⏱ {dur}</span>
                    <span class="badge badge-info">📝 {r.get('word_count',0):,} words</span>
                    <span style="background:#f8fafc;color:{sc};border:1px solid #e2e8f0;
                                 padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;">
                        {sentiment}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                if st.button("📂 Load this meeting", key=f"load_{r['id']}"):
                    full = get_meeting_by_id(r["id"])
                    if full:
                        st.session_state.transcript_data = {
                            "text": full.get("transcript",""),
                            "filename": full.get("filename",""),
                            "word_count": full.get("word_count",0),
                            "duration_seconds": full.get("duration_secs",0),
                            "language": "en",
                            "segments": [],
                            "file_size_mb": full.get("file_size_mb",0),
                        }
                        st.session_state.analysis = full.get("analysis", {})
                        st.session_state.follow_up_email = full.get("follow_up_email","")
                        st.session_state.meeting_title = full.get("title","")
                        st.session_state.page = "📋 Meeting Analysis"
                        st.rerun()
    else:
        st.markdown("Enter a search term above to find past meetings.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: ANALYTICS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📊 Analytics":
    import plotly.graph_objects as go
    import plotly.express as px

    st.markdown('<h1 style="color:#0f172a;">📊 Analytics Dashboard</h1>', unsafe_allow_html=True)

    if not db_ok():
        st.warning("⚠️ Database not configured. Set SUPABASE_URL and SUPABASE_KEY to enable analytics.")
        st.stop()

    stats = get_analytics()

    if stats["total_meetings"] == 0:
        st.info("No meetings recorded yet. Upload and analyze your first meeting!")
        st.stop()

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    for col, val, lbl, color in [
        (k1, stats["total_meetings"], "Total Meetings", "#4f46e5"),
        (k2, f"{stats['total_duration_mins']:.0f} min", "Total Time", "#7c3aed"),
        (k3, f"{stats['avg_duration_mins']:.0f} min", "Avg Duration", "#06b6d4"),
        (k4, stats["avg_attendees"], "Avg Attendees", "#10b981"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card" style="border-color:{color};"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    a1, a2 = st.columns(2)

    with a1:
        st.markdown('<div class="section-header">😊 Meeting Sentiment</div>', unsafe_allow_html=True)
        if stats["sentiment_counts"]:
            colors_map = {"Positive":"#16a34a","Neutral":"#64748b","Mixed":"#d97706","Tense":"#dc2626"}
            labels = list(stats["sentiment_counts"].keys())
            values = list(stats["sentiment_counts"].values())
            fig = go.Figure(go.Pie(
                labels=labels, values=values,
                marker_colors=[colors_map.get(l, "#4f46e5") for l in labels],
                hole=0.45,
            ))
            fig.update_layout(margin=dict(l=0,r=0,t=10,b=10), height=280, paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)

    with a2:
        st.markdown('<div class="section-header">⏱️ Meeting Duration Distribution</div>', unsafe_allow_html=True)
        if stats["duration_buckets"]:
            buckets = stats["duration_buckets"]
            fig2 = go.Figure(go.Bar(
                x=list(buckets.keys()), y=list(buckets.values()),
                marker_color="#4f46e5", marker_line_width=0,
            ))
            fig2.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=40,r=20,t=10,b=40), height=280,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9", title="Meetings"),
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Daily activity
    if stats["daily_counts"]:
        st.markdown('<div class="section-header">📈 Meeting Activity Over Time</div>', unsafe_allow_html=True)
        days = sorted(stats["daily_counts"].keys())
        counts = [stats["daily_counts"][d] for d in days]
        fig3 = go.Figure(go.Scatter(
            x=days, y=counts, mode="lines+markers",
            line=dict(color="#4f46e5", width=3),
            marker=dict(size=8, color="#4f46e5"),
            fill="tozeroy", fillcolor="rgba(79,70,229,0.1)",
        ))
        fig3.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40,r=20,t=10,b=40), height=220,
            xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9", title="Meetings"),
        )
        st.plotly_chart(fig3, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: HISTORY
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📁 History":
    st.markdown('<h1 style="color:#0f172a;">📁 Meeting History</h1>', unsafe_allow_html=True)

    if not db_ok():
        st.warning("⚠️ Database not configured. Set SUPABASE_URL and SUPABASE_KEY.")
        st.stop()

    meetings = get_all_meetings(limit=50)

    if not meetings:
        st.info("No meetings saved yet. Upload and analyze your first meeting!")
        st.stop()

    st.markdown(f"**{len(meetings)} meetings** saved")

    # Filter
    sentiments = list(set(r.get("sentiment", "Neutral") for r in meetings))
    filter_sent = st.selectbox("Filter by sentiment", ["All"] + sentiments)
    if filter_sent != "All":
        meetings = [r for r in meetings if r.get("sentiment") == filter_sent]

    for r in meetings:
        sentiment = r.get("sentiment", "Neutral")
        sent_icon = {"Positive":"🟢","Neutral":"⚪","Mixed":"🟡","Tense":"🔴"}.get(sentiment,"⚪")
        dur = format_duration(r.get("duration_secs", 0))

        with st.expander(
            f"{sent_icon} {r['title']} · {r['created_at']} · {dur} · {r.get('word_count',0):,} words"
        ):
            hc1, hc2, hc3 = st.columns(3)
            with hc1:
                if st.button("📂 Load", key=f"hload_{r['id']}", use_container_width=True):
                    full = get_meeting_by_id(r["id"])
                    if full:
                        st.session_state.transcript_data = {
                            "text": full.get("transcript",""),
                            "filename": full.get("filename",""),
                            "word_count": full.get("word_count",0),
                            "duration_seconds": full.get("duration_secs",0),
                            "language": "en",
                            "segments": [],
                            "file_size_mb": full.get("file_size_mb",0),
                        }
                        st.session_state.analysis = full.get("analysis",{})
                        st.session_state.follow_up_email = full.get("follow_up_email","")
                        st.session_state.meeting_title = full.get("title","")
                        st.session_state.page = "📋 Meeting Analysis"
                        st.rerun()
            with hc2:
                full = get_meeting_by_id(r["id"])
                if full:
                    pdf_bytes = export_pdf(
                        full.get("analysis",{}),
                        full.get("transcript",""),
                        full.get("follow_up_email",""),
                    )
                    st.download_button(
                        "📄 PDF",
                        data=pdf_bytes,
                        file_name=f"meeting_{r['id']}.pdf",
                        mime="application/pdf",
                        key=f"hpdf_{r['id']}",
                        use_container_width=True,
                    )
            with hc3:
                if st.button("🗑️ Delete", key=f"hdel_{r['id']}", use_container_width=True):
                    delete_meeting(r["id"])
                    st.rerun()

            st.markdown(f"""
            <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px;">
                <span class="badge badge-info">👥 {r.get('attendee_count',0)} attendees</span>
                <span class="badge badge-info">⏱ {dur}</span>
                <span class="badge badge-info">📝 {r.get('word_count',0):,} words</span>
                <span class="badge badge-info">📁 {r.get('filename','')}</span>
            </div>
            """, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.markdown('<h1 style="color:#0f172a;">⚙️ Settings</h1>', unsafe_allow_html=True)
    st.markdown("Configure your API keys to use the app. Your keys are stored only in your browser session — never saved to any server.")

    # ── API Key status banner ──
    current_key = _get_active_api_key()
    if current_key:
        source = "Your own key (entered below)" if st.session_state.get("user_api_key","").strip() else "Server-configured key"
        st.markdown(f"""
        <div style="background:#f0fdf4;border:2px solid #86efac;border-radius:14px;padding:16px 20px;margin-bottom:20px;">
            <div style="font-weight:700;color:#15803d;font-size:15px;">🟢 API Key Active</div>
            <div style="font-size:13px;color:#166534;margin-top:4px;">Source: {source}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#fef2f2;border:2px solid #fca5a5;border-radius:14px;padding:16px 20px;margin-bottom:20px;">
            <div style="font-weight:700;color:#dc2626;font-size:15px;">🔴 No API Key</div>
            <div style="font-size:13px;color:#991b1b;margin-top:4px;">Enter your OpenAI API key below to get started.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">🔑 OpenAI API Key</div>', unsafe_allow_html=True)

    col_key, col_info = st.columns([3, 2])

    with col_key:
        st.markdown("""
        <div class="glass-card">
            <div style="font-weight:600;color:#0f172a;margin-bottom:4px;">Enter your OpenAI API Key</div>
            <div style="font-size:12px;color:#64748b;margin-bottom:14px;">
                Used for Whisper transcription + GPT-4o analysis.
                Stored only in your browser session — cleared when you close the tab.
            </div>
        </div>
        """, unsafe_allow_html=True)

        entered_key = st.text_input(
            "OpenAI API Key",
            value=st.session_state.get("user_api_key", ""),
            type="password",
            placeholder="sk-proj-... or sk-...",
            label_visibility="collapsed",
        )

        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button("💾 Save API Key", type="primary", use_container_width=True):
                if entered_key.strip().startswith("sk-"):
                    st.session_state.user_api_key = entered_key.strip()
                    os.environ["OPENAI_API_KEY"] = entered_key.strip()
                    st.success("✅ API key saved! You can now use all features.")
                    st.rerun()
                elif entered_key.strip():
                    st.error("❌ Invalid key format. OpenAI keys start with 'sk-'")
                else:
                    st.error("Please enter an API key.")
        with sc2:
            if st.button("🗑️ Clear Key", use_container_width=True):
                st.session_state.user_api_key = ""
                if "OPENAI_API_KEY" in os.environ:
                    del os.environ["OPENAI_API_KEY"]
                st.success("Key cleared.")
                st.rerun()

        st.markdown("""
        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;
                    padding:12px 16px;margin-top:12px;">
            <div style="font-weight:600;color:#92400e;font-size:13px;">🔒 Privacy Note</div>
            <div style="font-size:12px;color:#78350f;margin-top:4px;line-height:1.6;">
                Your API key is stored only in your Streamlit session (browser memory).<br>
                It is never saved to any database or sent to any server other than OpenAI.<br>
                It disappears when you close or refresh the tab.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_info:
        st.markdown("""
        <div class="glass-card">
            <div style="font-weight:600;color:#0f172a;margin-bottom:10px;">📋 How to get your key</div>
            <div style="font-size:13px;color:#374151;line-height:1.9;">
                1. Go to <a href="https://platform.openai.com/api-keys" target="_blank"
                   style="color:#4f46e5;font-weight:600;">platform.openai.com/api-keys</a><br>
                2. Sign in or create an account<br>
                3. Click <strong>+ Create new secret key</strong><br>
                4. Copy the key (starts with <code>sk-</code>)<br>
                5. Paste it in the field on the left<br>
                6. Click <strong>Save API Key</strong>
            </div>
            <div style="margin-top:14px;font-weight:600;color:#0f172a;">💰 Estimated cost</div>
            <div style="font-size:12px;color:#64748b;margin-top:6px;line-height:1.7;">
                Whisper: ~$0.006 / minute of audio<br>
                GPT-4o analysis: ~$0.02–0.05 per meeting<br>
                <strong>A 1-hour meeting ≈ $0.40–0.55 total</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Optional Supabase ──
    st.markdown('<div class="section-header">🗄️ Supabase Database (Optional)</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="glass-card">
        <div style="font-size:13px;color:#374151;line-height:1.8;">
            Supabase enables <strong>meeting history</strong>, <strong>search</strong>, and <strong>analytics</strong>.
            Without it, all other features work perfectly — data just isn't saved between sessions.<br><br>
            To enable: run <code>supabase_schema.sql</code> in your Supabase SQL Editor,
            then set <code>SUPABASE_URL</code> and <code>SUPABASE_KEY</code> in Streamlit Cloud
            → App → Settings → Secrets.
        </div>
        <div style="margin-top:12px;">
    """, unsafe_allow_html=True)
    db_status = "🟢 Connected" if db_ok() else "🔴 Not configured"
    st.markdown(f"**Database status:** {db_status}")
    st.markdown("</div></div>", unsafe_allow_html=True)

    # ── Quick start ──
    if current_key:
        st.markdown('<div class="section-header">🚀 Ready to Go!</div>', unsafe_allow_html=True)
        if st.button("→ Go to Upload & Transcribe", type="primary"):
            st.session_state.page = "🎙️ Upload & Transcribe"
            st.rerun()