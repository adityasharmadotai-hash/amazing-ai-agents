"""
app.py — Personal Email Assistant Agent
=========================================
Run: streamlit run app.py
"""
from __future__ import annotations
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Email Assistant",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from modules import database, agent
from modules.demo_data import get_demo_emails, get_demo_contacts, get_demo_events

database.init_db()

# ═══════════════════════════════════════════════════════════════════════════════
#  Global CSS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background: #0A0A14 !important; color: #E2E8F0;
}
[data-testid="stSidebar"] {
    background: #0E0E1C !important;
    border-right: 1px solid #1E1E3A;
}

/* ── Metric card ── */
.mc {
    background: linear-gradient(135deg, #12122A 0%, #0E1628 100%);
    border: 1px solid #1E1E3A; border-radius: 14px;
    padding: 18px 20px; text-align: center;
}
.mc-val { font-size: 2.2rem; font-weight: 800; color: #6366F1; line-height: 1; }
.mc-lbl { font-size: 0.72rem; color: #64748B; text-transform: uppercase;
          letter-spacing: 0.06em; margin-top: 3px; }
.mc-sub { font-size: 0.82rem; color: #818CF8; margin-top: 2px; }

/* ── Section header ── */
.sh {
    font-size: 1.05rem; font-weight: 700; color: #E2E8F0;
    margin: 22px 0 10px; display: flex; align-items: center; gap: 8px;
}
.sh::after { content: ''; flex: 1; height: 1px;
             background: linear-gradient(to right, #6366F133, transparent); margin-left: 10px; }

/* ── Email row card ── */
.email-row {
    background: #12122A; border: 1px solid #1E1E3A;
    border-left: 3px solid #1E1E3A; border-radius: 10px;
    padding: 12px 16px; margin-bottom: 6px; cursor: pointer;
    transition: border-color 0.15s, background 0.15s;
}
.email-row:hover { background: #16163A; border-left-color: #6366F1; }
.email-row.unread { border-left-color: #6366F1; background: #14143A; }
.email-row.critical { border-left-color: #EF4444; }
.email-row.high { border-left-color: #F59E0B; }
.email-row.medium { border-left-color: #3B82F6; }
.email-row.low { border-left-color: #10B981; }
.email-subject { font-size: 0.92rem; font-weight: 600; color: #E2E8F0; }
.email-from { font-size: 0.78rem; color: #6366F1; }
.email-snippet { font-size: 0.8rem; color: #64748B; margin-top: 3px;
                 white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.email-date { font-size: 0.72rem; color: #374151; }

/* ── Email viewer ── */
.email-viewer {
    background: #12122A; border: 1px solid #1E1E3A; border-radius: 14px;
    padding: 24px; height: 100%;
}
.email-header-block {
    background: #0E0E1C; border-radius: 10px; padding: 14px 16px; margin-bottom: 16px;
}
.email-body-text {
    font-size: 0.88rem; color: #CBD5E1; line-height: 1.7;
    white-space: pre-wrap; padding: 8px 0;
}

/* ── Priority badge ── */
.badge {
    display: inline-block; padding: 2px 8px; border-radius: 6px;
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.06em;
}
.badge-critical { background: #7F1D1D; color: #FCA5A5; }
.badge-high     { background: #78350F; color: #FCD34D; }
.badge-medium   { background: #1E3A5F; color: #93C5FD; }
.badge-low      { background: #064E3B; color: #6EE7B7; }
.badge-purple   { background: #3730A3; color: #C7D2FE; }

/* ── AI card ── */
.ai-card {
    background: linear-gradient(135deg, #1E1B4B 0%, #1A1A3E 100%);
    border: 1px solid #3730A3; border-radius: 12px; padding: 16px;
    margin-bottom: 12px;
}
.ai-card-title { font-size: 0.78rem; font-weight: 700; color: #818CF8;
                 text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }

/* ── Meeting card ── */
.meeting-card {
    background: #12122A; border: 1px solid #1E1E3A;
    border-top: 3px solid #6366F1; border-radius: 12px;
    padding: 16px; margin-bottom: 10px;
}

/* ── Pill ── */
.pill {
    display: inline-block; background: #1E1E3A; border: 1px solid #2D2D5E;
    color: #818CF8; padding: 3px 10px; border-radius: 16px;
    font-size: 0.74rem; margin: 2px;
}

/* ── Contact card ── */
.contact-card {
    background: #12122A; border: 1px solid #1E1E3A; border-radius: 12px;
    padding: 16px; margin-bottom: 8px;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #6366F1, #4F46E5) !important;
    color: white !important; border: none !important;
    border-radius: 9px !important; font-weight: 600 !important;
    padding: 0.35rem 1rem !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* ── Email list select buttons: transparent ghost ── */
[data-testid="column"]:has(+ [data-testid="column"] div[style*="margin-top:-42px"]) 
  .stButton > button,
div[data-testid="stVerticalBlock"] [data-testid="stButton"]:has(button) + div[style*="margin-top:-42px"] {
    /* target via adjacent sibling */
}
/* Universal approach: any button inside the email list col_card that precedes a margin-top card */
div[style*="margin-top:-42px"] ~ .stButton > button {
    background: transparent !important;
    color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* ── Ghost/invisible email select buttons ── */
[data-testid="stButton"] button[kind="secondary"].ghost-email-btn,
div[data-testid="column"] .stButton.email-select-btn > button {
    display: none !important;
}
/* Target email select buttons by aria-label pattern */
button[aria-label="select"] {
    visibility: hidden !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    background: none !important;
    position: absolute !important;
}
/* Make ALL email list buttons invisible - only HTML cards show */
[data-testid="stVerticalBlock"] [data-testid="stButton"]:has(button[kind="secondary"]) > button[title] {
    visibility: hidden !important;
    height: 1px !important;
    overflow: hidden !important;
    padding: 0 !important;
    margin: 0 !important;
    min-height: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* ── Sidebar nav buttons ── */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid transparent !important;
    color: #94A3B8 !important;
    font-weight: 500 !important;
    text-align: left !important;
    border-radius: 8px !important;
    padding: 0.4rem 0.8rem !important;
    transition: all 0.15s !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #1E1E3A !important;
    color: #E2E8F0 !important;
    opacity: 1 !important;
    border-color: #2D2D5E !important;
}

/* ── Toggle labels — prevent wrap ── */
[data-testid="stToggle"] label {
    white-space: nowrap !important;
    font-size: 0.78rem !important;
}
[data-testid="stToggle"] { min-width: 0 !important; }

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"] { color: #64748B !important; font-size: 0.85rem !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #818CF8 !important; border-bottom: 2px solid #6366F1 !important;
}
[data-testid="stExpander"] {
    background: #12122A !important; border: 1px solid #1E1E3A !important;
    border-radius: 10px !important;
}

/* ════ EMAIL SELECT BUTTONS — fully transparent ════
   These buttons have keys starting with "esel_"
   We use the button's visible text (truncated subject) and 
   negative margin card trick. Button must be transparent. */
button[data-testid="baseButton-secondary"] {
    /* All secondary buttons get styled unless overridden */
}
/* The email-card button: sits ABOVE the card visually but is transparent */
[data-testid="stVerticalBlock"] [data-testid="stHorizontalBlock"] 
  [data-testid="column"]:last-child .stButton > button {
    background: transparent !important;
    color: transparent !important;
    border: 1px solid transparent !important;
    box-shadow: none !important;
    height: 66px !important;
    min-height: 66px !important;
    margin-bottom: -66px !important;
    position: relative !important;
    z-index: 5 !important;
    cursor: pointer !important;
}
[data-testid="stVerticalBlock"] [data-testid="stHorizontalBlock"] 
  [data-testid="column"]:last-child .stButton > button:hover {
    background: transparent !important;
    opacity: 0 !important;
}
[data-testid="stVerticalBlock"] [data-testid="stHorizontalBlock"] 
  [data-testid="column"]:last-child .stButton > button:active {
    background: transparent !important;
}

/* ════ SIDEBAR: override nav buttons to be subtle text nav ════ */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #6B7280 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.45rem 1rem !important;
    font-size: 0.86rem !important;
    font-weight: 500 !important;
    text-align: left !important;
    justify-content: flex-start !important;
    letter-spacing: 0 !important;
    opacity: 1 !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #1A1A30 !important;
    color: #C4C9F0 !important;
    opacity: 1 !important;
}

/* ── Scrollable email list ── */
.email-list-scroll {
    max-height: calc(100vh - 280px);
    overflow-y: auto;
    padding-right: 4px;
}
.email-list-scroll::-webkit-scrollbar { width: 4px; }
.email-list-scroll::-webkit-scrollbar-track { background: transparent; }
.email-list-scroll::-webkit-scrollbar-thumb { background: #2D2D5E; border-radius: 4px; }

/* ── Invisible email select buttons (dot buttons used as click targets) ── */
/* These buttons have "·" as their label */
[data-testid="stVerticalBlock"] .stButton > button:not([aria-expanded]) {
    /* Only hide buttons inside the email list column that are invisible triggers */
}
/* The wrapper div makes space; button is hidden inside it */
div[style*="margin-top:-74px"] .stButton > button,
div[style*="margin-top:-74"] .stButton > button {
    height: 74px !important;
    background: transparent !important;
    color: transparent !important;
    border: none !important;
    opacity: 0 !important;
    cursor: pointer !important;
    box-shadow: none !important;
    font-size: 1px !important;
}
div[style*="margin-top:-74px"] .stButton > button:hover {
    background: transparent !important;
    opacity: 0 !important;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def mc(value, label, sub=""):
    sub_html = f'<div class="mc-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
<div class="mc">
  <div class="mc-val">{value}</div>
  <div class="mc-lbl">{label}</div>
  {sub_html}
</div>""", unsafe_allow_html=True)


def badge(text: str, level: str = "purple") -> str:
    return f'<span class="badge badge-{level}">{text}</span>'


def priority_color(p: str) -> str:
    return {"critical": "#EF4444", "high": "#F59E0B", "medium": "#3B82F6", "low": "#10B981"}.get(p, "#6366F1")


def fmt_date(date_str: str) -> str:
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        if diff.days == 0:
            h = diff.seconds // 3600
            if h == 0:
                return f"{diff.seconds // 60}m ago"
            return f"{h}h ago"
        if diff.days == 1:
            return "Yesterday"
        if diff.days < 7:
            return f"{diff.days}d ago"
        return dt.strftime("%b %d")
    except Exception:
        return date_str[:10] if date_str else ""


def fmt_event_time(dt_str: str) -> str:
    try:
        from dateutil import parser as dp
        dt = dp.parse(dt_str)
        return dt.strftime("%I:%M %p")
    except Exception:
        return dt_str[11:16] if len(dt_str) > 16 else dt_str


def get_sender_name(from_str: str) -> str:
    if "<" in from_str:
        return from_str.split("<")[0].strip().strip('"')
    return from_str.split("@")[0]


def use_demo() -> bool:
    return st.session_state.get("use_demo", True)


def current_emails() -> list[dict]:
    if use_demo():
        return get_demo_emails()
    emails = database.get_emails(limit=100)
    if not emails:
        from modules import gmail_client
        if gmail_client.is_authenticated():
            raw = gmail_client.fetch_emails(max_results=50, include_body=False)
            database.upsert_emails(raw)
            return database.get_emails(limit=100)
    return emails


def current_events() -> list[dict]:
    if use_demo():
        return get_demo_events()
    try:
        from modules import gmail_client
        return gmail_client.fetch_upcoming_events(days_ahead=7)
    except Exception:
        return []


def ai_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


# ═══════════════════════════════════════════════════════════════════════════════
#  Sidebar
# ═══════════════════════════════════════════════════════════════════════════════

PAGES = {
    "📬 Inbox": "inbox",
    "✨ AI Triage": "triage",
    "📅 Calendar & Meetings": "calendar",
    "🧠 Meeting Prep": "meeting_prep",
    "✍️ AI Compose": "compose",
    "👥 Contacts": "contacts",
    "⏰ Reminders": "reminders",
    "📊 Dashboard": "dashboard",
    "⚙️ Settings": "settings",
}

with st.sidebar:
    st.markdown("""
<style>
/* ── Sidebar nav button overrides ── */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid transparent !important;
    color: #6B7280 !important;
    font-weight: 500 !important;
    text-align: left !important;
    border-radius: 8px !important;
    padding: 0.42rem 0.9rem !important;
    font-size: 0.87rem !important;
    justify-content: flex-start !important;
    opacity: 1 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #1A1A30 !important;
    color: #C4C9F0 !important;
    border-color: #2D2D5E !important;
}
[data-testid="stSidebar"] .stButton.nav-active > button,
[data-testid="stSidebar"] .stButton > button[data-active="true"] {
    background: linear-gradient(135deg,#2D2D6A,#1E1E50) !important;
    color: #818CF8 !important;
    border-color: #4F46E533 !important;
}
/* Toggle in sidebar */
[data-testid="stSidebar"] [data-testid="stToggle"] label { font-size: 0.82rem !important; }
</style>
<div style='text-align:center;padding:16px 0 10px;'>
  <div style='width:40px;height:40px;background:linear-gradient(135deg,#6366F1,#4F46E5);
              border-radius:12px;display:flex;align-items:center;justify-content:center;
              font-size:1.2rem;margin:0 auto 10px;'>✉️</div>
  <div style='font-size:1rem;font-weight:700;color:#E2E8F0;'>Email Assistant</div>
  <div style='font-size:0.68rem;color:#374151;margin-top:2px;'>AI-Powered · Personal</div>
</div>
<hr style='border-color:#1E1E3A;margin:6px 0 10px;'>
""", unsafe_allow_html=True)

    if "page" not in st.session_state:
        st.session_state.page = "inbox"

    for label, key in PAGES.items():
        is_active = st.session_state.page == key
        # Render active state with a highlight div behind the button
        if is_active:
            st.markdown(f"""
<div style="background:linear-gradient(135deg,#1E1E4A,#181838);border:1px solid #3730A333;
            border-radius:8px;margin-bottom:2px;overflow:hidden;">""", unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.rerun()
        if is_active:
            st.markdown("</div>", unsafe_allow_html=True)
        elif not is_active:
            st.markdown("<div style='margin-bottom:2px;'></div>", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#1E1E3A;margin:14px 0;'>", unsafe_allow_html=True)

    # Demo / Live toggle
    demo_mode = st.toggle("🎭 Demo Mode", value=st.session_state.get("use_demo", True))
    st.session_state.use_demo = demo_mode
    if demo_mode:
        st.markdown("<div style='font-size:0.72rem;color:#64748B;text-align:center;'>Using demo data — no Gmail needed</div>", unsafe_allow_html=True)

    # Quick stats
    stats = database.get_overall_stats()
    emails = current_emails()
    unread = sum(1 for e in emails if e.get("is_unread"))
    st.markdown(f"""
<div style='font-size:0.72rem;color:#374151;text-align:center;margin-top:8px;'>
  {unread} unread · {stats['reminders']} reminders · {stats['follow_ups']} follow-ups
</div>
""", unsafe_allow_html=True)

page = st.session_state.page


# ═══════════════════════════════════════════════════════════════════════════════
#  INBOX
# ═══════════════════════════════════════════════════════════════════════════════
if page == "inbox":
    # Page header
    st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
  <div style="font-size:1.6rem;font-weight:800;color:#E2E8F0;">📬 Inbox</div>
</div>""", unsafe_allow_html=True)

    emails = current_emails()
    col_list, col_viewer = st.columns([5, 7])

    with col_list:
        # ── Filter bar: single row, no wrapping ──────────────────────────
        st.markdown("""
<style>
/* Make filter row compact and no-wrap */
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stToggle"]) {
    gap: 4px !important; align-items: center !important;
}
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stToggle"]) 
  [data-testid="stToggle"] label p {
    font-size: 0.74rem !important; white-space: nowrap !important;
}
/* Search box compact */
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stToggle"]) 
  [data-testid="stTextInput"] input {
    font-size: 0.82rem !important; padding: 0.3rem 0.6rem !important;
}
</style>""", unsafe_allow_html=True)

        fc = st.columns([1.1, 1.1, 0.8, 3.2])
        with fc[0]:
            show_unread = st.toggle("Unread", value=False, key="tog_unread")
        with fc[1]:
            show_important = st.toggle("⭐ Star", value=False, key="tog_star")
        with fc[2]:
            show_starred = st.toggle("❗", value=False, key="tog_imp")
        with fc[3]:
            search = st.text_input("", placeholder="🔍 Search...",
                                   label_visibility="collapsed", key="inbox_search")

        filtered = emails
        if show_unread:
            filtered = [e for e in filtered if e.get("is_unread")]
        if show_important:
            filtered = [e for e in filtered if e.get("is_starred")]
        if show_starred:
            filtered = [e for e in filtered if e.get("is_important")]
        if search:
            s = search.lower()
            filtered = [e for e in filtered
                        if s in e.get("subject", "").lower()
                        or s in e.get("sender", e.get("from", "")).lower()
                        or s in e.get("snippet", "").lower()]

        # Count line
        unread_count = sum(1 for e in filtered if e.get("is_unread"))
        st.markdown(
            f"<div style='font-size:0.72rem;color:#4B5563;margin:6px 0 8px;'>"
            f"{len(filtered)} emails · <span style='color:#6366F1;'>{unread_count} unread</span></div>",
            unsafe_allow_html=True,
        )

        # ── Email cards ──────────────────────────────────────────────────
        for email in filtered:
            p = email.get("_ai_priority", "")
            is_unread = email.get("is_unread", False)
            is_selected = st.session_state.get("selected_email_id") == email["id"]
            p_color = priority_color(p) if p else "#2D2D5E"
            sender_name = get_sender_name(email.get("sender", email.get("from", "")))
            subject = email.get("subject", "(no subject)")
            snippet = email.get("snippet", "")
            date_str = fmt_date(email.get("date_str", email.get("date", "")))

            # Priority badge HTML
            p_badge = ""
            if p:
                p_badge = f'<span style="background:{p_color}22;color:{p_color};border:1px solid {p_color}55;border-radius:3px;font-size:0.6rem;font-weight:700;padding:1px 5px;text-transform:uppercase;letter-spacing:0.04em;flex-shrink:0;">{p}</span>'

            # Unread dot
            dot_color = "#6366F1" if is_unread else "transparent"
            bold_subj = "font-weight:700;" if is_unread else "font-weight:400;"
            card_bg = "#1A1A4A" if is_selected else "#12122A"
            card_border = "#6366F1" if is_selected else "#1E1E3A"
            left_bar = p_color if p else ("#6366F1" if is_unread else "#1E1E3A")

            # Flags
            flags = ""
            if email.get("is_starred"):
                flags += '<span style="font-size:0.72rem;">⭐</span>'
            if email.get("is_important"):
                flags += '<span style="font-size:0.72rem;">❗</span>'

            # ── Clickable email card using a hidden tiny button + HTML card ──
            # The button is styled to be invisible; the HTML card is the visual
            col_btn, col_card = st.columns([0.001, 1])
            with col_btn:
                pass  # empty spacer
            with col_card:
                clicked = st.button(
                    f"{subject[:30]}",
                    key=f"esel_{email['id']}",
                    use_container_width=True,
                )
                if clicked:
                    st.session_state.selected_email_id = email["id"]
                    st.session_state.selected_email = email
                    st.rerun()

                st.markdown(f"""
<div style="background:{card_bg};border:1px solid {card_border};
     border-left:3px solid {left_bar};border-radius:10px;
     padding:10px 13px;margin-top:-42px;margin-bottom:4px;
     pointer-events:none;">
  <div style="display:flex;align-items:flex-start;gap:8px;">
    <div style="width:7px;height:7px;border-radius:50%;background:{dot_color};
                flex-shrink:0;margin-top:6px;"></div>
    <div style="flex:1;min-width:0;">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:4px;margin-bottom:2px;">
        <div style="font-size:0.74rem;color:#818CF8;white-space:nowrap;
                    overflow:hidden;text-overflow:ellipsis;max-width:160px;">{flags}{sender_name}</div>
        <div style="font-size:0.66rem;color:#374151;white-space:nowrap;flex-shrink:0;">{date_str}</div>
      </div>
      <div style="font-size:0.83rem;{bold_subj}color:#E2E8F0;white-space:nowrap;
                  overflow:hidden;text-overflow:ellipsis;margin-bottom:3px;">{subject}</div>
      <div style="display:flex;align-items:center;gap:5px;">
        {p_badge}
        <div style="font-size:0.73rem;color:#4B5563;white-space:nowrap;
                    overflow:hidden;text-overflow:ellipsis;">{snippet[:80]}</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    with col_viewer:
        sel = st.session_state.get("selected_email")
        if not sel:
            st.markdown("""
<div style='text-align:center;padding:80px 20px;color:#374151;'>
  <div style='font-size:3rem;'>📩</div>
  <div style='font-size:1rem;margin-top:12px;'>Select an email to read</div>
</div>
""", unsafe_allow_html=True)
        else:
            p = sel.get("_ai_priority", "medium")
            color = priority_color(p)
            st.markdown(f"""
<div class="email-viewer">
  <div class="email-header-block">
    <div style="font-size:1.1rem;font-weight:700;color:#E2E8F0;">{sel.get('subject','')}</div>
    <div style="display:flex;gap:12px;margin-top:8px;flex-wrap:wrap;">
      <span style="font-size:0.8rem;color:#6366F1;">From: {sel.get('sender',sel.get('from',''))}</span>
      <span style="font-size:0.8rem;color:#4B5563;">To: {sel.get('to','')}</span>
      <span style="font-size:0.78rem;color:#374151;">{fmt_date(sel.get('date_str',sel.get('date','')))}</span>
      {badge(p.upper(), p) if p else ''}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

            tab_read, tab_ai, tab_reply = st.tabs(["📖 Read", "🤖 AI Analysis", "↩️ Reply"])

            with tab_read:
                body = sel.get("body") or sel.get("snippet", "")
                st.markdown(f'<div class="email-body-text">{body}</div>', unsafe_allow_html=True)

                act1, act2, act3, act4 = st.columns(4)
                with act1:
                    if st.button("⭐ Star", key="star_btn", use_container_width=True):
                        st.success("Starred!")
                with act2:
                    if st.button("⏰ Remind", key="remind_btn", use_container_width=True):
                        st.session_state.remind_email = sel
                        st.session_state.page = "reminders"
                        st.rerun()
                with act3:
                    if st.button("🔁 Follow Up", key="follow_btn", use_container_width=True):
                        due = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                        database.add_follow_up(
                            sel["id"], sel.get("subject", ""), sel.get("from", ""), due
                        )
                        st.success("Follow-up added for 3 days!")
                with act4:
                    if st.button("📁 Archive", key="archive_btn", use_container_width=True):
                        st.info("Archived (demo)")

            with tab_ai:
                if not ai_available():
                    st.warning("⚠️ Add your OpenAI API key in Settings to use AI features.")
                else:
                    body_text = sel.get("body") or sel.get("snippet", "")
                    col_s, col_p = st.columns(2)

                    with col_s:
                        if st.button("🔍 Summarize Email", use_container_width=True):
                            with st.spinner("Analyzing..."):
                                summary = agent.summarize_email(
                                    sel.get("subject", ""), sel.get("from", ""), body_text
                                )
                                st.session_state[f"summary_{sel['id']}"] = summary

                        summary = st.session_state.get(f"summary_{sel['id']}")
                        if summary:
                            st.markdown(f'<div class="ai-card"><div class="ai-card-title">📋 Summary</div>{summary}</div>', unsafe_allow_html=True)

                    with col_p:
                        if st.button("🎯 Classify Priority", use_container_width=True):
                            with st.spinner("Classifying..."):
                                cl = agent.classify_priority(
                                    sel.get("subject", ""), sel.get("from", ""), sel.get("snippet", "")
                                )
                                st.session_state[f"priority_{sel['id']}"] = cl

                        cl = st.session_state.get(f"priority_{sel['id']}")
                        if cl:
                            p2 = cl.get("priority", "medium")
                            st.markdown(f"""
<div class="ai-card">
  <div class="ai-card-title">🎯 Priority Classification</div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px;">
    {badge(p2.upper(), p2)}
    {badge(cl.get('category','').upper(), 'purple')}
    <span style="font-size:0.8rem;color:#64748B;">Urgency: {cl.get('urgency_score',0)}/10</span>
  </div>
  <div style="font-size:0.83rem;color:#94A3B8;">{cl.get('reason','')}</div>
  <div style="font-size:0.78rem;color:#6366F1;margin-top:6px;">Action: {cl.get('suggested_action','')}</div>
</div>""", unsafe_allow_html=True)

                    # Thread context
                    if st.button("🧵 Analyze Thread Context", use_container_width=True):
                        with st.spinner("Analyzing conversation..."):
                            # Use current email as single-message thread for demo
                            fake_thread = [sel]
                            ctx = agent.generate_conversation_context(fake_thread)
                            st.session_state[f"ctx_{sel['id']}"] = ctx

                    ctx = st.session_state.get(f"ctx_{sel['id']}")
                    if ctx:
                        st.markdown(f"""
<div class="ai-card">
  <div class="ai-card-title">🧵 Thread Context</div>
  <div style="font-size:0.85rem;color:#CBD5E1;margin-bottom:8px;">{ctx.get('thread_summary','')}</div>
  <div style="font-size:0.8rem;color:#64748B;"><strong style="color:#818CF8;">Status:</strong> {ctx.get('current_status','')}</div>
  <div style="font-size:0.8rem;color:#64748B;margin-top:4px;"><strong style="color:#818CF8;">Next step:</strong> {ctx.get('next_step','')}</div>
  {''.join([f"<div style='font-size:0.78rem;margin-top:6px;'>• <strong style='color:#818CF8;'>{a.get('who','')}:</strong> {a.get('what','')}</div>" for a in ctx.get('action_items',[])[:3]])}
</div>""", unsafe_allow_html=True)

            with tab_reply:
                body_text = sel.get("body") or sel.get("snippet", "")

                if ai_available():
                    if st.button("✨ Generate Smart Replies", use_container_width=True, key="gen_replies"):
                        with st.spinner("Generating reply options..."):
                            replies = agent.suggest_replies(
                                sel.get("subject", ""), sel.get("from", ""), body_text
                            )
                            st.session_state[f"replies_{sel['id']}"] = replies

                    replies = st.session_state.get(f"replies_{sel['id']}", [])
                    if replies:
                        for i, r in enumerate(replies):
                            with st.expander(f"Option {i+1}: {r.get('tone','')}", expanded=(i == 0)):
                                edited = st.text_area("", value=r.get("body", ""),
                                                       height=120, key=f"reply_text_{sel['id']}_{i}")
                                c1, c2 = st.columns(2)
                                with c1:
                                    if st.button("📋 Copy", key=f"copy_{i}", use_container_width=True):
                                        st.code(edited)
                                with c2:
                                    if st.button("💾 Save as Draft", key=f"draft_{i}", use_container_width=True):
                                        database.save_draft(
                                            sel.get("from", ""),
                                            r.get("subject", f"Re: {sel.get('subject','')}"),
                                            edited, r.get("tone", "professional").lower(),
                                            sel["id"],
                                        )
                                        st.success("Saved to drafts!")

                # Manual compose
                st.markdown("---")
                st.markdown("**✍️ Or write your reply:**")
                reply_to = sel.get("from", "")
                reply_subject = f"Re: {sel.get('subject', '')}"
                reply_body = st.text_area("Your reply", height=150, key="manual_reply_body")
                rc1, rc2 = st.columns(2)
                with rc1:
                    if st.button("📤 Send Reply", use_container_width=True, key="send_reply"):
                        if not use_demo():
                            from modules import gmail_client
                            ok = gmail_client.send_email(reply_to, reply_subject, reply_body, sel["id"], sel.get("thread_id",""))
                            st.success("Sent!" if ok else "Send failed")
                        else:
                            st.success("✅ Sent! (demo mode — not actually sent)")
                with rc2:
                    if st.button("💾 Save Draft", use_container_width=True, key="save_reply_draft"):
                        database.save_draft(reply_to, reply_subject, reply_body, "professional", sel["id"])
                        st.success("Draft saved!")


# ═══════════════════════════════════════════════════════════════════════════════
#  AI TRIAGE
# ═══════════════════════════════════════════════════════════════════════════════
if page == "triage":
    st.markdown("# ✨ AI Triage")
    st.markdown("<p style='color:#4B5563;margin-top:-10px;'>AI-ranked inbox — most important emails first</p>", unsafe_allow_html=True)

    emails = current_emails()

    col_a, col_b, col_c, col_d = st.columns(4)
    critical = [e for e in emails if e.get("_ai_priority") == "critical"]
    high = [e for e in emails if e.get("_ai_priority") == "high"]
    medium = [e for e in emails if e.get("_ai_priority") == "medium"]
    low = [e for e in emails if e.get("_ai_priority") == "low"]

    with col_a: mc(len(critical), "Critical 🔴")
    with col_b: mc(len(high), "High 🟠")
    with col_c: mc(len(medium), "Medium 🔵")
    with col_d: mc(len(low), "Low 🟢")

    st.markdown("")

    if ai_available():
        if st.button("🤖 Re-Rank with AI (Live)", use_container_width=False):
            with st.spinner("AI is ranking your inbox..."):
                unread_emails = [e for e in emails if e.get("is_unread")][:20]
                ranked = agent.rank_priority_inbox(unread_emails)
                st.session_state.ai_ranked = ranked
                st.success(f"Ranked {len(ranked)} emails!")

    # Priority sections
    for priority, label, emoji in [
        ("critical", "Critical — Act Now", "🔴"),
        ("high", "High Priority", "🟠"),
        ("medium", "Medium Priority", "🔵"),
        ("low", "Low / FYI", "🟢"),
    ]:
        grp = [e for e in emails if e.get("_ai_priority") == priority]
        if not grp:
            continue
        st.markdown(f'<div class="sh">{emoji} {label} ({len(grp)})</div>', unsafe_allow_html=True)

        for email in grp:
            col_email, col_actions = st.columns([5, 1])
            with col_email:
                cat = email.get("_ai_category", "")
                urgency = email.get("_ai_urgency", "")
                st.markdown(f"""
<div class="email-row {priority}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div style="flex:1;">
      <div class="email-subject">{email.get('subject','')}</div>
      <div class="email-from">{get_sender_name(email.get('sender',email.get('from','')))} 
        {f'<span class="pill">{cat}</span>' if cat else ''}
        {f'<span style="font-size:0.72rem;color:#64748B;">urgency {urgency}/10</span>' if urgency else ''}
      </div>
      <div class="email-snippet">{email.get('snippet','')[:110]}</div>
    </div>
    <div class="email-date">{fmt_date(email.get('date_str',email.get('date','')))}</div>
  </div>
</div>
""", unsafe_allow_html=True)

            with col_actions:
                if st.button("Open", key=f"tri_open_{email['id']}", use_container_width=True):
                    st.session_state.selected_email = email
                    st.session_state.selected_email_id = email["id"]
                    st.session_state.page = "inbox"
                    st.rerun()

    # Unanswered important emails detection
    st.markdown('<div class="sh">🚨 Needs Your Reply</div>', unsafe_allow_html=True)
    unread_important = [e for e in emails if e.get("is_unread") and e.get("_ai_priority") in ("critical", "high")]
    if unread_important:
        for email in unread_important[:5]:
            p = email.get("_ai_priority", "high")
            st.markdown(f"""
<div class="email-row {p}" style="background:#1A0E0E;">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <div>
      <div class="email-subject">⚠️ {email.get('subject','')}</div>
      <div class="email-from">{get_sender_name(email.get('sender',email.get('from','')))} · Unread · {badge(p.upper(), p)}</div>
      <div class="email-snippet">{email.get('snippet','')[:100]}</div>
    </div>
    <div class="email-date">{fmt_date(email.get('date_str',email.get('date','')))}</div>
  </div>
</div>
""", unsafe_allow_html=True)
    else:
        st.success("✅ No urgent unanswered emails detected.")


# ═══════════════════════════════════════════════════════════════════════════════
#  CALENDAR & MEETINGS
# ═══════════════════════════════════════════════════════════════════════════════
if page == "calendar":
    st.markdown("# 📅 Calendar & Meetings")

    events = current_events()
    emails = current_emails()

    # Today strip
    today_evts = [e for e in events if datetime.now().date().isoformat() in e.get("start", "")]
    if today_evts:
        st.markdown('<div class="sh">📍 Today</div>', unsafe_allow_html=True)
        cols = st.columns(min(len(today_evts), 4))
        for i, evt in enumerate(today_evts):
            with cols[i % 4]:
                attendee_count = len(evt.get("attendees", []))
                st.markdown(f"""
<div class="meeting-card">
  <div style="font-size:0.72rem;color:#6366F1;font-weight:700;">{fmt_event_time(evt.get('start',''))} – {fmt_event_time(evt.get('end',''))}</div>
  <div style="font-weight:700;color:#E2E8F0;margin:4px 0;">{evt.get('title','')}</div>
  <div style="font-size:0.78rem;color:#64748B;">{evt.get('location','') or 'No location'}</div>
  <div style="font-size:0.75rem;color:#374151;margin-top:4px;">👥 {attendee_count} attendees</div>
  {f'<a href="{evt.get("meet_link","")}" target="_blank" style="font-size:0.75rem;color:#6366F1;">🔗 Join Meeting</a>' if evt.get("meet_link") else ''}
</div>
""", unsafe_allow_html=True)

    # Upcoming events
    st.markdown('<div class="sh">📆 Upcoming 7 Days</div>', unsafe_allow_html=True)

    for evt in events:
        attendees = evt.get("attendees", [])
        # Find related emails (by attendee name matching)
        related = [e for e in emails if any(
            a.split("@")[0] in e.get("sender", e.get("from", "")).lower()
            for a in attendees
        )][:2]

        with st.expander(f"📅 {evt.get('title','')} — {evt.get('start','')[:10]} at {fmt_event_time(evt.get('start',''))}"):
            col1, col2 = st.columns([3, 2])

            with col1:
                st.markdown(f"**📍 Location:** {evt.get('location','N/A')}")
                st.markdown(f"**🕐 Time:** {fmt_event_time(evt.get('start',''))} – {fmt_event_time(evt.get('end',''))}")
                if evt.get("description"):
                    st.markdown(f"**📝 Description:** {evt.get('description','')}")
                if evt.get("meet_link"):
                    st.markdown(f"**🔗 [Join Meeting]({evt.get('meet_link','')})**")

                if attendees:
                    st.markdown("**👥 Attendees:**")
                    st.markdown(" ".join([f'<span class="pill">{a}</span>' for a in attendees]), unsafe_allow_html=True)

            with col2:
                if related:
                    st.markdown("**📬 Related Emails:**")
                    for em in related:
                        st.markdown(f"""
<div style="background:#0E0E1C;border-radius:8px;padding:8px 10px;margin-bottom:4px;font-size:0.78rem;">
  <div style="color:#818CF8;">{em.get('subject','')[:50]}</div>
  <div style="color:#4B5563;">{fmt_date(em.get('date_str',em.get('date','')))}</div>
</div>""", unsafe_allow_html=True)

                if st.button("🧠 Prep Brief", key=f"prep_{evt['id']}", use_container_width=True):
                    st.session_state.prep_event = evt
                    st.session_state.prep_related = related
                    st.session_state.page = "meeting_prep"
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  MEETING PREP
# ═══════════════════════════════════════════════════════════════════════════════
if page == "meeting_prep":
    st.markdown("# 🧠 Meeting Preparation")

    events = current_events()
    emails = current_emails()

    # Event selector
    event_options = {f"{e.get('title','')} — {e.get('start','')[:10]}": e for e in events}
    chosen_label = st.selectbox("Select Meeting", list(event_options.keys()))
    evt = event_options.get(chosen_label, st.session_state.get("prep_event"))

    if not evt:
        st.info("Select a meeting to prepare for.")
        st.stop()

    # Related emails for this meeting
    attendees = evt.get("attendees", [])
    related_emails = [e for e in emails if any(
        a.split("@")[0].lower() in e.get("sender", e.get("from", "")).lower()
        for a in attendees
    )][:6]

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"""
<div class="meeting-card">
  <div style="font-size:0.72rem;color:#6366F1;font-weight:700;">MEETING DETAILS</div>
  <div style="font-weight:800;font-size:1.1rem;color:#E2E8F0;margin:8px 0;">{evt.get('title','')}</div>
  <div style="font-size:0.83rem;color:#94A3B8;">📅 {evt.get('start','')[:10]}</div>
  <div style="font-size:0.83rem;color:#94A3B8;">🕐 {fmt_event_time(evt.get('start',''))}</div>
  <div style="font-size:0.83rem;color:#94A3B8;">📍 {evt.get('location','N/A')}</div>
  <div style="font-size:0.83rem;color:#94A3B8;margin-top:8px;">👥 {len(attendees)} attendees</div>
  <div style="margin-top:8px;">{''.join([f'<span class="pill">{a}</span>' for a in attendees[:4]])}</div>
</div>
""", unsafe_allow_html=True)

        if related_emails:
            st.markdown('<div class="sh" style="font-size:0.9rem;">📬 Related Emails</div>', unsafe_allow_html=True)
            for em in related_emails[:3]:
                st.markdown(f"""
<div style="background:#0E0E1C;border-radius:8px;padding:8px 10px;margin-bottom:4px;">
  <div style="font-size:0.8rem;color:#818CF8;">{em.get('subject','')[:55]}</div>
  <div style="font-size:0.72rem;color:#4B5563;">{get_sender_name(em.get('sender',em.get('from','')))} · {fmt_date(em.get('date_str',em.get('date','')))}</div>
</div>""", unsafe_allow_html=True)

    with col2:
        if not ai_available():
            st.warning("Add your OpenAI API key in Settings to generate meeting prep briefs.")
        else:
            if st.button("🧠 Generate Full Meeting Brief", use_container_width=True, type="primary"):
                with st.spinner("Preparing your meeting brief..."):
                    brief = agent.prepare_meeting_brief(
                        evt.get("title", ""),
                        attendees,
                        evt.get("description", ""),
                        related_emails,
                    )
                    st.session_state[f"brief_{evt['id']}"] = brief

            brief = st.session_state.get(f"brief_{evt['id']}")
            if brief:
                tab_overview, tab_talking, tab_attendees, tab_checklist = st.tabs([
                    "📋 Overview", "💬 Talking Points", "👥 Attendees", "✅ Checklist"
                ])

                with tab_overview:
                    st.markdown(f'<div class="ai-card"><div class="ai-card-title">Executive Summary</div><div style="font-size:0.9rem;color:#CBD5E1;">{brief.get("executive_summary","")}</div></div>', unsafe_allow_html=True)

                    if brief.get("key_context"):
                        st.markdown("**🔑 Key Context:**")
                        for ctx in brief["key_context"]:
                            st.markdown(f"- {ctx}")

                    if brief.get("open_items"):
                        st.markdown("**❓ Open Items / Questions:**")
                        for item in brief["open_items"]:
                            st.markdown(f"- {item}")

                    if brief.get("suggested_outcomes"):
                        st.markdown("**🎯 Suggested Outcomes:**")
                        for out in brief["suggested_outcomes"]:
                            st.markdown(f"- {out}")

                with tab_talking:
                    st.markdown("**💬 Suggested Talking Points:**")
                    for i, tp in enumerate(brief.get("talking_points", []), 1):
                        st.markdown(f"""
<div style="background:#0E0E1C;border-left:3px solid #6366F1;border-radius:6px;
            padding:10px 14px;margin-bottom:8px;font-size:0.88rem;color:#CBD5E1;">
  <span style="color:#6366F1;font-weight:700;">{i}.</span> {tp}
</div>""", unsafe_allow_html=True)

                with tab_attendees:
                    for person in brief.get("attendee_notes", []):
                        st.markdown(f"""
<div class="contact-card">
  <div style="font-weight:600;color:#818CF8;">{person.get('person','')}</div>
  <div style="font-size:0.78rem;color:#6366F1;margin:2px 0;">{person.get('role','')}</div>
  <div style="font-size:0.83rem;color:#94A3B8;">{person.get('note','')}</div>
</div>""", unsafe_allow_html=True)

                with tab_checklist:
                    st.markdown("**✅ Pre-Meeting Checklist:**")
                    for i, task in enumerate(brief.get("prep_checklist", [])):
                        done = st.checkbox(task, key=f"chk_{evt['id']}_{i}")

            else:
                # Show contact history previews even without AI
                st.markdown('<div class="sh">📬 Conversation History with Attendees</div>', unsafe_allow_html=True)
                if related_emails:
                    for em in related_emails[:4]:
                        st.markdown(f"""
<div class="email-row">
  <div class="email-subject">{em.get('subject','')}</div>
  <div class="email-from">{get_sender_name(em.get('sender',em.get('from','')))} · {fmt_date(em.get('date_str',em.get('date','')))}</div>
  <div class="email-snippet">{em.get('snippet','')[:100]}</div>
</div>""", unsafe_allow_html=True)
                else:
                    st.info("No related emails found for this meeting's attendees.")


# ═══════════════════════════════════════════════════════════════════════════════
#  AI COMPOSE
# ═══════════════════════════════════════════════════════════════════════════════
if page == "compose":
    st.markdown("# ✍️ AI Compose")
    st.markdown("<p style='color:#4B5563;margin-top:-10px;'>Draft, rewrite, and perfect emails with AI</p>", unsafe_allow_html=True)

    tab_new, tab_rewrite, tab_drafts = st.tabs(["✨ New Email", "🔄 Rewrite Tone", "💾 Saved Drafts"])

    with tab_new:
        col1, col2 = st.columns([2, 1])
        with col1:
            to_addr = st.text_input("To", placeholder="recipient@email.com")
            purpose = st.text_area("What should this email say?",
                placeholder="e.g. Follow up on our meeting yesterday about the Q3 budget. Ask when they can send the final numbers. Keep it friendly.",
                height=90)
        with col2:
            tone = st.selectbox("Tone", ["professional", "friendly", "assertive", "brief", "formal", "diplomatic"])
            context = st.text_area("Background context (optional)", height=60)

        if st.button("✨ Draft with AI", use_container_width=True, disabled=not ai_available()):
            if not purpose:
                st.warning("Please describe what the email should say.")
            else:
                with st.spinner("Drafting your email..."):
                    draft = agent.draft_email(to_addr, purpose, tone, context)
                    st.session_state.ai_draft = draft

        if not ai_available():
            st.warning("⚠️ Add your OpenAI API key in Settings to use AI drafting.")

        ai_draft = st.session_state.get("ai_draft")
        if ai_draft:
            st.markdown("---")
            st.markdown("**✨ AI Draft:**")
            col_subj, _ = st.columns([3, 1])
            with col_subj:
                subj_edit = st.text_input("Subject", value=ai_draft.get("subject", ""))
            body_edit = st.text_area("Body", value=ai_draft.get("body", ""), height=250)

            ca, cb, cc = st.columns(3)
            with ca:
                if st.button("📤 Send Now", use_container_width=True):
                    if not use_demo():
                        from modules import gmail_client
                        ok = gmail_client.send_email(to_addr, subj_edit, body_edit)
                        st.success("Sent!" if ok else "Send failed")
                    else:
                        st.success("✅ Email sent! (demo mode)")
            with cb:
                if st.button("💾 Save Draft", use_container_width=True):
                    database.save_draft(to_addr, subj_edit, body_edit, tone)
                    st.success("Draft saved!")
            with cc:
                if st.button("🔄 Regenerate", use_container_width=True):
                    with st.spinner("Redrafting..."):
                        st.session_state.ai_draft = agent.draft_email(to_addr, purpose, tone, context)
                    st.rerun()

    with tab_rewrite:
        st.markdown("**Paste your email and rewrite its tone:**")
        original_text = st.text_area("Original email body", height=180, placeholder="Paste your email here...")
        target_tone = st.selectbox("Rewrite in this tone",
            ["professional", "friendly", "assertive", "diplomatic", "brief", "formal"],
            key="rewrite_tone_sel")

        if st.button("🔄 Rewrite with AI", use_container_width=True, disabled=not ai_available()):
            if not original_text.strip():
                st.warning("Paste an email first.")
            else:
                with st.spinner("Rewriting..."):
                    rewritten = agent.rewrite_tone(original_text, target_tone)
                    st.session_state.rewritten_text = rewritten

        rewritten = st.session_state.get("rewritten_text")
        if rewritten:
            st.markdown("---")
            col_before, col_after = st.columns(2)
            with col_before:
                st.markdown("**Original:**")
                st.markdown(f'<div style="background:#0E0E1C;border-radius:8px;padding:12px;font-size:0.83rem;color:#94A3B8;">{original_text}</div>', unsafe_allow_html=True)
            with col_after:
                st.markdown(f"**{target_tone.title()} version:**")
                edited_rewrite = st.text_area("", value=rewritten, height=200, key="rewrite_edit")
                if st.button("💾 Save Rewritten Draft", use_container_width=True):
                    database.save_draft("", "Rewritten draft", edited_rewrite, target_tone)
                    st.success("Saved!")

        if not ai_available():
            st.warning("⚠️ Add your OpenAI API key in Settings.")

    with tab_drafts:
        drafts = database.get_drafts()
        if not drafts:
            st.info("No saved drafts yet.")
        else:
            for d in drafts:
                with st.expander(f"💾 {d.get('subject','')[:50]} → {d.get('to_addr','')}", expanded=False):
                    col_info, col_acts = st.columns([4, 1])
                    with col_info:
                        new_body = st.text_area("", value=d.get("body", ""), height=150, key=f"draft_body_{d['id']}")
                        st.markdown(f'<span class="pill">{d.get("tone","")}</span>', unsafe_allow_html=True)
                    with col_acts:
                        if st.button("💾 Update", key=f"upd_{d['id']}", use_container_width=True):
                            database.update_draft(d["id"], new_body)
                            st.success("Updated!")
                        if st.button("📤 Send", key=f"snd_{d['id']}", use_container_width=True):
                            if not use_demo():
                                from modules import gmail_client
                                ok = gmail_client.send_email(d.get("to_addr",""), d.get("subject",""), new_body)
                                if ok: database.delete_draft(d["id"])
                                st.success("Sent!" if ok else "Failed")
                            else:
                                st.success("Sent! (demo)")
                        if st.button("🗑️ Delete", key=f"del_{d['id']}", use_container_width=True):
                            database.delete_draft(d["id"])
                            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTACTS
# ═══════════════════════════════════════════════════════════════════════════════
if page == "contacts":
    st.markdown("# 👥 Contacts")

    emails = current_emails()
    demo_contacts = get_demo_contacts() if use_demo() else []

    # Sync contacts from emails
    contact_map: dict = {}
    for e in emails:
        from_str = e.get("sender", e.get("from", ""))
        if "<" in from_str:
            name = from_str.split("<")[0].strip().strip('"')
            addr = from_str.split("<")[1].replace(">", "").strip()
        else:
            addr = from_str
            name = addr.split("@")[0]
        if addr and "@" in addr and addr not in contact_map:
            contact_map[addr] = {"email": addr, "name": name, "count": 1}
        elif addr in contact_map:
            contact_map[addr]["count"] += 1

    # Merge with demo contacts
    all_contacts = demo_contacts if use_demo() else list(contact_map.values())

    search_c = st.text_input("🔍 Search contacts", placeholder="Name or email...")
    if search_c:
        all_contacts = [c for c in all_contacts if
                        search_c.lower() in c.get("name", "").lower() or
                        search_c.lower() in c.get("email", "").lower()]

    col_list, col_detail = st.columns([2, 3])

    with col_list:
        st.markdown(f'<div style="font-size:0.75rem;color:#4B5563;margin-bottom:8px;">{len(all_contacts)} contacts</div>', unsafe_allow_html=True)
        for c in all_contacts:
            initial = c.get("name", "?")[0].upper() if c.get("name") else "?"
            if st.button(f"{c.get('name','Unknown')} · {c.get('email','')[:30]}", key=f"c_{c['email']}", use_container_width=True):
                st.session_state.selected_contact = c

            st.markdown(f"""
<div class="contact-card" style="margin-top:-8px;margin-bottom:4px;">
  <div style="display:flex;align-items:center;gap:12px;">
    <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#6366F1,#4F46E5);
                display:flex;align-items:center;justify-content:center;font-weight:700;color:white;font-size:0.9rem;flex-shrink:0;">
      {initial}
    </div>
    <div>
      <div style="font-weight:600;color:#E2E8F0;font-size:0.88rem;">{c.get('name','Unknown')}</div>
      <div style="font-size:0.75rem;color:#64748B;">{c.get('company','') or c.get('email','')}</div>
      <div style="font-size:0.72rem;color:#374151;">{c.get('email_count', c.get('count',0))} emails · {c.get('last_contact','')[:10]}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    with col_detail:
        sel_c = st.session_state.get("selected_contact")
        if not sel_c:
            st.markdown("""
<div style='text-align:center;padding:60px;color:#374151;'>
  <div style='font-size:2.5rem;'>👤</div>
  <div style='margin-top:10px;'>Select a contact to view details</div>
</div>""", unsafe_allow_html=True)
        else:
            initial = sel_c.get("name", "?")[0].upper()
            st.markdown(f"""
<div style="display:flex;align-items:center;gap:16px;padding:16px;background:#12122A;
            border:1px solid #1E1E3A;border-radius:14px;margin-bottom:16px;">
  <div style="width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,#6366F1,#4F46E5);
              display:flex;align-items:center;justify-content:center;font-weight:800;
              color:white;font-size:1.3rem;flex-shrink:0;">{initial}</div>
  <div>
    <div style="font-size:1.15rem;font-weight:700;color:#E2E8F0;">{sel_c.get('name','Unknown')}</div>
    <div style="font-size:0.83rem;color:#6366F1;">{sel_c.get('email','')}</div>
    <div style="font-size:0.78rem;color:#64748B;">{sel_c.get('company','')}</div>
  </div>
</div>""", unsafe_allow_html=True)

            tab_overview, tab_emails, tab_ai = st.tabs(["📋 Overview", "📬 Emails", "🤖 AI Summary"])

            with tab_overview:
                st.markdown(f"**📊 Emails exchanged:** {sel_c.get('email_count', sel_c.get('count',0))}")
                st.markdown(f"**🕐 Last contact:** {sel_c.get('last_contact','N/A')[:10]}")
                notes = st.text_area("📝 Notes", value=sel_c.get("notes",""), height=100, key="contact_notes")
                if st.button("💾 Save Notes", use_container_width=True):
                    st.success("Notes saved!")

            with tab_emails:
                contact_emails = [e for e in emails if sel_c.get("email","") in e.get("sender",e.get("from",""))]
                if contact_emails:
                    for em in contact_emails[:6]:
                        st.markdown(f"""
<div class="email-row">
  <div class="email-subject">{em.get('subject','')[:60]}</div>
  <div style="font-size:0.75rem;color:#374151;">{fmt_date(em.get('date_str',em.get('date','')))}</div>
  <div class="email-snippet">{em.get('snippet','')[:90]}</div>
</div>""", unsafe_allow_html=True)
                else:
                    st.info("No emails found from this contact.")

            with tab_ai:
                if sel_c.get("ai_summary"):
                    st.markdown(f'<div class="ai-card"><div class="ai-card-title">🤖 AI Profile</div><div style="font-size:0.88rem;color:#CBD5E1;">{sel_c["ai_summary"]}</div></div>', unsafe_allow_html=True)
                elif ai_available():
                    if st.button("🤖 Generate AI Summary", use_container_width=True):
                        c_emails = [e for e in emails if sel_c.get("email","") in e.get("sender",e.get("from",""))]
                        with st.spinner("Analyzing email history..."):
                            summary = agent.summarize_contact(
                                sel_c.get("email",""), sel_c.get("name",""), c_emails
                            )
                        st.markdown(f'<div class="ai-card"><div class="ai-card-title">🤖 AI Profile</div><div style="font-size:0.88rem;color:#CBD5E1;">{summary}</div></div>', unsafe_allow_html=True)
                else:
                    st.warning("Add OpenAI API key to generate AI contact summaries.")


# ═══════════════════════════════════════════════════════════════════════════════
#  REMINDERS
# ═══════════════════════════════════════════════════════════════════════════════
if page == "reminders":
    st.markdown("# ⏰ Reminders & Follow-ups")

    tab_remind, tab_follow = st.tabs(["⏰ Reminders", "🔁 Follow-ups"])

    with tab_remind:
        col_form, col_list = st.columns([2, 3])

        with col_form:
            st.markdown('<div class="sh" style="font-size:0.9rem;">➕ New Reminder</div>', unsafe_allow_html=True)
            remind_title = st.text_input("Title", placeholder="e.g. Reply to Sarah about roadmap")
            remind_date = st.date_input("Due Date", value=datetime.now().date() + timedelta(days=1))
            remind_note = st.text_area("Note (optional)", height=70)
            if st.button("➕ Add Reminder", use_container_width=True):
                if remind_title:
                    database.add_reminder(remind_title, remind_date.isoformat(), note=remind_note)
                    st.success("Reminder added!")
                    st.rerun()

        with col_list:
            reminders = database.get_reminders(include_done=False)
            overdue = [r for r in reminders if r.get("due_date", "") < datetime.now().date().isoformat()]
            upcoming = [r for r in reminders if r.get("due_date", "") >= datetime.now().date().isoformat()]

            if overdue:
                st.markdown('<div class="sh" style="color:#EF4444;font-size:0.9rem;">🔴 Overdue</div>', unsafe_allow_html=True)
                for r in overdue:
                    cc1, cc2, cc3 = st.columns([5, 1, 1])
                    with cc1:
                        st.markdown(f"""
<div style="background:#1A0E0E;border:1px solid #EF444433;border-left:3px solid #EF4444;
            border-radius:8px;padding:10px 14px;margin-bottom:4px;">
  <div style="font-weight:600;color:#FCA5A5;">{r.get('title','')}</div>
  <div style="font-size:0.75rem;color:#EF4444;">Due: {r.get('due_date','')} · OVERDUE</div>
  {f'<div style="font-size:0.75rem;color:#4B5563;">{r.get("note","")}</div>' if r.get('note') else ''}
</div>""", unsafe_allow_html=True)
                    with cc2:
                        if st.button("✅", key=f"done_r_{r['id']}", use_container_width=True):
                            database.complete_reminder(r["id"])
                            st.rerun()
                    with cc3:
                        if st.button("🗑️", key=f"del_r_{r['id']}", use_container_width=True):
                            database.delete_reminder(r["id"])
                            st.rerun()

            if upcoming:
                st.markdown('<div class="sh" style="font-size:0.9rem;">📅 Upcoming</div>', unsafe_allow_html=True)
                for r in upcoming:
                    cc1, cc2, cc3 = st.columns([5, 1, 1])
                    with cc1:
                        days_left = (datetime.fromisoformat(r.get("due_date","2099-01-01")).date() - datetime.now().date()).days
                        color = "#F59E0B" if days_left <= 1 else "#6366F1"
                        st.markdown(f"""
<div style="background:#12122A;border:1px solid #1E1E3A;border-left:3px solid {color};
            border-radius:8px;padding:10px 14px;margin-bottom:4px;">
  <div style="font-weight:600;color:#E2E8F0;">{r.get('title','')}</div>
  <div style="font-size:0.75rem;color:{color};">Due: {r.get('due_date','')} · {days_left}d left</div>
  {f'<div style="font-size:0.75rem;color:#4B5563;">{r.get("note","")}</div>' if r.get('note') else ''}
</div>""", unsafe_allow_html=True)
                    with cc2:
                        if st.button("✅", key=f"done_r_{r['id']}", use_container_width=True):
                            database.complete_reminder(r["id"])
                            st.rerun()
                    with cc3:
                        if st.button("🗑️", key=f"del_r_{r['id']}", use_container_width=True):
                            database.delete_reminder(r["id"])
                            st.rerun()

            if not reminders:
                st.success("✅ No pending reminders!")

    with tab_follow:
        col_form2, col_list2 = st.columns([2, 3])

        with col_form2:
            st.markdown('<div class="sh" style="font-size:0.9rem;">➕ Track Follow-up</div>', unsafe_allow_html=True)
            emails = current_emails()
            email_opts = {f"{e.get('subject','')[:40]}": e for e in emails[:20]}
            selected_for_fu = st.selectbox("Email to follow up on", ["(manual)"] + list(email_opts.keys()))
            fu_recipient = st.text_input("Recipient email")
            fu_subject = st.text_input("Subject", value=email_opts.get(selected_for_fu, {}).get("subject","") if selected_for_fu != "(manual)" else "")
            fu_due = st.date_input("Follow-up by", value=datetime.now().date() + timedelta(days=3), key="fu_date")
            fu_note = st.text_area("Note", height=60)
            if st.button("➕ Add Follow-up", use_container_width=True):
                em = email_opts.get(selected_for_fu)
                database.add_follow_up(
                    em["id"] if em else "",
                    fu_subject, fu_recipient, fu_due.isoformat(), fu_note
                )
                st.success("Follow-up tracked!")
                st.rerun()

        with col_list2:
            follow_ups = database.get_follow_ups("pending")
            if follow_ups:
                st.markdown('<div class="sh" style="font-size:0.9rem;">🔁 Pending Follow-ups</div>', unsafe_allow_html=True)
                for fu in follow_ups:
                    days_left = (datetime.fromisoformat(fu.get("due_date","2099-01-01")).date() - datetime.now().date()).days
                    overdue = days_left < 0
                    color = "#EF4444" if overdue else "#F59E0B" if days_left <= 1 else "#6366F1"
                    fa, fb = st.columns([5, 1])
                    with fa:
                        st.markdown(f"""
<div style="background:#12122A;border:1px solid #1E1E3A;border-left:3px solid {color};
            border-radius:8px;padding:10px 14px;margin-bottom:4px;">
  <div style="font-weight:600;color:#E2E8F0;">{fu.get('subject','')[:55]}</div>
  <div style="font-size:0.75rem;color:#64748B;">To: {fu.get('recipient','N/A')}</div>
  <div style="font-size:0.75rem;color:{color};">{'OVERDUE' if overdue else f'{days_left}d left'} · Due {fu.get('due_date','')}</div>
</div>""", unsafe_allow_html=True)
                    with fb:
                        if st.button("✅", key=f"fu_done_{fu['id']}", use_container_width=True):
                            database.update_follow_up_status(fu["id"], "done")
                            st.rerun()
            else:
                st.success("✅ No pending follow-ups!")



# ═══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD / ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
if page == "dashboard":
    st.markdown("# 📊 Productivity Dashboard")

    emails = current_emails()
    stats = database.get_overall_stats()
    events = current_events()

    # Top metrics
    unread = sum(1 for e in emails if e.get("is_unread"))
    critical = sum(1 for e in emails if e.get("_ai_priority") == "critical")
    starred = sum(1 for e in emails if e.get("is_starred"))
    important = sum(1 for e in emails if e.get("is_important"))

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: mc(len(emails), "Total Emails", "cached")
    with c2: mc(unread, "Unread", "in inbox")
    with c3: mc(critical, "Critical 🔴", "need action")
    with c4: mc(stats["follow_ups"], "Follow-ups", "pending")
    with c5: mc(stats["reminders"], "Reminders", "active")

    st.markdown("")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<div class="sh">📊 Priority Distribution</div>', unsafe_allow_html=True)
        priority_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unclassified": 0}
        for e in emails:
            p = e.get("_ai_priority", "unclassified")
            if p in priority_counts:
                priority_counts[p] += 1
            else:
                priority_counts["unclassified"] += 1

        colors = {"critical": "#EF4444", "high": "#F59E0B", "medium": "#3B82F6",
                  "low": "#10B981", "unclassified": "#4B5563"}
        fig = go.Figure(go.Bar(
            x=list(priority_counts.keys()),
            y=list(priority_counts.values()),
            marker_color=[colors.get(k, "#6366F1") for k in priority_counts.keys()],
            text=list(priority_counts.values()),
            textposition="outside",
        ))
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#E2E8F0", height=250,
            xaxis=dict(showgrid=False, color="#4B5563"),
            yaxis=dict(showgrid=True, gridcolor="#1E1E3A", color="#4B5563"),
            margin=dict(l=0, r=0, t=20, b=0),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Category pie
        st.markdown('<div class="sh">📂 Email Categories</div>', unsafe_allow_html=True)
        cat_counts: dict = {}
        for e in emails:
            cat = e.get("_ai_category", "other")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        if cat_counts:
            fig2 = go.Figure(go.Pie(
                labels=list(cat_counts.keys()),
                values=list(cat_counts.values()),
                hole=0.5,
                marker_colors=["#6366F1", "#4F46E5", "#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"],
            ))
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#E2E8F0", height=260,
                showlegend=True, legend=dict(font=dict(color="#94A3B8"), x=1, y=0.5),
                margin=dict(l=0, r=100, t=0, b=0),
            )
            st.plotly_chart(fig2, use_container_width=True)

    with col_right:
        st.markdown('<div class="sh">⏰ Today\'s Schedule</div>', unsafe_allow_html=True)
        today_events = [e for e in events if datetime.now().date().isoformat() in e.get("start", "")]
        if today_events:
            for evt in today_events:
                st.markdown(f"""
<div class="meeting-card" style="padding:12px;">
  <div style="font-size:0.72rem;color:#6366F1;">{fmt_event_time(evt.get('start',''))}</div>
  <div style="font-weight:600;color:#E2E8F0;font-size:0.88rem;">{evt.get('title','')}</div>
  <div style="font-size:0.75rem;color:#4B5563;">{len(evt.get('attendees',[]))} attendees</div>
</div>""", unsafe_allow_html=True)
        else:
            st.info("No meetings today.")

        st.markdown('<div class="sh">🔥 Top Senders</div>', unsafe_allow_html=True)
        sender_map: dict = {}
        for e in emails:
            s = get_sender_name(e.get("sender", e.get("from", "")))
            sender_map[s] = sender_map.get(s, 0) + 1

        top_senders = sorted(sender_map.items(), key=lambda x: x[1], reverse=True)[:6]
        for name, count in top_senders:
            pct = int(count / max(len(emails), 1) * 100)
            st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
  <div style="font-size:0.83rem;color:#E2E8F0;width:120px;overflow:hidden;
              text-overflow:ellipsis;white-space:nowrap;">{name}</div>
  <div style="flex:1;background:#1E1E3A;border-radius:4px;height:6px;">
    <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#6366F1,#4F46E5);border-radius:4px;"></div>
  </div>
  <div style="font-size:0.72rem;color:#4B5563;width:24px;">{count}</div>
</div>""", unsafe_allow_html=True)

        # AI Inbox Insight
        if ai_available():
            st.markdown('<div class="sh">🤖 AI Insight</div>', unsafe_allow_html=True)
            if st.button("Generate Inbox Insight", use_container_width=True):
                with st.spinner("Analyzing inbox..."):
                    insight = agent.generate_inbox_insight(
                        stats, [s for s, _ in top_senders[:5]], emails[:5]
                    )
                    st.session_state.inbox_insight = insight

            insight = st.session_state.get("inbox_insight")
            if insight:
                st.markdown(f'<div class="ai-card"><div class="ai-card-title">🤖 Inbox Intelligence</div><div style="font-size:0.85rem;color:#CBD5E1;">{insight}</div></div>', unsafe_allow_html=True)

    # Upcoming events table
    st.markdown('<div class="sh">📆 Upcoming Meetings</div>', unsafe_allow_html=True)
    if events:
        evt_data = [{
            "Date": e.get("start","")[:10],
            "Time": fmt_event_time(e.get("start","")),
            "Meeting": e.get("title",""),
            "Attendees": len(e.get("attendees",[])),
            "Location": e.get("location","") or "Virtual",
        } for e in events[:5]]
        st.dataframe(pd.DataFrame(evt_data), use_container_width=True, hide_index=True)

    # Pending items
    st.markdown('<div class="sh">📋 Action Items</div>', unsafe_allow_html=True)
    ac1, ac2, ac3 = st.columns(3)
    with ac1:
        reminders = database.get_reminders()
        st.markdown(f"**⏰ Reminders ({len(reminders)})**")
        for r in reminders[:3]:
            st.markdown(f"- {r.get('title','')[:50]} · {r.get('due_date','')}")
    with ac2:
        follow_ups = database.get_follow_ups("pending")
        st.markdown(f"**🔁 Follow-ups ({len(follow_ups)})**")
        for f in follow_ups[:3]:
            st.markdown(f"- {f.get('subject','')[:50]} · {f.get('due_date','')}")
    with ac3:
        drafts = database.get_drafts()
        st.markdown(f"**💾 Drafts ({len(drafts)})**")
        for d in drafts[:3]:
            st.markdown(f"- {d.get('subject','')[:50]} → {d.get('to_addr','')[:25]}")


# ═══════════════════════════════════════════════════════════════════════════════
#  SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
if page == "settings":
    st.markdown("# ⚙️ Settings")

    tab_api, tab_gmail, tab_prefs, tab_db, tab_about = st.tabs([
        "🔑 API Keys", "📧 Gmail / OAuth", "🎛️ Preferences", "🗄️ Database", "ℹ️ About"
    ])

    with tab_api:
        st.markdown('<div class="sh">OpenAI Configuration</div>', unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        with col1:
            new_key = st.text_input("OpenAI API Key", type="password",
                value=os.environ.get("OPENAI_API_KEY",""),
                placeholder="sk-proj-...")
        with col2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("💾 Save", use_container_width=True):
                if new_key.startswith("sk-"):
                    os.environ["OPENAI_API_KEY"] = new_key
                    st.success("✅ Key saved!")
                else:
                    st.error("Must start with sk-")

        if os.environ.get("OPENAI_API_KEY"):
            key = os.environ["OPENAI_API_KEY"]
            st.markdown(f"""
<div style="background:#064E3B22;border:1px solid #10B98133;border-radius:8px;padding:10px 14px;
            font-size:0.82rem;color:#6EE7B7;">
  ✅ Active: <code>{key[:8]}...{key[-4:]}</code>
</div>""", unsafe_allow_html=True)
            if st.button("🧪 Test Connection"):
                with st.spinner("Testing..."):
                    try:
                        from openai import OpenAI
                        OpenAI(api_key=key).models.list()
                        st.success("✅ GPT-4o ready!")
                    except Exception as e:
                        st.error(f"❌ {e}")

        st.markdown('<div class="sh" style="margin-top:20px;">Model Settings</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"], index=0)
            st.session_state.ai_model = model
            cost = {"gpt-4o": "~$0.03–0.06/session", "gpt-4o-mini": "~$0.003/session", "gpt-4-turbo": "~$0.04/session"}
            st.caption(f"💰 {cost.get(model,'')}")
        with col2:
            max_emails = st.slider("Max emails to analyze", 10, 100, 50)
            st.session_state.max_emails = max_emails

    with tab_gmail:
        st.markdown('<div class="sh">Google OAuth Setup</div>', unsafe_allow_html=True)

        from modules import gmail_client
        if gmail_client.is_authenticated():
            st.success("✅ Gmail connected!")
            profile = gmail_client.get_profile()
            st.markdown(f"**Connected as:** {profile.get('emailAddress','')}")
            st.markdown(f"**Messages:** {profile.get('messagesTotal', 0):,}")
            if st.button("🔌 Disconnect Gmail"):
                gmail_client.revoke_credentials()
                st.success("Disconnected.")
                st.rerun()
        else:
            st.info("Connect your Gmail to use live email data (instead of demo mode).")

            col1, col2 = st.columns(2)
            with col1:
                g_client_id = st.text_input("Google Client ID",
                    value=os.environ.get("GOOGLE_CLIENT_ID",""), type="password")
            with col2:
                g_client_secret = st.text_input("Google Client Secret",
                    value=os.environ.get("GOOGLE_CLIENT_SECRET",""), type="password")

            redirect_uri = st.text_input("Redirect URI", value="http://localhost:8501")

            if st.button("🔗 Connect Gmail", disabled=not (g_client_id and g_client_secret)):
                os.environ["GOOGLE_CLIENT_ID"] = g_client_id
                os.environ["GOOGLE_CLIENT_SECRET"] = g_client_secret
                try:
                    flow = gmail_client.get_oauth_flow(g_client_id, g_client_secret, redirect_uri)
                    auth_url = gmail_client.get_auth_url(flow)
                    st.session_state.oauth_flow = flow
                    st.markdown(f"**[👉 Click here to authorize Gmail access]({auth_url})**")
                    st.info("After authorizing, paste the code from the redirect URL below.")
                except Exception as e:
                    st.error(f"OAuth setup failed: {e}")

            if st.session_state.get("oauth_flow"):
                auth_code = st.text_input("Paste authorization code here")
                if st.button("✅ Complete Connection") and auth_code:
                    try:
                        gmail_client.exchange_code(st.session_state.oauth_flow, auth_code)
                        st.success("✅ Gmail connected!")
                        st.session_state.use_demo = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Auth failed: {e}")

        st.markdown("""
<div style="background:#12122A;border:1px solid #1E1E3A;border-radius:10px;
            padding:14px 16px;font-size:0.82rem;color:#64748B;margin-top:16px;">
  <strong style="color:#818CF8;">📋 Google Cloud Setup:</strong><br>
  1. Go to <a href="https://console.cloud.google.com" target="_blank" style="color:#6366F1;">console.cloud.google.com</a><br>
  2. Create a project → Enable Gmail API + Google Calendar API<br>
  3. Create OAuth 2.0 credentials (Web application)<br>
  4. Add your redirect URI to authorized URIs<br>
  5. Copy Client ID and Client Secret here
</div>""", unsafe_allow_html=True)

    with tab_prefs:
        st.markdown('<div class="sh">Interface Preferences</div>', unsafe_allow_html=True)
        emails_per_page = st.slider("Emails per page", 10, 100, 50)
        st.session_state.emails_per_page = emails_per_page

        auto_classify = st.toggle("Auto-classify emails on load", value=False)
        st.session_state.auto_classify = auto_classify
        st.caption("⚠️ Uses API credits — ~$0.001 per email")

        show_snippets = st.toggle("Show email snippets in inbox", value=True)
        st.session_state.show_snippets = show_snippets

        default_tone = st.selectbox("Default reply tone", ["professional", "friendly", "brief", "assertive"])
        st.session_state.default_tone = default_tone

        reminder_days = st.slider("Default follow-up reminder (days)", 1, 14, 3)
        st.session_state.reminder_days = reminder_days

    with tab_db:
        st.markdown('<div class="sh">Database Status</div>', unsafe_allow_html=True)
        stats = database.get_overall_stats()
        c1, c2, c3, c4 = st.columns(4)
        with c1: mc(stats["emails"], "Emails")
        with c2: mc(stats["contacts"], "Contacts")
        with c3: mc(stats["reminders"], "Reminders")
        with c4: mc(stats["drafts"], "Drafts")

        st.markdown("")
        from pathlib import Path as P2
        db_p = P2("data/email_assistant.db")
        if db_p.exists():
            st.caption(f"📁 DB: {db_p} · {db_p.stat().st_size/1024:.1f} KB")

        col_ex, col_cl = st.columns(2)
        with col_ex:
            if st.button("📤 Export Data (JSON)", use_container_width=True):
                export = {
                    "emails": database.get_emails(limit=200),
                    "contacts": database.get_contacts(),
                    "reminders": database.get_reminders(include_done=True),
                    "follow_ups": database.get_follow_ups("pending"),
                    "exported_at": datetime.now().isoformat(),
                }
                st.download_button("⬇️ Download", data=json.dumps(export, indent=2, default=str),
                    file_name="email_assistant_backup.json", mime="application/json")
        with col_cl:
            with st.expander("⚠️ Clear Cache"):
                if st.button("🗑️ Clear email cache", type="primary"):
                    import sqlite3 as sl
                    conn2 = sl.connect("data/email_assistant.db")
                    conn2.execute("DELETE FROM emails")
                    conn2.commit()
                    conn2.close()
                    st.success("Cache cleared.")
                    st.rerun()

    with tab_about:
        st.markdown("""
<div style="background:linear-gradient(135deg,#12122A,#0E1628);border:1px solid #1E1E3A;
            border-radius:16px;padding:24px;display:grid;grid-template-columns:1fr 1fr;gap:16px;">
  <div>
    <div style="font-size:0.72rem;color:#6366F1;font-weight:700;text-transform:uppercase;">Application</div>
    <div style="color:#E2E8F0;font-weight:600;margin-top:3px;">Personal Email Assistant Agent</div>
    <div style="color:#4B5563;font-size:0.8rem;">v1.0.0</div>
  </div>
  <div>
    <div style="font-size:0.72rem;color:#6366F1;font-weight:700;text-transform:uppercase;">AI Engine</div>
    <div style="color:#E2E8F0;font-weight:600;margin-top:3px;">OpenAI GPT-4o</div>
    <div style="color:#4B5563;font-size:0.8rem;">12 specialized prompts</div>
  </div>
  <div>
    <div style="font-size:0.72rem;color:#6366F1;font-weight:700;text-transform:uppercase;">Integrations</div>
    <div style="color:#E2E8F0;font-weight:600;margin-top:3px;">Gmail · Google Calendar</div>
    <div style="color:#4B5563;font-size:0.8rem;">OAuth 2.0 · REST APIs</div>
  </div>
  <div>
    <div style="font-size:0.72rem;color:#6366F1;font-weight:700;text-transform:uppercase;">Storage</div>
    <div style="color:#E2E8F0;font-weight:600;margin-top:3px;">SQLite (local)</div>
    <div style="color:#4B5563;font-size:0.8rem;">7 tables · zero config</div>
  </div>
</div>""", unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<hr style='border-color:#1E1E3A;margin-top:40px;'>
<div style='text-align:center;font-size:0.7rem;color:#1F2937;padding-bottom:16px;'>
  ✉️ Personal Email Assistant · GPT-4o · Gmail API · Streamlit
</div>
""", unsafe_allow_html=True)
