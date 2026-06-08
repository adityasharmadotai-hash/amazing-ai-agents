"""
app.py — Founder Daily Brief Agent
An AI executive dashboard that pulls Gmail, Calendar, Notion, Slack & revenue into
one daily briefing so founders stop checking 7 tools every morning.

10 pages: Daily Brief · Inbox · Calendar · Notion · Slack · Revenue ·
          AI Insights · Analytics · Ask · Settings
"""

import os, sys, time
from datetime import datetime, timedelta

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(page_title="Founder Daily Brief", page_icon="☀️", layout="wide",
                   initial_sidebar_state="expanded")

# ── Styles ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
html,body,[class*="css"]{ font-family:'Inter',sans-serif; }

[data-testid="stSidebar"]{ background:linear-gradient(180deg,#06121a 0%,#0a1722 55%,#071019 100%) !important; }
[data-testid="stSidebar"]>div:first-child{ background:transparent !important; }
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,[data-testid="stSidebar"] label{ color:#e2e8f0 !important; }
[data-testid="stSidebar"] .stButton>button{
    background:rgba(255,255,255,0.06) !important; border:1px solid rgba(255,255,255,0.1) !important;
    border-radius:10px !important; color:#cbd5e1 !important; font-size:14px !important;
    font-weight:500 !important; padding:10px 14px !important; width:100% !important;
    margin:2px 0 !important; text-align:left !important; transition:all 0.18s !important;
}
[data-testid="stSidebar"] .stButton>button p{ color:#cbd5e1 !important; }
[data-testid="stSidebar"] .stButton>button:hover{
    background:rgba(13,148,136,0.28) !important; border-color:rgba(13,148,136,0.5) !important; color:white !important;
}
[data-testid="stSidebar"] .nav-active>button{
    background:linear-gradient(135deg,#0d9488,#0ea5e9) !important;
    border-left:4px solid #5eead4 !important;
    color:white !important; font-weight:700 !important;
    box-shadow:0 4px 18px rgba(13,148,136,0.45) !important; transform:translateX(3px) !important;
}
[data-testid="stSidebar"] .nav-active>button p{ color:white !important; }
.nav-div{ height:1px; background:rgba(255,255,255,0.08); margin:10px 0; }

/* Cards */
.card{background:white;border:1px solid #e2e8f0;border-radius:16px;padding:20px;
      box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:12px;transition:all 0.2s;}
.card:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(0,0,0,0.1);}
.metric-card{background:white;border-radius:14px;padding:18px;text-align:center;
             border:1px solid #e2e8f0;box-shadow:0 2px 6px rgba(0,0,0,0.05);}
.metric-val{font-size:28px;font-weight:900;color:#0f172a;}
.metric-lbl{font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;margin-top:4px;}

/* Priority badges */
.p-high{background:#fef2f2;color:#dc2626;border:1px solid #fecaca;padding:2px 9px;border-radius:11px;font-size:10px;font-weight:700;}
.p-medium{background:#fffbeb;color:#d97706;border:1px solid #fde68a;padding:2px 9px;border-radius:11px;font-size:10px;font-weight:700;}
.p-low{background:#f0fdf4;color:#16a34a;border:1px solid #bbf7d0;padding:2px 9px;border-radius:11px;font-size:10px;font-weight:700;}
.chip{display:inline-block;background:#f1f5f9;color:#475569;border:1px solid #e2e8f0;padding:2px 9px;border-radius:11px;font-size:10px;font-weight:600;margin:2px;}

/* Section header */
.sec-hdr{background:linear-gradient(90deg,#0d9488,#0ea5e9);color:white;border-radius:10px;
         padding:11px 18px;margin:18px 0 12px;font-size:14px;font-weight:600;}

/* List rows */
.row{background:white;border:1px solid #e2e8f0;border-radius:12px;padding:13px 16px;margin:6px 0;}
.row-l{border-left:4px solid #0d9488;}
.row-red{border-left:4px solid #ef4444;}
.row-amber{border-left:4px solid #f59e0b;}

/* Brief hero */
.brief-hero{background:linear-gradient(135deg,#0d9488,#0ea5e9);border-radius:18px;padding:28px 32px;color:white;
            box-shadow:0 10px 30px rgba(13,148,136,0.35);margin-bottom:18px;}
.brief-hero h1{font-size:30px;font-weight:800;margin:0;color:white;}
.brief-hero p{font-size:14px;color:rgba(255,255,255,0.9);margin-top:6px;}

/* Page header */
.page-hdr{padding:4px 0 18px;}
.page-hdr h1{font-size:26px;font-weight:800;color:#0f172a;margin:0;}
.page-hdr p{color:#64748b;font-size:14px;margin-top:5px;}

/* Inputs */
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{
    border-radius:10px !important; border:2px solid #e2e8f0 !important;}
[data-testid="stTextInput"] input:focus,[data-testid="stTextArea"] textarea:focus{border-color:#0d9488 !important;}
.stTabs [data-baseweb="tab-list"]{background:#f1f5f9;border-radius:10px;padding:3px;gap:2px;}
.stTabs [data-baseweb="tab"]{border-radius:8px;font-weight:500;font-size:13px;}
.stTabs [aria-selected="true"]{background:white !important;box-shadow:0 1px 4px rgba(0,0,0,0.1);}
#MainMenu,footer{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

from modules import connectors as cx
from modules import brief as bf
from modules import ai
from modules.storage import init_profile, get_profile, update_profile, get_connections, toggle_connection

init_profile()
cx.init_connectors()

if "page" not in st.session_state:
    st.session_state.page = "☀️ Daily Brief"


def _sync_key():
    k = ai.get_key()
    if k:
        os.environ["OPENAI_API_KEY"] = k
_sync_key()


def fmt_money(x):
    cur = get_profile().get("currency", "$")
    try:
        return f"{cur}{x:,.0f}"
    except Exception:
        return f"{cur}{x}"


def ago(iso):
    try:
        delta = datetime.now() - datetime.fromisoformat(iso)
        h = delta.total_seconds() / 3600
        if h < 1:
            return f"{int(delta.total_seconds()/60)}m ago"
        if h < 24:
            return f"{int(h)}h ago"
        return f"{int(h/24)}d ago"
    except Exception:
        return ""


PCSS = {"high": "p-high", "medium": "p-medium", "low": "p-low"}
CAT_ICON = {"Customer": "🎧", "Sales": "💼", "Team": "👥", "Finance": "💳",
            "Personal": "👤", "Newsletter": "📰"}

NAV = [
    ("☀️", "Daily Brief"), ("📧", "Inbox"), ("📅", "Calendar"), ("📝", "Notion"),
    ("💬", "Slack"), ("💰", "Revenue"), ("🧠", "AI Insights"), ("📊", "Analytics"),
    ("🔍", "Ask"), ("🔑", "Settings"),
]


# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    prof = get_profile()
    st.markdown(f"""
    <div style="padding:18px 4px 14px;text-align:center;">
        <div style="width:54px;height:54px;background:linear-gradient(135deg,#0d9488,#0ea5e9);
                    border-radius:14px;margin:0 auto;display:flex;align-items:center;
                    justify-content:center;font-size:26px;box-shadow:0 4px 14px rgba(13,148,136,0.4);">☀️</div>
        <div style="font-size:15px;font-weight:800;color:white;margin-top:9px;">Founder Brief</div>
        <div style="font-size:11px;color:#64748b;margin-top:2px;">{prof.get('company','')}</div>
    </div>
    <div class="nav-div"></div>
    <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:0.1em;font-weight:600;padding:0 4px;margin-bottom:6px;">Navigation</div>
    """, unsafe_allow_html=True)

    current = st.session_state.get("page", "☀️ Daily Brief")
    for icon, label in NAV:
        full = f"{icon} {label}"
        active = (current == full)
        if active:
            st.markdown('<div class="nav-active">', unsafe_allow_html=True)
        btn_lbl = f"✦  {icon}  {label}" if active else f"{icon}  {label}"
        if st.button(btn_lbl, key=f"nav_{label}", use_container_width=True):
            st.session_state.page = full
            st.rerun()
        if active:
            st.markdown("</div>", unsafe_allow_html=True)

    page = st.session_state.get("page", "☀️ Daily Brief")

    # quick status
    ihs = cx.inbox_health_score()
    rev = cx.revenue_yesterday()
    st.markdown(f"""
    <div class="nav-div"></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;padding:0 2px;">
        <div style="background:rgba(13,148,136,0.15);border:1px solid rgba(13,148,136,0.3);border-radius:8px;padding:8px;text-align:center;">
            <div style="font-size:18px;font-weight:700;color:white;">{ihs}</div>
            <div style="font-size:10px;color:#64748b;">Inbox Health</div>
        </div>
        <div style="background:rgba(13,148,136,0.15);border:1px solid rgba(13,148,136,0.3);border-radius:8px;padding:8px;text-align:center;">
            <div style="font-size:16px;font-weight:700;color:#22c55e;">{fmt_money(rev)}</div>
            <div style="font-size:10px;color:#64748b;">Rev. Yesterday</div>
        </div>
    </div>
    <div class="nav-div"></div>
    <div style="font-size:10px;color:#475569;text-align:center;">{'🟢 AI connected' if ai.is_configured() else '⚪ AI off — add key in Settings'}</div>
    <div style="font-size:11px;color:#334155;text-align:center;padding:8px 0 4px;">
        Built with ❤️ by <a href="https://www.adityasharma.ai" target="_blank" style="color:#5eead4;text-decoration:none;">adityasharma.ai</a>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DAILY BRIEF
# ══════════════════════════════════════════════════════════════════════════════
if page == "☀️ Daily Brief":
    prof = get_profile()
    ctx = cx.collect_context()

    if st.session_state.get("last_brief") is None:
        st.session_state.last_brief = bf.generate_brief(prof["founder_name"], ctx)
    brief = st.session_state.last_brief
    m = brief["metrics"]

    # Hero
    st.markdown(f"""
    <div class="brief-hero">
        <h1>{brief['greeting']} 👋</h1>
        <p>{datetime.now().strftime('%A, %B %d, %Y')} &nbsp;·&nbsp; Your day across Gmail, Calendar, Notion, Slack & revenue</p>
    </div>""", unsafe_allow_html=True)

    hc1, hc2 = st.columns([4, 1])
    with hc2:
        if st.button("🔄 Regenerate", use_container_width=True):
            with st.spinner("Rebuilding your brief..."):
                st.session_state.last_brief = bf.generate_brief(prof["founder_name"], cx.collect_context())
            st.rerun()

    # Headline metrics
    cols = st.columns(6)
    cards = [
        ("📅", m["meetings"], "Meetings Today", "#0ea5e9"),
        ("📧", m["important_emails"], "Important Emails", "#6366f1"),
        ("↩️", m["followups"], "Pending Follow-Ups", "#f59e0b"),
        ("🎧", m["customer_issues"], "Customer Issues", "#ef4444"),
        ("✅", m["open_actions"], "Open Actions", "#0d9488"),
        ("💰", fmt_money(m["revenue_yesterday"]), "Revenue Yesterday", "#22c55e"),
    ]
    for col, (icon, val, lbl, color) in zip(cols, cards):
        with col:
            st.markdown(f"""<div class="metric-card" style="border-top:3px solid {color};">
                <div style="font-size:20px;">{icon}</div>
                <div class="metric-val" style="color:{color};font-size:24px;">{val}</div>
                <div class="metric-lbl">{lbl}</div></div>""", unsafe_allow_html=True)

    # Summary + suggested focus
    bcol1, bcol2 = st.columns([3, 2])
    with bcol1:
        st.markdown('<div class="sec-hdr">📋 Executive Summary</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="card"><p style="font-size:15px;color:#374151;line-height:1.7;margin:0;">{brief["summary"]}</p></div>', unsafe_allow_html=True)

        st.markdown('<div class="sec-hdr">🌟 Highlights</div>', unsafe_allow_html=True)
        for h in brief.get("highlights", []):
            st.markdown(f'<div class="row row-l"><span style="font-size:14px;color:#374151;">✦ {h}</span></div>', unsafe_allow_html=True)

    with bcol2:
        st.markdown('<div class="sec-hdr">🎯 Suggested Focus</div>', unsafe_allow_html=True)
        st.markdown(f"""<div style="background:linear-gradient(135deg,#0d948815,#0ea5e910);
            border:2px solid #0d948840;border-radius:14px;padding:20px;">
            <div style="font-size:15px;color:#0f172a;line-height:1.7;font-weight:500;">{brief["suggested_focus"]}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="sec-hdr">⚠️ Watch Outs</div>', unsafe_allow_html=True)
        for w in brief.get("watch_outs", []):
            st.markdown(f'<div class="row row-red"><span style="font-size:13px;color:#374151;">{w}</span></div>', unsafe_allow_html=True)

    src = "🤖 Generated by GPT-4o" if brief.get("ai") else "⚙️ Rule-based brief — add an OpenAI key in Settings for AI narrative"
    st.caption(f"{src} · {brief.get('generated_at','')[:16].replace('T',' ')}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: INBOX
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📧 Inbox":
    st.markdown('<div class="page-hdr"><h1>📧 Inbox</h1><p>Gmail — important emails, follow-ups, and priority triage</p></div>', unsafe_allow_html=True)

    emails = cx.get_emails()
    k1, k2, k3, k4 = st.columns(4)
    for col, val, lbl, color in [
        (k1, len(cx.unread_emails()), "Unread", "#6366f1"),
        (k2, len(cx.important_emails()), "Important", "#ef4444"),
        (k3, len(cx.pending_followups()), "Need Follow-Up", "#f59e0b"),
        (k4, f"{cx.inbox_health_score()}/100", "Inbox Health", "#0d9488"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card" style="border-top:3px solid {color};"><div class="metric-val" style="color:{color};">{val}</div><div class="metric-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    fc1, fc2 = st.columns([3, 2])
    with fc1:
        search = st.text_input("Search", placeholder="🔍 Search sender or subject...", label_visibility="collapsed")
    with fc2:
        flt = st.selectbox("Filter", ["All", "Unread", "Important", "Needs Follow-Up", "Customer Issues"], label_visibility="collapsed")

    rows = emails
    if search:
        rows = [e for e in rows if search.lower() in (e["sender"] + e["subject"] + e["snippet"]).lower()]
    if flt == "Unread":
        rows = [e for e in rows if e["unread"]]
    elif flt == "Important":
        rows = [e for e in rows if e["priority"] == "high" or e["is_issue"]]
    elif flt == "Needs Follow-Up":
        rows = [e for e in rows if e["needs_followup"]]
    elif flt == "Customer Issues":
        rows = [e for e in rows if e["is_issue"]]

    st.caption(f"{len(rows)} email(s)")
    for e in rows:
        border = "row-red" if e["is_issue"] else ("row-amber" if e["needs_followup"] else "row-l")
        dot = "🔵 " if e["unread"] else ""
        tags = f'<span class="{PCSS[e["priority"]]}">{e["priority"].upper()}</span> '
        tags += f'<span class="chip">{CAT_ICON.get(e["category"],"📩")} {e["category"]}</span> '
        if e["needs_followup"]:
            tags += '<span class="chip">↩️ Follow-up</span> '
        if e["is_issue"]:
            tags += '<span class="chip">🚨 Issue</span>'
        st.markdown(f"""<div class="row {border}">
            <div style="display:flex;justify-content:space-between;align-items:start;">
                <div style="font-weight:700;color:#0f172a;font-size:14px;">{dot}{e['subject']}</div>
                <div style="font-size:11px;color:#94a3b8;white-space:nowrap;margin-left:10px;">{ago(e['received'])}</div>
            </div>
            <div style="font-size:12px;color:#64748b;margin:3px 0;">{e['sender']} &lt;{e['sender_email']}&gt;</div>
            <div style="font-size:13px;color:#475569;line-height:1.5;margin-bottom:8px;">{e['snippet']}</div>
            <div>{tags}</div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: CALENDAR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📅 Calendar":
    st.markdown('<div class="page-hdr"><h1>📅 Calendar</h1><p>Google Calendar — today\'s schedule with AI meeting prep</p></div>', unsafe_allow_html=True)

    meetings = cx.get_today_meetings()
    ctx = cx.collect_context()

    k1, k2, k3 = st.columns(3)
    for col, val, lbl, color in [
        (k1, len(meetings), "Meetings Today", "#0ea5e9"),
        (k2, f"{cx.meeting_load_hours()}h", "Meeting Load", "#6366f1"),
        (k3, sum(len(m["attendees"]) for m in meetings), "Total Attendees", "#0d9488"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card" style="border-top:3px solid {color};"><div class="metric-val" style="color:{color};">{val}</div><div class="metric-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="sec-hdr">🗓️ Today\'s Schedule</div>', unsafe_allow_html=True)
    if not meetings:
        st.info("No meetings today — protect that deep work time. 🧘")
    for mtg in meetings:
        t1 = mtg["start"][11:16]
        t2 = mtg["end"][11:16]
        with st.expander(f"🕐 {t1}–{t2}  ·  {mtg['title']}  ·  {mtg['type']}"):
            st.markdown(f"""<div style="font-size:13px;color:#475569;line-height:1.8;">
                <strong>👥 Attendees:</strong> {', '.join(mtg['attendees'])}<br>
                <strong>📍 Location:</strong> {mtg['location']}<br>
                <strong>📝 Notes:</strong> {mtg.get('notes','—')}
            </div>""", unsafe_allow_html=True)
            prep_key = f"prepbrief_{mtg['id']}"
            if st.button("🧠 Generate AI Prep Brief", key=f"prep_{mtg['id']}"):
                with st.spinner("Preparing..."):
                    st.session_state[prep_key] = bf.meeting_prep(mtg, ctx)
            if prep_key in st.session_state:
                st.markdown(f'<div class="card" style="border-left:4px solid #0d9488;">{st.session_state[prep_key]}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: NOTION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📝 Notion":
    st.markdown('<div class="page-hdr"><h1>📝 Notion</h1><p>Tasks, projects, and action items from your workspace</p></div>', unsafe_allow_html=True)

    tasks = cx.get_tasks()
    open_t = cx.get_open_tasks()
    k1, k2, k3, k4 = st.columns(4)
    for col, val, lbl, color in [
        (k1, len(open_t), "Open Tasks", "#0d9488"),
        (k2, sum(1 for t in tasks if t["status"] == "Blocked"), "Blocked", "#ef4444"),
        (k3, sum(1 for t in tasks if t["priority"] == "high" and t["status"] != "Done"), "High Priority", "#f59e0b"),
        (k4, f"{cx.task_completion_rate()}%", "Completion", "#22c55e"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card" style="border-top:3px solid {color};"><div class="metric-val" style="color:{color};">{val}</div><div class="metric-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    with st.expander("➕ Add a task"):
        with st.form("add_task", clear_on_submit=True):
            a1, a2, a3 = st.columns([3, 2, 1])
            with a1:
                t_title = st.text_input("Title", placeholder="What needs doing?")
            with a2:
                t_proj = st.text_input("Project", placeholder="Project / area")
            with a3:
                t_pri = st.selectbox("Priority", ["high", "medium", "low"])
            t_due = st.date_input("Due", value=datetime.now().date())
            if st.form_submit_button("Add Task ➕", type="primary") and t_title:
                cx.add_task(t_title, t_proj or "General", t_pri,
                            datetime.combine(t_due, datetime.min.time()).isoformat())
                st.success("Added!")
                st.rerun()

    STATUS_ORDER = ["Blocked", "In Progress", "Open", "Done"]
    SICON = {"Open": "⬜", "In Progress": "🔵", "Blocked": "🔴", "Done": "✅"}
    flt = st.selectbox("Show", ["All open", "Everything", "Blocked", "High priority"], label_visibility="collapsed")

    view = tasks
    if flt == "All open":
        view = [t for t in tasks if t["status"] != "Done"]
    elif flt == "Blocked":
        view = [t for t in tasks if t["status"] == "Blocked"]
    elif flt == "High priority":
        view = [t for t in tasks if t["priority"] == "high"]

    view = sorted(view, key=lambda t: (STATUS_ORDER.index(t["status"]) if t["status"] in STATUS_ORDER else 9,
                                       {"high": 0, "medium": 1, "low": 2}.get(t["priority"], 3)))

    for t in view:
        due_dt = datetime.fromisoformat(t["due"]).date()
        overdue = due_dt < datetime.now().date() and t["status"] != "Done"
        due_txt = f"{'🔴 Overdue · ' if overdue else '📅 '}{due_dt.strftime('%b %d')}"
        border = "row-red" if t["status"] == "Blocked" else ("row-amber" if t["priority"] == "high" else "row-l")
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f"""<div class="row {border}">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="font-weight:600;color:#0f172a;font-size:14px;">{SICON.get(t['status'],'⬜')} {t['title']}</div>
                    <span class="{PCSS[t['priority']]}">{t['priority'].upper()}</span>
                </div>
                <div style="font-size:12px;color:#64748b;margin-top:4px;">
                    <span class="chip">📁 {t['project']}</span> <span class="chip">{t['status']}</span> {due_txt}
                </div>
            </div>""", unsafe_allow_html=True)
        with c2:
            if t["status"] != "Done":
                if st.button("✅ Done", key=f"done_{t['id']}", use_container_width=True):
                    cx.set_task_status(t["id"], "Done")
                    st.rerun()
            else:
                if st.button("↩️ Reopen", key=f"reopen_{t['id']}", use_container_width=True):
                    cx.set_task_status(t["id"], "Open")
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SLACK
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💬 Slack":
    st.markdown('<div class="page-hdr"><h1>💬 Slack</h1><p>Mentions, unanswered messages, and team discussions</p></div>', unsafe_allow_html=True)

    msgs = cx.get_slack()
    k1, k2, k3 = st.columns(3)
    for col, val, lbl, color in [
        (k1, len(cx.slack_mentions()), "Mentions", "#6366f1"),
        (k2, len(cx.unanswered_slack()), "Unanswered", "#f59e0b"),
        (k3, sum(1 for m in msgs if m["important"]), "Important", "#ef4444"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card" style="border-top:3px solid {color};"><div class="metric-val" style="color:{color};">{val}</div><div class="metric-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    flt = st.selectbox("Filter", ["All", "Mentions", "Unanswered", "Important"], label_visibility="collapsed")
    view = msgs
    if flt == "Mentions":
        view = [m for m in msgs if m["mention"]]
    elif flt == "Unanswered":
        view = [m for m in msgs if m["unanswered"]]
    elif flt == "Important":
        view = [m for m in msgs if m["important"]]

    for m in view:
        border = "row-red" if m["important"] and m["unanswered"] else ("row-amber" if m["unanswered"] else "row-l")
        tags = ""
        if m["mention"]:
            tags += '<span class="chip">@ Mention</span> '
        if m["unanswered"]:
            tags += '<span class="chip">💬 Unanswered</span> '
        if m["important"]:
            tags += '<span class="chip">⭐ Important</span>'
        st.markdown(f"""<div class="row {border}">
            <div style="display:flex;justify-content:space-between;">
                <div style="font-weight:700;color:#0d9488;font-size:13px;">{m['channel']} · {m['user']}</div>
                <div style="font-size:11px;color:#94a3b8;">{ago(m['ts'])}</div>
            </div>
            <div style="font-size:14px;color:#374151;margin:5px 0 8px;">{m['text']}</div>
            <div>{tags}</div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: REVENUE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💰 Revenue":
    import plotly.graph_objects as go
    st.markdown('<div class="page-hdr"><h1>💰 Revenue</h1><p>Stripe & Razorpay — MRR, trends, and manual entries</p></div>', unsafe_allow_html=True)

    rev = cx.get_revenue()
    k1, k2, k3, k4 = st.columns(4)
    for col, val, lbl, color in [
        (k1, fmt_money(cx.revenue_yesterday()), "Yesterday", "#22c55e"),
        (k2, fmt_money(cx.revenue_last_n_days(7)), "Last 7 Days", "#0ea5e9"),
        (k3, fmt_money(cx.revenue_last_n_days(30)), "Last 30 Days", "#0d9488"),
        (k4, fmt_money(cx.estimated_mrr()), "Est. MRR", "#6366f1"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card" style="border-top:3px solid {color};"><div class="metric-val" style="color:{color};font-size:22px;">{val}</div><div class="metric-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    # Trend chart — last 14 days
    st.markdown('<div class="sec-hdr">📈 Revenue Trend (14 days)</div>', unsafe_allow_html=True)
    days = [(datetime.now().date() - timedelta(days=i)) for i in range(13, -1, -1)]
    totals = []
    for d in days:
        tot = sum(r["amount"] for r in rev if cx._safe_dt(r["date"]) and cx._safe_dt(r["date"]).date() == d)
        totals.append(tot)
    fig = go.Figure(go.Bar(x=[d.strftime("%b %d") for d in days], y=totals,
                           marker_color="#0d9488", marker_line_width=0))
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=280,
                      margin=dict(l=10, r=10, t=10, b=10),
                      yaxis=dict(showgrid=True, gridcolor="#f1f5f9", title="Revenue"))
    st.plotly_chart(fig, use_container_width=True)

    cc1, cc2 = st.columns([2, 3])
    with cc1:
        st.markdown('<div class="sec-hdr">➕ Add Revenue</div>', unsafe_allow_html=True)
        with st.form("add_rev", clear_on_submit=True):
            r_amt = st.number_input("Amount", min_value=0.0, step=50.0, value=100.0)
            r_cust = st.text_input("Customer", placeholder="Acme Corp")
            r_src = st.selectbox("Source", ["Stripe", "Razorpay", "Manual"])
            r_type = st.selectbox("Type", ["subscription", "one-time"])
            r_date = st.date_input("Date", value=datetime.now().date())
            if st.form_submit_button("Add Entry 💰", type="primary"):
                cx.add_revenue(r_amt, r_src, r_cust or "—", r_type,
                               datetime.combine(r_date, datetime.min.time()).isoformat())
                st.success("Added!")
                st.rerun()

    with cc2:
        st.markdown('<div class="sec-hdr">🧾 Recent Transactions</div>', unsafe_allow_html=True)
        SRC_ICON = {"Stripe": "💳", "Razorpay": "🇮🇳", "Manual": "✍️"}
        for r in rev[:12]:
            d = cx._safe_dt(r["date"])
            dt_txt = d.strftime("%b %d") if d else ""
            rc1, rc2 = st.columns([6, 1])
            with rc1:
                st.markdown(f"""<div class="row row-l" style="margin:4px 0;padding:10px 14px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div><span style="font-weight:700;color:#0f172a;">{fmt_money(r['amount'])}</span>
                            <span style="font-size:12px;color:#64748b;margin-left:8px;">{r['customer']}</span></div>
                        <div style="font-size:11px;color:#94a3b8;">{SRC_ICON.get(r['source'],'')} {r['source']} · {r['type']} · {dt_txt}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            with rc2:
                if st.button("🗑️", key=f"delrev_{r['id']}", use_container_width=True):
                    cx.delete_revenue(r["id"])
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AI INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🧠 AI Insights":
    st.markdown('<div class="page-hdr"><h1>🧠 AI Insights</h1><p>Priorities, risks, opportunities, and recommended next actions</p></div>', unsafe_allow_html=True)

    ctx = cx.collect_context()
    cta1, cta2 = st.columns([4, 1])
    with cta2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.pop("last_insights", None)
            st.rerun()

    if st.session_state.get("last_insights") is None:
        with st.spinner("Analysing your day..."):
            st.session_state.last_insights = bf.generate_insights(ctx)
    ins = st.session_state.last_insights

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sec-hdr">🎯 Top Priorities</div>', unsafe_allow_html=True)
        for i, p in enumerate(ins.get("priorities", []), 1):
            st.markdown(f"""<div class="row row-l">
                <div style="font-weight:700;color:#0f172a;font-size:14px;">{i}. {p.get('title','')}</div>
                <div style="font-size:12px;color:#64748b;margin-top:3px;">{p.get('why','')}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="sec-hdr">⚠️ Risks</div>', unsafe_allow_html=True)
        for r in ins.get("risks", []):
            st.markdown(f"""<div class="row row-red">
                <div style="font-weight:700;color:#0f172a;font-size:14px;">{r.get('title','')}</div>
                <div style="font-size:12px;color:#64748b;margin-top:3px;">{r.get('detail','')}</div>
            </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="sec-hdr">🚀 Opportunities</div>', unsafe_allow_html=True)
        for o in ins.get("opportunities", []):
            st.markdown(f"""<div class="row" style="border-left:4px solid #22c55e;">
                <div style="font-weight:700;color:#0f172a;font-size:14px;">{o.get('title','')}</div>
                <div style="font-size:12px;color:#64748b;margin-top:3px;">{o.get('detail','')}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="sec-hdr">↩️ Follow-Up Recommendations</div>', unsafe_allow_html=True)
        for f in ins.get("followups", []):
            st.markdown(f"""<div class="row row-amber">
                <div style="font-weight:700;color:#0f172a;font-size:14px;">{f.get('who','')}</div>
                <div style="font-size:12px;color:#64748b;margin-top:3px;">{f.get('action','')}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sec-hdr">✅ Recommended Next Actions</div>', unsafe_allow_html=True)
    acols = st.columns(2)
    for i, a in enumerate(ins.get("next_actions", [])):
        with acols[i % 2]:
            st.markdown(f'<div class="row row-l"><span style="font-size:14px;color:#374151;">▢ {a}</span></div>', unsafe_allow_html=True)

    st.caption("🤖 Generated by GPT-4o" if ins.get("ai") else "⚙️ Rule-based insights — add an OpenAI key in Settings for deeper analysis")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Analytics":
    import plotly.graph_objects as go
    st.markdown('<div class="page-hdr"><h1>📊 Analytics</h1><p>Health scores, productivity, and workload at a glance</p></div>', unsafe_allow_html=True)

    ihs = cx.inbox_health_score()
    prod = cx.productivity_score()
    tcr = cx.task_completion_rate()
    load = cx.meeting_load_hours()
    fu = cx.followup_status()

    k1, k2, k3, k4, k5 = st.columns(5)
    for col, val, lbl, color in [
        (k1, f"{ihs}", "Inbox Health", "#0d9488"),
        (k2, f"{prod}", "Productivity", "#6366f1"),
        (k3, f"{tcr}%", "Task Completion", "#22c55e"),
        (k4, f"{load}h", "Meeting Load", "#0ea5e9"),
        (k5, fu["pending"], "Follow-Ups Due", "#f59e0b"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card" style="border-top:3px solid {color};"><div class="metric-val" style="color:{color};">{val}</div><div class="metric-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        st.markdown('<div class="sec-hdr">🩺 Health Scores</div>', unsafe_allow_html=True)
        fig = go.Figure(go.Bar(
            x=[ihs, prod, tcr], y=["Inbox Health", "Productivity", "Task Completion"],
            orientation="h", marker_color=["#0d9488", "#6366f1", "#22c55e"], marker_line_width=0))
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=240,
                          margin=dict(l=10, r=10, t=10, b=10),
                          xaxis=dict(range=[0, 100], showgrid=True, gridcolor="#f1f5f9"))
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        st.markdown('<div class="sec-hdr">📋 Task Status Breakdown</div>', unsafe_allow_html=True)
        tasks = cx.get_tasks()
        sc = {}
        for t in tasks:
            sc[t["status"]] = sc.get(t["status"], 0) + 1
        SC = {"Open": "#94a3b8", "In Progress": "#0ea5e9", "Blocked": "#ef4444", "Done": "#22c55e"}
        fig2 = go.Figure(go.Pie(labels=list(sc.keys()), values=list(sc.values()),
                                marker_colors=[SC.get(k, "#0d9488") for k in sc], hole=0.45,
                                textinfo="label+value"))
        fig2.update_layout(margin=dict(l=0, r=0, t=10, b=10), height=240, paper_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="sec-hdr">💰 Revenue by Source</div>', unsafe_allow_html=True)
    rev = cx.get_revenue()
    by_src = {}
    for r in rev:
        by_src[r["source"]] = by_src.get(r["source"], 0) + r["amount"]
    if by_src:
        fig3 = go.Figure(go.Bar(x=list(by_src.keys()), y=list(by_src.values()),
                                marker_color="#0ea5e9", marker_line_width=0))
        fig3.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=240,
                           margin=dict(l=10, r=10, t=10, b=10),
                           yaxis=dict(showgrid=True, gridcolor="#f1f5f9", title="Total"))
        st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ASK (Search Assistant)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Ask":
    st.markdown('<div class="page-hdr"><h1>🔍 Ask Your Day</h1><p>Natural-language assistant over your inbox, calendar, tasks, Slack & revenue</p></div>', unsafe_allow_html=True)

    ctx = cx.collect_context()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.markdown('<div class="sec-hdr">💡 Try asking</div>', unsafe_allow_html=True)
    suggestions = [
        "What needs my attention today?",
        "Which clients need follow-up?",
        "What meetings do I have today?",
        "What are the biggest risks this week?",
        "Show revenue summary.",
    ]
    scols = st.columns(len(suggestions))
    clicked = None
    for col, s in zip(scols, suggestions):
        with col:
            if st.button(s, key=f"sg_{s}", use_container_width=True):
                clicked = s

    q = st.chat_input("Ask anything about your day...")
    question = clicked or q
    if question:
        st.session_state.chat_history.append(("user", question))
        with st.spinner("Thinking..."):
            answer = bf.ask(question, ctx)
        st.session_state.chat_history.append(("assistant", answer))

    for role, text in st.session_state.chat_history:
        with st.chat_message("user" if role == "user" else "assistant",
                             avatar="🧑‍💼" if role == "user" else "☀️"):
            st.markdown(text)

    if st.session_state.chat_history:
        if st.button("🗑️ Clear conversation"):
            st.session_state.chat_history = []
            st.rerun()
    else:
        st.info("👋 Ask a question above, or tap one of the suggestions. "
                + ("AI answers are live." if ai.is_configured() else "Add an OpenAI key in Settings for smarter answers."))


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔑 Settings":
    st.markdown('<div class="page-hdr"><h1>🔑 Settings</h1><p>Profile, connections, and your OpenAI API key</p></div>', unsafe_allow_html=True)

    # API key status
    if ai.is_configured():
        src = "Your key" if st.session_state.get("user_api_key", "").strip() else "Server-configured"
        st.markdown(f"""<div style="background:#f0fdf4;border:2px solid #86efac;border-radius:12px;padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px;">
            <div style="font-size:24px;">🟢</div>
            <div><div style="font-weight:700;color:#15803d;">AI Active — smart briefs, insights & answers enabled</div>
            <div style="font-size:12px;color:#166534;">Source: {src}</div></div></div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="background:#fffbeb;border:2px solid #fde68a;border-radius:12px;padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px;">
            <div style="font-size:24px;">⚪</div>
            <div><div style="font-weight:700;color:#b45309;">Running in rule-based mode</div>
            <div style="font-size:12px;color:#92400e;">The app works fully without a key. Add one below for GPT-4o-powered briefs.</div></div></div>""", unsafe_allow_html=True)

    s1, s2 = st.columns([3, 2])
    with s1:
        st.markdown('<div class="sec-hdr">🔑 OpenAI API Key</div>', unsafe_allow_html=True)
        entered = st.text_input("Key", value=st.session_state.get("user_api_key", ""),
                                type="password", placeholder="sk-proj-...", label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Save Key", type="primary", use_container_width=True):
                if entered.strip().startswith("sk-"):
                    st.session_state.user_api_key = entered.strip()
                    os.environ["OPENAI_API_KEY"] = entered.strip()
                    st.session_state.pop("last_brief", None)
                    st.session_state.pop("last_insights", None)
                    st.success("✅ Key saved!")
                    st.rerun()
                elif entered.strip():
                    st.error("Keys must start with 'sk-'")
                else:
                    st.error("Please enter a key.")
        with c2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.user_api_key = ""
                os.environ.pop("OPENAI_API_KEY", None)
                st.rerun()
        st.markdown("""<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:12px 14px;margin-top:10px;font-size:12px;color:#78350f;">
            🔒 Stored in your browser session only — never saved to any server or database. Cleared on tab close.</div>""", unsafe_allow_html=True)

        st.markdown('<div class="sec-hdr">👤 Founder Profile</div>', unsafe_allow_html=True)
        prof = get_profile()
        with st.form("profile_form"):
            pf1, pf2 = st.columns(2)
            with pf1:
                f_name = st.text_input("Founder Name", value=prof["founder_name"])
                f_role = st.text_input("Role", value=prof["role"])
            with pf2:
                f_co = st.text_input("Company", value=prof["company"])
                f_cur = st.selectbox("Currency", ["$", "₹", "€", "£"],
                                     index=["$", "₹", "€", "£"].index(prof.get("currency", "$")))
            if st.form_submit_button("💾 Save Profile", type="primary", use_container_width=True):
                update_profile(founder_name=f_name, role=f_role, company=f_co, currency=f_cur)
                st.session_state.pop("last_brief", None)
                st.success("✅ Profile saved!")
                st.rerun()

    with s2:
        st.markdown('<div class="sec-hdr">🔌 Connections</div>', unsafe_allow_html=True)
        conns = get_connections()
        for name in conns:
            cur = conns[name]
            new = st.toggle(name, value=cur, key=f"conn_{name}")
            if new != cur:
                toggle_connection(name, new)
        st.caption("Demo data is active for connected tools. Wire real OAuth in modules/connectors.py.")

        st.markdown('<div class="sec-hdr">📦 Demo Data</div>', unsafe_allow_html=True)
        if st.button("🔄 Reset demo data", use_container_width=True):
            cx.reset_demo_data()
            st.success("Demo data reset!")
            st.rerun()

        st.markdown('<div class="sec-hdr">📋 Get an API Key</div>', unsafe_allow_html=True)
        st.markdown("""<div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px;font-size:13px;color:#374151;line-height:2;">
            1. Visit <a href="https://platform.openai.com/api-keys" target="_blank" style="color:#0d9488;font-weight:600;">platform.openai.com/api-keys</a><br>
            2. Click <strong>+ Create new secret key</strong><br>
            3. Copy the key (starts with <code>sk-</code>)<br>
            4. Paste it on the left and save</div>""", unsafe_allow_html=True)
