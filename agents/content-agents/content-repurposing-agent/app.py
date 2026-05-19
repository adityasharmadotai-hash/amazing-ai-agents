"""
app.py — AI Content Repurposing Agent
Streamlit application entry point
"""

import json
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Content Repurposing Agent",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Sidebar background ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0d1a 0%, #1a1a2e 60%, #16213e 100%) !important;
}
[data-testid="stSidebar"] > div:first-child {
    background: transparent !important;
}

/* Hide ALL default radio widget chrome inside sidebar */
[data-testid="stSidebar"] .stRadio { display: none !important; }

/* ── Force ALL sidebar text white ── */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div { color: #e2e8f0 !important; }

/* ── Sidebar st.button → styled as nav items ── */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 11px 16px !important;
    text-align: left !important;
    width: 100% !important;
    margin: 2px 0 !important;
    transition: all 0.18s ease !important;
    box-shadow: none !important;
}
/* Inner text element Streamlit renders inside button */
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span,
[data-testid="stSidebar"] .stButton > button div {
    color: #e2e8f0 !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(99,102,241,0.28) !important;
    border-color: rgba(99,102,241,0.55) !important;
    color: #ffffff !important;
    transform: none !important;
    box-shadow: 0 2px 10px rgba(99,102,241,0.2) !important;
}
[data-testid="stSidebar"] .stButton > button:hover p,
[data-testid="stSidebar"] .stButton > button:hover span {
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stButton > button:active {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border-color: transparent !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(99,102,241,0.4) !important;
}

/* Divider */
.nav-divider {
    height: 1px;
    background: rgba(255,255,255,0.08);
    margin: 12px 0;
}

/* Cards */
.glass-card {
    background: rgba(255,255,255,0.95);
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 16px; padding: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    margin-bottom: 16px;
}
.metric-card {
    background: white; border-radius: 14px; padding: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    border-left: 4px solid #6366f1; text-align: center;
}
.metric-card .val { font-size: 32px; font-weight: 800; color: #0f172a; }
.metric-card .lbl { font-size: 12px; color: #64748b; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }

/* Content output boxes */
.content-box {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 20px;
    font-size: 14px; line-height: 1.7;
    white-space: pre-wrap; font-family: 'Inter', sans-serif;
    max-height: 400px; overflow-y: auto;
}
.content-box-full {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 20px;
    font-size: 14px; line-height: 1.7;
    white-space: pre-wrap; font-family: 'Inter', sans-serif;
}

/* Style pills */
.style-pill {
    display: inline-block; padding: 4px 14px;
    border-radius: 20px; font-size: 12px; font-weight: 600;
    margin: 2px;
}
.pill-viral   { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.pill-edu     { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.pill-founder { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
.pill-tech    { background: #faf5ff; color: #7c3aed; border: 1px solid #ddd6fe; }

/* Section headers */
.section-header {
    background: linear-gradient(90deg, #6366f1, #8b5cf6);
    color: white; border-radius: 12px; padding: 14px 20px;
    margin: 20px 0 16px; font-size: 16px; font-weight: 600;
}

/* Content type tabs */
.ct-badge {
    display: inline-block; padding: 6px 16px;
    background: #f1f5f9; border-radius: 20px;
    font-size: 13px; font-weight: 600; color: #475569;
    margin: 4px;
}

/* Transcript viewer */
.transcript-box {
    background: #0f172a; color: #94a3b8;
    border-radius: 12px; padding: 20px;
    font-family: 'Courier New', monospace;
    font-size: 13px; line-height: 1.8;
    max-height: 400px; overflow-y: auto;
    white-space: pre-wrap;
}

/* ── Content text areas (clean output display) ── */
[data-testid="stTextArea"] textarea {
    background: #0f172a !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    line-height: 1.75 !important;
    border: 1px solid #1e293b !important;
    border-radius: 10px !important;
    padding: 16px !important;
    resize: vertical !important;
}
[data-testid="stTextArea"] textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.15) !important;
}

/* URL input */
[data-testid="stTextInput"] input {
    border-radius: 10px; border: 2px solid #e2e8f0;
    font-size: 15px; padding: 12px 16px;
    transition: border-color 0.2s;
}
[data-testid="stTextInput"] input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
}

/* Buttons */
.stButton button {
    border-radius: 10px; font-weight: 600;
    transition: all 0.2s;
}
.stButton button:hover { transform: translateY(-1px); }

/* Progress bar */
.stProgress > div > div { border-radius: 8px; background: #6366f1; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #f1f5f9; border-radius: 12px; padding: 4px; gap: 2px;
}
.stTabs [data-baseweb="tab"] { border-radius: 9px; font-weight: 500; }
.stTabs [aria-selected="true"] {
    background: white !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}

/* Hide branding */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Imports ───────────────────────────────────────────────────────────────────
from modules.agent import is_configured as agent_ok, generate_content, generate_all_content, generate_title_and_summary
from modules.database import init_db, is_configured as db_ok, save_content, get_all_history, get_content_by_id, get_analytics, delete_content
from modules.transcript import get_transcript, get_video_metadata, chunk_transcript
from modules.prompts import WRITING_STYLES, CONTENT_PROMPTS, DEFAULT_CUSTOM_PROMPTS, get_all_content_types

init_db()

# ── Session state ─────────────────────────────────────────────────────────────
def _ss(key, default=None):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]

_ss("transcript_data", None)
_ss("generated_content", {})
_ss("current_style", "Educational")
_ss("page", "🏠 Home")
_ss("custom_prompts", {})
_ss("video_meta", {})

# ── Credential check ──────────────────────────────────────────────────────────
def _check_credentials():
    if not agent_ok():
        st.markdown("""
        <div style="background:#fef2f2;border:2px solid #fecaca;border-radius:16px;
                    padding:32px;max-width:600px;margin:60px auto;text-align:center;">
            <div style="font-size:48px;">🔑</div>
            <h2 style="color:#dc2626;margin:12px 0 8px;">API Key Required</h2>
            <p style="color:#7f1d1d;margin-bottom:20px;">
                Set your <strong>OPENAI_API_KEY</strong> to use this app.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.code('OPENAI_API_KEY = "sk-your-openai-key-here"', language="toml")
        st.caption("Add this to Streamlit Cloud → App → Settings → Secrets, or to your local .env file")
        st.stop()

_check_credentials()

# ── Sidebar ───────────────────────────────────────────────────────────────────
NAV_PAGES = [
    ("🏠", "Home"), ("📄", "Transcript"), ("✨", "Generate"),
    ("📋", "All Content"), ("📁", "History"), ("📊", "Analytics"), ("⚙️", "Prompts"),
]

with st.sidebar:

    # Branding
    st.markdown("""
    <div style="padding:24px 4px 18px;text-align:center;">
        <div style="font-size:52px;line-height:1;">🎬</div>
        <div style="font-size:17px;font-weight:800;color:white;margin-top:10px;
                    letter-spacing:-0.2px;">Content Repurposer</div>
        <div style="font-size:11px;color:#475569;margin-top:5px;font-weight:500;">
            ✦ Powered by OpenAI GPT-4o
        </div>
    </div>
    <div class="nav-divider"></div>
    <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:0.1em;
                font-weight:600;padding:0 4px;margin-bottom:6px;">Navigation</div>
    """, unsafe_allow_html=True)

    # Nav buttons
    for icon, label in NAV_PAGES:
        full_page = f"{icon} {label}"
        if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
            st.session_state.page = full_page
            st.rerun()

    page = st.session_state.get("page", "🏠 Home")

    # Active video card + style selector
    if st.session_state.transcript_data:
        td = st.session_state.transcript_data
        meta = st.session_state.video_meta
        title = meta.get("title", "Video loaded")[:36]
        dur = td.get("duration_minutes", 0)
        wc = td.get("word_count", 0)
        st.markdown(f"""
        <div class="nav-divider"></div>
        <div style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.3);
                    border-radius:10px;padding:11px 13px;margin:4px 0 10px;">
            <div style="font-size:10px;color:#818cf8;text-transform:uppercase;
                        letter-spacing:0.08em;font-weight:600;">▶ Active Video</div>
            <div style="font-size:12px;font-weight:600;color:white;margin-top:5px;
                        line-height:1.35;">{title}</div>
            <div style="font-size:11px;color:#475569;margin-top:5px;">
                ⏱ {dur} min &nbsp;·&nbsp; 📝 {wc:,} words
            </div>
        </div>
        <div class="nav-divider"></div>
        <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:0.1em;
                    font-weight:600;padding:0 4px;margin-bottom:6px;">Writing Style</div>
        """, unsafe_allow_html=True)

        for style_name, style_data in WRITING_STYLES.items():
            is_sel = (st.session_state.current_style == style_name)
            lbl = f"✓  {style_data['icon']}  {style_name}" if is_sel else f"{style_data['icon']}  {style_name}"
            if st.button(lbl, key=f"style_{style_name}", use_container_width=True):
                if style_name != st.session_state.current_style:
                    st.session_state.current_style = style_name
                    st.session_state.generated_content = {}
                    st.rerun()

    st.markdown("""
    <div class="nav-divider"></div>
    <div style="font-size:11px;color:#334155;text-align:center;padding:2px 0 8px;">
        Built with ❤️ by <a href="https://www.adityasharma.ai" target="_blank" style="color:#818cf8;">Aditya Sharma</a>
    </div>
    """, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: HOME
# ═════════════════════════════════════════════════════════════════════════════
if page == "🏠 Home":
    st.markdown("""
    <div style="padding:8px 0 32px;">
        <h1 style="font-size:36px;font-weight:800;color:#0f172a;margin:0;">
            🎬 AI Content Repurposing Agent
        </h1>
        <p style="color:#64748b;font-size:17px;margin-top:8px;">
            Paste a YouTube URL → get LinkedIn posts, Twitter threads, Instagram captions,
            viral hooks, carousel slides, and blog summaries — in seconds.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # URL Input
    st.markdown('<div class="section-header">🔗 YouTube URL</div>', unsafe_allow_html=True)
    col_url, col_btn = st.columns([5, 1])
    with col_url:
        yt_url = st.text_input(
            "url",
            placeholder="https://www.youtube.com/watch?v=...",
            label_visibility="collapsed",
            key="yt_url_input",
        )
    with col_btn:
        extract_btn = st.button("Extract ▶", type="primary", use_container_width=True)

    if extract_btn and yt_url:
        with st.spinner("🔍 Fetching transcript..."):
            result = get_transcript(yt_url)

        if "error" in result:
            st.error(f"❌ {result['error']}")
        else:
            st.session_state.transcript_data = result
            st.session_state.generated_content = {}

            # Get metadata
            with st.spinner("📺 Fetching video info..."):
                meta = get_video_metadata(result["video_id"])
            st.session_state.video_meta = meta

            st.success(f"✅ Transcript extracted! {result['word_count']:,} words · {result['duration_minutes']} minutes")
            st.rerun()

    # Feature overview
    if not st.session_state.transcript_data:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">🚀 What This Agent Does</div>', unsafe_allow_html=True)
        f1, f2, f3 = st.columns(3)
        for col, icon, title, desc in [
            (f1, "🔗", "1. Paste YouTube URL", "Any public YouTube video with English captions"),
            (f2, "✨", "2. Generate Content", "6 content formats × 4 writing styles = 24 variations"),
            (f3, "📋", "3. Copy & Export", "One-click copy for each piece of content"),
        ]:
            with col:
                st.markdown(f"""
                <div class="glass-card" style="text-align:center;padding:28px 20px;">
                    <div style="font-size:36px;">{icon}</div>
                    <div style="font-weight:700;color:#0f172a;margin:12px 0 8px;">{title}</div>
                    <div style="font-size:13px;color:#64748b;line-height:1.5;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">📦 Content Formats</div>', unsafe_allow_html=True)
        all_ct = get_all_content_types()
        cols = st.columns(4)
        for i, (ct_key, ct_data) in enumerate(all_ct.items()):
            with cols[i % 4]:
                st.markdown(f"""
                <div class="glass-card" style="text-align:center;padding:16px;">
                    <div style="font-size:28px;">{ct_data['icon']}</div>
                    <div style="font-weight:600;font-size:13px;color:#0f172a;margin-top:8px;">{ct_data['label']}</div>
                    <div style="font-size:11px;color:#94a3b8;margin-top:4px;">{ct_data.get('description','')[:40]}</div>
                </div>
                """, unsafe_allow_html=True)

    else:
        # Video loaded — show summary
        td = st.session_state.transcript_data
        meta = st.session_state.video_meta

        st.markdown('<div class="section-header">📺 Video Loaded</div>', unsafe_allow_html=True)
        vc1, vc2, vc3, vc4 = st.columns(4)
        for col, val, lbl in [
            (vc1, f"{td.get('duration_minutes',0)} min", "Duration"),
            (vc2, f"{td.get('word_count',0):,}", "Words"),
            (vc3, meta.get("channel", "—"), "Channel"),
            (vc4, f"{len(st.session_state.generated_content)}", "Generated"),
        ]:
            with col:
                st.markdown(f'<div class="metric-card"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-weight:700;font-size:16px;color:#0f172a;margin-bottom:8px;">
                📺 {meta.get('title','Video')}
            </div>
            <div style="font-size:13px;color:#64748b;">{meta.get('description','')[:300]}</div>
            <div style="margin-top:12px;">
                <a href="{td.get('url','')}" target="_blank" style="color:#6366f1;font-weight:600;text-decoration:none;">
                    ▶ Watch on YouTube →
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**→ Go to ✨ Generate to create content**")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: TRANSCRIPT
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📄 Transcript":
    st.markdown('<h1 style="color:#0f172a;">📄 Transcript Viewer</h1>', unsafe_allow_html=True)

    if not st.session_state.transcript_data:
        st.info("No transcript loaded yet. Go to 🏠 Home and paste a YouTube URL.")
        st.stop()

    td = st.session_state.transcript_data

    t1, t2 = st.tabs(["📝 Full Transcript", "⏱️ Segments"])

    with t1:
        st.markdown(f"""
        <div style="display:flex;gap:16px;margin-bottom:16px;">
            <span style="background:#eff6ff;color:#2563eb;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;">
                📊 {td.get('word_count',0):,} words
            </span>
            <span style="background:#f0fdf4;color:#16a34a;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;">
                ⏱️ {td.get('duration_minutes',0)} minutes
            </span>
            <span style="background:#faf5ff;color:#7c3aed;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;">
                🔤 {len(td.get('transcript',''))} characters
            </span>
        </div>
        """, unsafe_allow_html=True)

        transcript_text = td.get("transcript", "")
        st.markdown(f'<div class="transcript-box">{transcript_text}</div>', unsafe_allow_html=True)

        st.download_button(
            "⬇️ Download Transcript (.txt)",
            data=transcript_text,
            file_name=f"transcript_{td.get('video_id','video')}.txt",
            mime="text/plain",
        )

    with t2:
        segments = td.get("segments", [])
        if segments:
            st.markdown(f"**{len(segments)} segments**")
            # Show first 50 segments
            for seg in segments[:50]:
                mins = int(seg["start"] // 60)
                secs = int(seg["start"] % 60)
                st.markdown(
                    f'<div style="display:flex;gap:12px;padding:6px 0;border-bottom:1px solid #f1f5f9;">'
                    f'<span style="color:#6366f1;font-weight:600;min-width:50px;font-family:monospace;">'
                    f'{mins:02d}:{secs:02d}</span>'
                    f'<span style="color:#374151;font-size:13px;">{seg["text"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            if len(segments) > 50:
                st.caption(f"... and {len(segments) - 50} more segments")
        else:
            st.info("No segment data available.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: GENERATE
# ═════════════════════════════════════════════════════════════════════════════
elif page == "✨ Generate":
    st.markdown('<h1 style="color:#0f172a;">✨ Generate Content</h1>', unsafe_allow_html=True)

    if not st.session_state.transcript_data:
        st.info("No transcript loaded yet. Go to 🏠 Home and paste a YouTube URL.")
        st.stop()

    td = st.session_state.transcript_data
    style = st.session_state.current_style
    transcript_chunk = chunk_transcript(td["transcript"])

    style_data = WRITING_STYLES[style]
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;
                border-radius:12px;padding:16px 20px;margin-bottom:20px;">
        <strong>{style_data['icon']} {style} Style</strong> — {style_data['description']}
        <div style="font-size:12px;opacity:0.8;margin-top:4px;">Change style in the sidebar</div>
    </div>
    """, unsafe_allow_html=True)

    # Generate all button
    gc1, gc2 = st.columns([2, 1])
    with gc1:
        if st.button("⚡ Generate ALL Content", type="primary", use_container_width=True):
            progress = st.progress(0)
            status = st.empty()
            all_types = list(CONTENT_PROMPTS.keys())
            for i, ct in enumerate(all_types):
                status.markdown(f"Generating **{CONTENT_PROMPTS[ct]['label']}**...")
                result = generate_content(ct, transcript_chunk, style)
                st.session_state.generated_content[ct] = result
                progress.progress((i + 1) / len(all_types))

                # Auto-save to DB
                if db_ok() and not result.startswith("Error:"):
                    meta_info = generate_title_and_summary(transcript_chunk) if i == 0 else st.session_state.get("_last_meta", {"title": "Video", "summary": ""})
                    if i == 0:
                        st.session_state["_last_meta"] = meta_info
                    save_content(
                        td["video_id"], td["url"],
                        meta_info.get("title", "Video"),
                        meta_info.get("summary", ""),
                        td["transcript"],
                        td.get("duration_minutes", 0),
                        td.get("word_count", 0),
                        style, ct, result,
                    )

            progress.empty()
            status.empty()
            st.success("✅ All content generated!")
            st.rerun()

    with gc2:
        st.button("🗑️ Clear All", on_click=lambda: st.session_state.update({"generated_content": {}}), use_container_width=True)

    st.markdown("---")

    # Individual content type cards
    all_types = list(CONTENT_PROMPTS.keys())
    for ct_key in all_types:
        ct_data = CONTENT_PROMPTS[ct_key]
        icon = ct_data["icon"]
        label = ct_data["label"]
        generated = st.session_state.generated_content.get(ct_key, "")

        with st.expander(f"{icon} {label}", expanded=bool(generated)):
            if generated and not generated.startswith("Error:"):
                # Use st.text_area for clean plain-text display — no markdown rendering
                st.text_area(
                    label="content",
                    value=generated,
                    height=300,
                    key=f"ta_{ct_key}",
                    label_visibility="collapsed",
                )
                bc1, bc2, bc3 = st.columns(3)
                with bc1:
                    st.download_button(
                        "⬇️ Download",
                        data=generated,
                        file_name=f"{ct_key}_{style.lower()}.txt",
                        mime="text/plain",
                        key=f"dl_{ct_key}",
                        use_container_width=True,
                    )
                with bc2:
                    st.caption(f"📊 {len(generated):,} chars")
                with bc3:
                    if st.button("🔄 Regenerate", key=f"regen_{ct_key}", use_container_width=True):
                        with st.spinner(f"Regenerating {label}..."):
                            new_content = generate_content(ct_key, transcript_chunk, style)
                        st.session_state.generated_content[ct_key] = new_content
                        st.rerun()
            elif generated.startswith("Error:"):
                st.error(generated)
                if st.button("🔄 Retry", key=f"retry_{ct_key}"):
                    with st.spinner("Retrying..."):
                        new_content = generate_content(ct_key, transcript_chunk, style)
                    st.session_state.generated_content[ct_key] = new_content
                    st.rerun()
            else:
                col_gen, _ = st.columns([1, 2])
                with col_gen:
                    if st.button(f"Generate {label}", key=f"gen_{ct_key}", type="primary", use_container_width=True):
                        with st.spinner(f"✨ Generating {label}..."):
                            result = generate_content(ct_key, transcript_chunk, style)
                        st.session_state.generated_content[ct_key] = result

                        if db_ok() and not result.startswith("Error:"):
                            meta_info = generate_title_and_summary(transcript_chunk)
                            save_content(
                                td["video_id"], td["url"],
                                meta_info.get("title", "Video"),
                                meta_info.get("summary", ""),
                                td["transcript"],
                                td.get("duration_minutes", 0),
                                td.get("word_count", 0),
                                style, ct_key, result,
                            )
                        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: ALL CONTENT
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📋 All Content":
    st.markdown('<h1 style="color:#0f172a;">📋 All Generated Content</h1>', unsafe_allow_html=True)

    if not st.session_state.generated_content:
        st.info("No content generated yet. Go to ✨ Generate to create content.")
        st.stop()

    style = st.session_state.current_style
    td = st.session_state.transcript_data or {}

    # Export all button
    if st.session_state.generated_content:
        all_text = f"=== AI Content Repurposing Agent ===\n"
        all_text += f"Video: {td.get('url','')}\n"
        all_text += f"Style: {style}\n"
        all_text += "=" * 50 + "\n\n"
        for ct_key, content in st.session_state.generated_content.items():
            ct_data = CONTENT_PROMPTS.get(ct_key, {})
            all_text += f"{'=' * 40}\n{ct_data.get('icon','')} {ct_data.get('label', ct_key).upper()}\n{'=' * 40}\n\n{content}\n\n"

        st.download_button(
            "⬇️ Export All Content (.txt)",
            data=all_text,
            file_name=f"all_content_{style.lower()}.txt",
            mime="text/plain",
            type="primary",
        )

    st.markdown("---")

    for ct_key, content in st.session_state.generated_content.items():
        if content.startswith("Error:"):
            continue
        ct_data = CONTENT_PROMPTS.get(ct_key, DEFAULT_CUSTOM_PROMPTS.get(ct_key, {}))
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;margin:20px 0 10px;">
            <span style="font-size:24px;">{ct_data.get('icon','📄')}</span>
            <span style="font-size:18px;font-weight:700;color:#0f172a;">{ct_data.get('label', ct_key)}</span>
            <span style="background:#eff6ff;color:#2563eb;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600;">{style}</span>
        </div>
        """, unsafe_allow_html=True)
        st.text_area(
            label="content_full",
            value=content,
            height=350,
            key=f"allpage_ta_{ct_key}",
            label_visibility="collapsed",
        )
        st.download_button(
            f"⬇️ Download",
            data=content,
            file_name=f"{ct_key}_{style.lower()}.txt",
            mime="text/plain",
            key=f"allpage_dl_{ct_key}",
        )
        st.markdown("---")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: HISTORY
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📁 History":
    st.markdown('<h1 style="color:#0f172a;">📁 Content History</h1>', unsafe_allow_html=True)

    if not db_ok():
        st.warning("⚠️ Database not configured. Set SUPABASE_URL and SUPABASE_KEY to enable history.")
        st.code("""
OPENAI_API_KEY = "sk-your-openai-key..."
SUPABASE_URL      = "https://xxxx.supabase.co"
SUPABASE_KEY      = "your-anon-key"
""", language="toml")
        st.stop()

    history = get_all_history(limit=50)

    if not history:
        st.info("No content history yet. Generate some content first!")
        st.stop()

    st.markdown(f"**{len(history)} pieces of content generated**")

    # Filter
    fc1, fc2 = st.columns(2)
    with fc1:
        filter_style = st.selectbox("Filter by style", ["All"] + list(WRITING_STYLES.keys()))
    with fc2:
        filter_ct = st.selectbox("Filter by type", ["All"] + [v["label"] for v in CONTENT_PROMPTS.values()])

    filtered = history
    if filter_style != "All":
        filtered = [r for r in filtered if r.get("style") == filter_style]
    if filter_ct != "All":
        ct_key_map = {v["label"]: k for k, v in CONTENT_PROMPTS.items()}
        target_key = ct_key_map.get(filter_ct, filter_ct)
        filtered = [r for r in filtered if r.get("content_type") == target_key]

    st.markdown(f"Showing **{len(filtered)}** items")
    st.markdown("---")

    for row in filtered:
        ct_key = row.get("content_type", "")
        ct_data = CONTENT_PROMPTS.get(ct_key, DEFAULT_CUSTOM_PROMPTS.get(ct_key, {}))
        icon = ct_data.get("icon", "📄")
        label = ct_data.get("label", ct_key)
        style_name = row.get("style", "")

        with st.expander(
            f"{icon} {label} · {style_name} · {row.get('video_title','')[:40]} · {row.get('created_at','')}",
        ):
            st.markdown(f"""
            <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;">
                <span class="ct-badge">{icon} {label}</span>
                <span class="ct-badge">🎨 {style_name}</span>
                <span class="ct-badge">📊 {row.get('char_count',0):,} chars</span>
                <span class="ct-badge">🕐 {row.get('created_at','')}</span>
            </div>
            """, unsafe_allow_html=True)

            full = get_content_by_id(row["id"])
            if full:
                st.text_area(
                    label="hist_content",
                    value=full.get("generated_text", ""),
                    height=280,
                    key=f"hist_ta_{row['id']}",
                    label_visibility="collapsed",
                )
                hc1, hc2 = st.columns(2)
                with hc1:
                    st.download_button(
                        "⬇️ Download",
                        data=full.get("generated_text", ""),
                        file_name=f"{ct_key}_{style_name}.txt",
                        mime="text/plain",
                        key=f"hist_dl_{row['id']}",
                        use_container_width=True,
                    )
                with hc2:
                    if st.button("🗑️ Delete", key=f"hist_del_{row['id']}", use_container_width=True):
                        delete_content(row["id"])
                        st.rerun()


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

    if stats["total_pieces"] == 0:
        st.info("No data yet. Generate some content to see analytics!")
        st.stop()

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    for col, val, lbl, color in [
        (k1, stats["total_pieces"], "Content Pieces", "#6366f1"),
        (k2, stats["unique_videos"], "Videos Processed", "#8b5cf6"),
        (k3, f"{stats['total_chars']:,}", "Total Characters", "#06b6d4"),
        (k4, f"{stats['total_chars'] // max(stats['total_pieces'],1):,}", "Avg Chars/Piece", "#10b981"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card" style="border-color:{color};"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    a1, a2 = st.columns(2)

    with a1:
        st.markdown('<div class="section-header">📦 Content by Type</div>', unsafe_allow_html=True)
        ct_labels = []
        ct_values = []
        for ct_key, count in stats["content_type_counts"].items():
            ct_data = CONTENT_PROMPTS.get(ct_key, {})
            ct_labels.append(f"{ct_data.get('icon','')} {ct_data.get('label', ct_key)}")
            ct_values.append(count)

        if ct_labels:
            fig = go.Figure(go.Bar(
                x=ct_values, y=ct_labels, orientation="h",
                marker_color="#6366f1", marker_line_width=0,
            ))
            fig.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=0,r=20,t=10,b=20), height=280,
                xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                yaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig, use_container_width=True)

    with a2:
        st.markdown('<div class="section-header">🎨 Content by Style</div>', unsafe_allow_html=True)
        if stats["style_counts"]:
            style_labels = [f"{WRITING_STYLES.get(k,{}).get('icon','')} {k}" for k in stats["style_counts"]]
            style_values = list(stats["style_counts"].values())
            colors = ["#6366f1","#8b5cf6","#06b6d4","#10b981"]
            fig2 = go.Figure(go.Pie(
                labels=style_labels, values=style_values,
                marker_colors=colors[:len(style_labels)],
                hole=0.4,
            ))
            fig2.update_layout(
                margin=dict(l=0,r=0,t=10,b=10), height=280,
                paper_bgcolor="white",
                showlegend=True,
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Daily activity
    if stats["daily_counts"]:
        st.markdown('<div class="section-header">📈 Daily Activity</div>', unsafe_allow_html=True)
        days = sorted(stats["daily_counts"].keys())
        counts = [stats["daily_counts"][d] for d in days]
        fig3 = go.Figure(go.Scatter(
            x=days, y=counts, mode="lines+markers",
            line=dict(color="#6366f1", width=3),
            marker=dict(size=8, color="#6366f1"),
            fill="tozeroy", fillcolor="rgba(99,102,241,0.1)",
        ))
        fig3.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40,r=20,t=10,b=40), height=220,
            xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9", title="Pieces"),
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Top videos
    if stats["top_videos"]:
        st.markdown('<div class="section-header">🏆 Top Videos</div>', unsafe_allow_html=True)
        for i, (title, count) in enumerate(stats["top_videos"], 1):
            pct = count / stats["total_pieces"] * 100
            st.markdown(f"""
            <div class="glass-card" style="padding:14px 20px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-weight:700;color:#6366f1;">#{i}</span>
                        <span style="font-weight:600;color:#0f172a;margin-left:10px;">{title[:60]}</span>
                    </div>
                    <span style="background:#eff6ff;color:#4338ca;padding:4px 12px;border-radius:20px;font-weight:700;">
                        {count} pieces
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: PROMPTS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Prompts":
    st.markdown('<h1 style="color:#0f172a;">⚙️ Prompt Manager</h1>', unsafe_allow_html=True)
    st.markdown("View, edit, and test all prompts. Custom prompts are saved for your session.")

    t1, t2, t3 = st.tabs(["📋 Built-in Prompts", "✏️ Custom Prompt", "🎨 Writing Styles"])

    with t1:
        st.markdown('<div class="section-header">📋 Built-in Prompt Templates</div>', unsafe_allow_html=True)
        for ct_key, ct_data in CONTENT_PROMPTS.items():
            with st.expander(f"{ct_data['icon']} {ct_data['label']}"):
                st.markdown("**System Prompt:**")
                st.code(ct_data["system"], language=None)
                st.markdown("**User Prompt Template:**")
                st.code(ct_data["user"], language=None)
                st.caption("Use {transcript} and {style_instruction} as placeholders in custom prompts.")

    with t2:
        st.markdown('<div class="section-header">✏️ Create Custom Prompt</div>', unsafe_allow_html=True)
        st.markdown("Create a custom content type. It will appear in the Generate page.")

        cp_label = st.text_input("Content Type Name", placeholder="e.g. Podcast Script")
        cp_icon = st.text_input("Icon (emoji)", placeholder="🎙️", max_chars=4)
        cp_system = st.text_area(
            "System Prompt",
            value="You are an expert content creator.",
            height=100,
        )
        cp_user = st.text_area(
            "User Prompt Template",
            value="Based on this transcript, create content.\n\nSTYLE: {style_instruction}\n\nTRANSCRIPT:\n{transcript}",
            height=200,
        )

        if st.button("💾 Save Custom Prompt", type="primary"):
            if cp_label and cp_system and cp_user:
                key = cp_label.lower().replace(" ", "_")
                st.session_state.custom_prompts[key] = {
                    "label": cp_label,
                    "icon": cp_icon or "📄",
                    "system": cp_system,
                    "user": cp_user,
                }
                st.success(f"✅ Saved '{cp_label}' — it will appear in the Generate page!")
            else:
                st.error("Fill in all fields.")

        if st.session_state.custom_prompts:
            st.markdown("**Your Custom Prompts:**")
            for k, v in st.session_state.custom_prompts.items():
                sc1, sc2 = st.columns([4, 1])
                with sc1:
                    st.markdown(f"- {v['icon']} **{v['label']}**")
                with sc2:
                    if st.button("🗑️", key=f"del_custom_{k}"):
                        del st.session_state.custom_prompts[k]
                        st.rerun()

        # Test custom prompt
        if st.session_state.transcript_data and st.session_state.custom_prompts:
            st.markdown("---")
            st.markdown("**Test a Custom Prompt:**")
            test_key = st.selectbox("Select prompt to test", list(st.session_state.custom_prompts.keys()))
            test_style = st.selectbox("Style", list(WRITING_STYLES.keys()))
            if st.button("▶ Test Prompt", type="primary"):
                p = st.session_state.custom_prompts[test_key]
                td = st.session_state.transcript_data
                style_instr = WRITING_STYLES[test_style]["instruction"]
                user_prompt = p["user"].format(
                    style_instruction=style_instr,
                    transcript=chunk_transcript(td["transcript"])
                )
                with st.spinner("Generating..."):
                    result = generate_content(
                        test_key, chunk_transcript(td["transcript"]), test_style,
                        custom_system=p["system"], custom_user=user_prompt
                    )
                st.text_area(
                    label="prompt_test_result",
                    value=result,
                    height=350,
                    label_visibility="collapsed",
                )

    with t3:
        st.markdown('<div class="section-header">🎨 Writing Style Definitions</div>', unsafe_allow_html=True)
        for style_name, style_data in WRITING_STYLES.items():
            st.markdown(f"""
            <div class="glass-card">
                <div style="font-size:24px;margin-bottom:8px;">{style_data['icon']}</div>
                <div style="font-weight:700;font-size:16px;color:#0f172a;">{style_name}</div>
                <div style="color:#64748b;margin:4px 0 12px;">{style_data['description']}</div>
                <div style="background:#f8fafc;border-radius:8px;padding:12px;font-size:13px;color:#374151;font-family:monospace;">
                    {style_data['instruction']}
                </div>
            </div>
            """, unsafe_allow_html=True)