"""
app.py — AI News Summary Agent
================================
Run: streamlit run app.py
"""
from __future__ import annotations
import os
import json
from datetime import datetime, timedelta

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AI News Agent",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

from modules import database, agent
from modules.demo_data import get_demo_articles, get_demo_digest

database.init_db()

# ═══════════════════════════════════════════════════════════════════════════════
#  GLOBAL CSS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
    background: #080B14 !important; color: #E2E8F0;
}
[data-testid="stSidebar"] {
    background: #0A0D1A !important;
    border-right: 1px solid #0F1A12;
}

/* ── Sidebar nav buttons ── */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important; border: none !important;
    color: #6B7280 !important; font-weight: 500 !important;
    text-align: left !important; border-radius: 8px !important;
    padding: 0.42rem 0.9rem !important; font-size: 0.87rem !important;
    justify-content: flex-start !important; opacity: 1 !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #0F1A12 !important; color: #D1FAE5 !important;
    opacity: 1 !important;
}

/* ── Main buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #059669, #047857) !important;
    color: white !important; border: none !important;
    border-radius: 9px !important; font-weight: 600 !important;
    padding: 0.4rem 1.2rem !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* ── News card ── */
.news-card {
    background: #0F1521; border: 1px solid #1A2438;
    border-left: 3px solid #1A2438; border-radius: 14px;
    padding: 16px 18px; margin-bottom: 10px;
    transition: border-color 0.2s, background 0.2s;
}
.news-card:hover { border-left-color: #10B981; background: #111827; }
.news-card.high   { border-left-color: #10B981; }
.news-card.medium { border-left-color: #3B82F6; }
.news-card.low    { border-left-color: #374151; }
.nc-source { font-size: 0.7rem; font-weight: 700; color: #10B981;
             text-transform: uppercase; letter-spacing: 0.08em; }
.nc-title  { font-size: 0.95rem; font-weight: 700; color: #F1F5F9;
             margin: 4px 0; line-height: 1.4; }
.nc-summary { font-size: 0.8rem; color: #64748B; line-height: 1.5; }
.nc-meta { font-size: 0.7rem; color: #374151; margin-top: 8px;
           display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }

/* ── Signal badge ── */
.sig { display: inline-block; padding: 2px 8px; border-radius: 5px;
       font-size: 0.66rem; font-weight: 700; letter-spacing: 0.05em; }
.sig-high   { background: #064E3B; color: #6EE7B7; border: 1px solid #10B98133; }
.sig-medium { background: #1E3A5F; color: #93C5FD; border: 1px solid #3B82F633; }
.sig-low    { background: #1F2937; color: #6B7280; border: 1px solid #37415133; }
.sig-neg    { background: #7F1D1D; color: #FCA5A5; border: 1px solid #EF444433; }

/* ── Metric card ── */
.mc { background: linear-gradient(135deg, #0F1521 0%, #0B1120 100%);
      border: 1px solid #1A2438; border-radius: 14px;
      padding: 18px 20px; text-align: center; }
.mc-val { font-size: 2.2rem; font-weight: 800; color: #10B981; line-height: 1; }
.mc-lbl { font-size: 0.72rem; color: #4B5563; text-transform: uppercase;
          letter-spacing: 0.06em; margin-top: 3px; }
.mc-sub { font-size: 0.82rem; color: #059669; margin-top: 2px; }

/* ── Section header ── */
.sh { font-size: 1rem; font-weight: 700; color: #E2E8F0; margin: 20px 0 10px;
      display: flex; align-items: center; gap: 8px; }
.sh::after { content: ''; flex: 1; height: 1px;
             background: linear-gradient(to right, #10B98122, transparent);
             margin-left: 10px; }

/* ── Digest card ── */
.digest-section {
    background: #0F1521; border: 1px solid #1A2438; border-radius: 12px;
    padding: 18px; margin-bottom: 12px;
}
.digest-cat { font-size: 0.72rem; font-weight: 700; color: #10B981;
              text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
.digest-headline { font-size: 1rem; font-weight: 700; color: #F1F5F9; margin-bottom: 10px; }
.takeaway { background: #0A1F14; border-left: 3px solid #10B981; padding: 10px 14px;
            border-radius: 0 8px 8px 0; font-size: 0.83rem; color: #6EE7B7; margin-top: 10px; }

/* ── Sentiment pill ── */
.sent-pos { color: #10B981; } .sent-neg { color: #EF4444; } .sent-neu { color: #64748B; }

/* ── Scrollable feed ── */
.feed-scroll { max-height: 75vh; overflow-y: auto; padding-right: 4px; }
.feed-scroll::-webkit-scrollbar { width: 3px; }
.feed-scroll::-webkit-scrollbar-thumb { background: #1A2438; border-radius: 4px; }

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"] { color: #4B5563 !important; font-size: 0.85rem !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #10B981 !important; border-bottom: 2px solid #10B981 !important;
}
/* ── Inputs ── */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
    background: #0F1521 !important; border: 1px solid #1A2438 !important;
    color: #E2E8F0 !important; border-radius: 8px !important;
}
[data-testid="stExpander"] {
    background: #0F1521 !important; border: 1px solid #1A2438 !important;
    border-radius: 10px !important;
}
[data-testid="stToggle"] label { font-size: 0.8rem !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def mc(value, label, sub=""):
    sub_h = f'<div class="mc-sub">{sub}</div>' if sub else ""
    st.markdown(f'<div class="mc"><div class="mc-val">{value}</div>'
                f'<div class="mc-lbl">{label}</div>{sub_h}</div>',
                unsafe_allow_html=True)


def sig_badge(score: float) -> str:
    s = float(score)
    if s >= 7:
        return f'<span class="sig sig-high">🔥 {s:.1f}</span>'
    elif s >= 4:
        return f'<span class="sig sig-medium">◆ {s:.1f}</span>'
    return f'<span class="sig sig-low">· {s:.1f}</span>'


def sent_badge(sentiment: str) -> str:
    icons = {"positive": ("▲", "pos"), "negative": ("▼", "neg"), "neutral": ("—", "neu")}
    icon, cls = icons.get(sentiment, ("—", "neu"))
    return f'<span class="sent-{cls}">{icon} {sentiment.title()}</span>'


def fmt_pub(pub: str) -> str:
    try:
        from dateutil import parser as dp
        dt = dp.parse(pub)
        diff = datetime.now(dt.tzinfo) - dt
        if diff.days == 0:
            h = diff.seconds // 3600
            return f"{h}h ago" if h > 0 else f"{diff.seconds // 60}m ago"
        return f"{diff.days}d ago"
    except Exception:
        return pub[:10] if pub else ""


def topic_pill(t: str) -> str:
    colors = {
        "AI": "#064E3B", "Technology": "#1E3A5F", "Finance": "#78350F",
        "Business": "#3730A3", "Science": "#1F2937", "Health": "#701A75",
        "Politics": "#7F1D1D", "Energy": "#14532D", "Crypto": "#422006",
        "World": "#1E3A5F",
    }
    bg = colors.get(t, "#1F2937")
    return f'<span style="background:{bg};color:#D1FAE5;padding:2px 8px;border-radius:10px;font-size:0.68rem;margin:2px;">{t}</span>'


def news_card_html(a: dict, show_summary: bool = True) -> str:
    score = float(a.get("signal_score", 0))
    level = "high" if score >= 7 else "medium" if score >= 4 else "low"
    topics_html = "".join(topic_pill(t) for t in a.get("topics", [])[:3])
    summary_html = f'<div class="nc-summary">{a.get("summary","")[:180]}</div>' if show_summary and a.get("summary") else ""
    source = a.get("source", "Unknown")
    pub = fmt_pub(a.get("published", a.get("fetched_at", "")))
    title = a.get("title", "")[:120]
    url = a.get("url", "#")

    return f"""
<div class="news-card {level}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">
    <div style="flex:1;min-width:0;">
      <div class="nc-source">{source}</div>
      <div class="nc-title"><a href="{url}" target="_blank" style="color:inherit;text-decoration:none;">{title}</a></div>
      {summary_html}
      <div class="nc-meta">
        {sig_badge(score)} {sent_badge(a.get('sentiment','neutral'))} 
        <span style="color:#374151;">{pub}</span>
        <span style="flex:1;">{topics_html}</span>
      </div>
    </div>
  </div>
</div>"""


def use_demo() -> bool:
    return st.session_state.get("demo_mode", True)


def current_articles(limit: int = 100, min_signal: float = 0.0, search: str = "") -> list[dict]:
    if use_demo():
        arts = get_demo_articles()
        if search:
            s = search.lower()
            arts = [a for a in arts if s in a["title"].lower() or s in a.get("summary","").lower()]
        if min_signal > 0:
            arts = [a for a in arts if float(a.get("signal_score",0)) >= min_signal]
        return arts[:limit]
    return database.get_articles(limit=limit, min_signal=min_signal, search=search)


def ai_ok() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

PAGES = {
    "📰 News Feed": "feed",
    "✨ AI Digest": "digest",
    "🔥 High Signal": "high_signal",
    "📊 Analytics": "analytics",
    "🔖 Saved Stories": "saved",
    "⚙️ Preferences": "preferences",
    "📬 Delivery": "delivery",
    "🕐 Scheduler": "scheduler",
    "❓ Ask the News": "ask",
    "⚙️ Settings": "settings",
}

with st.sidebar:
    st.markdown("""
<div style='text-align:center;padding:14px 0 10px;'>
  <div style='width:42px;height:42px;background:linear-gradient(135deg,#059669,#047857);
              border-radius:12px;display:flex;align-items:center;justify-content:center;
              font-size:1.3rem;margin:0 auto 10px;'>📰</div>
  <div style='font-size:1rem;font-weight:700;color:#E2E8F0;'>AI News Agent</div>
  <div style='font-size:0.67rem;color:#374151;margin-top:2px;'>Powered by GPT-4o</div>
</div>
<hr style='border-color:#0F1A12;margin:6px 0 10px;'>
""", unsafe_allow_html=True)

    if "page" not in st.session_state:
        st.session_state.page = "feed"

    for label, key in PAGES.items():
        is_active = st.session_state.page == key
        if is_active:
            st.markdown(f'<div style="background:#0A1F14;border-radius:8px;border:1px solid #10B98122;margin-bottom:2px;">',
                        unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.rerun()
        if is_active:
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='margin-bottom:2px;'></div>", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#0F1A12;margin:10px 0;'>", unsafe_allow_html=True)
    demo = st.toggle("🎭 Demo Mode", value=st.session_state.get("demo_mode", True))
    st.session_state.demo_mode = demo

    # Article count badge
    arts = current_articles(limit=200)
    high_sig = sum(1 for a in arts if float(a.get("signal_score", 0)) >= 7)
    st.markdown(f"""
<div style='font-size:0.7rem;color:#374151;text-align:center;margin-top:6px;'>
  {len(arts)} stories · <span style='color:#10B981;'>{high_sig} high signal</span>
</div>""", unsafe_allow_html=True)

page = st.session_state.page


# ═══════════════════════════════════════════════════════════════════════════════
#  NEWS FEED
# ═══════════════════════════════════════════════════════════════════════════════
if page == "feed":
    st.markdown("""
<div style='margin-bottom:18px;'>
  <div style='font-size:1.6rem;font-weight:800;color:#F1F5F9;'>📰 News Feed</div>
  <div style='font-size:0.83rem;color:#4B5563;margin-top:2px;'>AI-curated stories from 20+ sources</div>
</div>""", unsafe_allow_html=True)

    # ── Controls ──
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([3, 1.5, 1.5, 1])
    with ctrl1:
        search = st.text_input("", placeholder="🔍  Search stories...", label_visibility="collapsed", key="feed_search")
    with ctrl2:
        min_sig = st.slider("Min Signal", 0.0, 10.0, 0.0, 0.5, key="feed_signal")
    with ctrl3:
        prefs = database.get_preferences()
        all_topics = ["All"] + (prefs.get("topics", []) or
                                ["Technology", "AI", "Finance", "Business", "Science", "Health"])
        topic_filter = st.selectbox("Topic", all_topics, key="feed_topic", label_visibility="collapsed")
    with ctrl4:
        if not use_demo() and st.button("🔄 Fetch", use_container_width=True):
            st.session_state.page = "fetch"
            st.rerun()

    articles = current_articles(limit=100, min_signal=min_sig, search=search)
    if topic_filter != "All":
        articles = [a for a in articles if topic_filter in (a.get("topics") or [])]

    dupes = sum(1 for a in articles if a.get("is_duplicate"))
    unique = [a for a in articles if not a.get("is_duplicate")]

    # Stats row
    c1, c2, c3, c4 = st.columns(4)
    with c1: mc(len(unique), "Unique Stories")
    with c2: mc(sum(1 for a in unique if float(a.get("signal_score",0))>=7), "High Signal 🔥")
    with c3: mc(dupes, "Duplicates Removed")
    with c4:
        pos = sum(1 for a in unique if a.get("sentiment") == "positive")
        mc(f"{int(pos/max(len(unique),1)*100)}%", "Positive Sentiment")

    st.markdown("")

    # ── Main layout: feed + selected article ──
    col_feed, col_detail = st.columns([2, 3])

    with col_feed:
        # Sort controls
        sort_opts = {"Signal ↓": "signal_score", "Newest": "published", "Source": "source"}
        sort_by = st.radio("Sort by", list(sort_opts.keys()), horizontal=True, label_visibility="collapsed")

        key = sort_opts[sort_by]
        sorted_articles = sorted(unique, key=lambda x: x.get(key, ""), reverse=(key != "source"))

        st.markdown(f'<div style="font-size:0.72rem;color:#374151;margin-bottom:8px;">{len(sorted_articles)} stories</div>',
                    unsafe_allow_html=True)

        for art in sorted_articles:
            # Click button + card overlay
            col_btn, col_card = st.columns([0.001, 1])
            with col_card:
                if st.button(art["title"][:35], key=f"art_{art['id']}", use_container_width=True):
                    st.session_state.selected_article = art
                    st.rerun()
                st.markdown(news_card_html(art), unsafe_allow_html=True)
                # Hide button, show only card
                st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] [data-testid="column"]:last-child .stButton > button {
    height:88px!important;background:transparent!important;color:transparent!important;
    border:none!important;box-shadow:none!important;margin-bottom:-88px!important;
    position:relative!important;z-index:5!important;cursor:pointer!important;opacity:0!important;
}
</style>""", unsafe_allow_html=True)

    with col_detail:
        sel = st.session_state.get("selected_article")
        if not sel:
            st.markdown("""
<div style='text-align:center;padding:80px 20px;color:#1A2438;'>
  <div style='font-size:4rem;'>📰</div>
  <div style='font-size:1rem;margin-top:12px;color:#374151;'>Select a story to read</div>
</div>""", unsafe_allow_html=True)
        else:
            score = float(sel.get("signal_score", 0))
            topics_html = "".join(topic_pill(t) for t in sel.get("topics", []))
            st.markdown(f"""
<div style="background:#0F1521;border:1px solid #1A2438;border-radius:14px;padding:22px;margin-bottom:16px;">
  <div style="font-size:0.72rem;font-weight:700;color:#10B981;text-transform:uppercase;
              letter-spacing:0.08em;margin-bottom:6px;">{sel.get('source','')}</div>
  <div style="font-size:1.15rem;font-weight:800;color:#F1F5F9;line-height:1.4;margin-bottom:10px;">
    <a href="{sel.get('url','#')}" target="_blank" style="color:inherit;text-decoration:none;">
      {sel.get('title','')}</a>
  </div>
  <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:12px;">
    {sig_badge(score)} {sent_badge(sel.get('sentiment','neutral'))}
    <span style="font-size:0.72rem;color:#374151;">{fmt_pub(sel.get('published',''))}</span>
    {topics_html}
  </div>
  <div style="font-size:0.88rem;color:#94A3B8;line-height:1.7;">
    {sel.get('summary','') or sel.get('full_text','No content available.')[:600]}
  </div>
  {f'<div style="margin-top:12px;background:#0A1F14;border-left:3px solid #10B981;padding:10px 14px;border-radius:0 8px 8px 0;font-size:0.83rem;color:#6EE7B7;">💡 {sel.get("why_matters","")}</div>' if sel.get("why_matters") else ""}
</div>
""", unsafe_allow_html=True)

            ta, tb, tc = st.columns(3)
            with ta:
                if st.button("🔖 Save Story", use_container_width=True, key="save_art"):
                    database.save_story(sel["id"])
                    st.success("Saved!")
            with tb:
                if ai_ok() and st.button("🤖 AI Summary", use_container_width=True, key="ai_sum"):
                    with st.spinner("Analysing..."):
                        result = agent.analyse_article(sel["title"], sel.get("summary",""), sel.get("source",""))
                        st.session_state[f"ai_{sel['id']}"] = result

            ai_res = st.session_state.get(f"ai_{sel['id']}")
            if ai_res:
                st.markdown(f"""
<div style="background:#0A1F14;border:1px solid #10B98133;border-radius:10px;padding:14px;margin-top:8px;">
  <div style="font-size:0.72rem;font-weight:700;color:#10B981;text-transform:uppercase;margin-bottom:8px;">🤖 AI Analysis</div>
  <div style="font-size:0.85rem;color:#D1FAE5;">{ai_res.get('summary','')}</div>
  <div style="font-size:0.78rem;color:#6B7280;margin-top:8px;">
    Signal: {ai_res.get('signal_score',0):.1f}/10 · Sentiment: {ai_res.get('sentiment','')}
  </div>
</div>""", unsafe_allow_html=True)

            with tc:
                if st.button("🔗 Open Article", use_container_width=True, key="open_art"):
                    st.markdown(f"[Open in new tab]({sel.get('url','#')})")


# ═══════════════════════════════════════════════════════════════════════════════
#  AI DIGEST
# ═══════════════════════════════════════════════════════════════════════════════
if page == "digest":
    st.markdown("""
<div style='margin-bottom:18px;'>
  <div style='font-size:1.6rem;font-weight:800;color:#F1F5F9;'>✨ AI Executive Digest</div>
  <div style='font-size:0.83rem;color:#4B5563;'>GPT-4o morning briefing for decision-makers</div>
</div>""", unsafe_allow_html=True)

    # Generate or load digest
    if ai_ok():
        if st.button("✨ Generate Fresh Digest", use_container_width=False):
            with st.spinner("GPT-4o is writing your executive brief..."):
                arts = current_articles(limit=50)
                prefs = database.get_preferences()
                digest = agent.generate_executive_digest(arts, prefs)
                st.session_state.digest = digest
                # Save to DB
                art_ids = [a["id"] for a in arts[:15]]
                database.save_digest(
                    digest.get("title",""), digest.get("overview",""), art_ids
                )
                st.success("Digest generated!")

    digest = st.session_state.get("digest") or (get_demo_digest() if use_demo() else None)

    if not digest:
        st.info("Click 'Generate Fresh Digest' to create your AI briefing, or enable Demo Mode.")
        st.stop()

    # Header
    sent = digest.get("sentiment_overview", "positive")
    sent_color = "#10B981" if sent == "positive" else "#EF4444" if sent == "negative" else "#64748B"
    st.markdown(f"""
<div style="background:linear-gradient(135deg,#0F1521,#0A1F14);border:1px solid #10B98133;
            border-radius:16px;padding:24px;margin-bottom:20px;">
  <div style="font-size:1.2rem;font-weight:800;color:#F1F5F9;">{digest.get('title','Daily Brief')}</div>
  <div style="display:flex;gap:12px;margin-top:8px;align-items:center;flex-wrap:wrap;">
    <span style="color:{sent_color};font-size:0.83rem;font-weight:600;">
      {'📈' if sent=='positive' else '📉' if sent=='negative' else '➡️'} Sentiment: {sent.title()}
    </span>
    <span style="color:#6B7280;font-size:0.83rem;">Word of the day: <em style="color:#10B981;">{digest.get('word_of_day','')}</em></span>
  </div>
  <div style="margin-top:14px;font-size:0.9rem;color:#CBD5E1;line-height:1.7;
              border-left:3px solid #10B981;padding-left:14px;">
    {digest.get('overview','')}
  </div>
</div>
""", unsafe_allow_html=True)

    # Key themes
    themes = digest.get("key_themes", [])
    if themes:
        st.markdown("**🔑 Key Themes:**")
        st.markdown("".join([
            f'<span style="background:#0A1F14;border:1px solid #10B98133;color:#6EE7B7;'
            f'padding:4px 12px;border-radius:12px;margin:3px;display:inline-block;font-size:0.8rem;">'
            f'{t}</span>'
            for t in themes
        ]), unsafe_allow_html=True)
        st.markdown("")

    # Two-column layout: sections + signals
    col_sections, col_signals = st.columns([3, 2])

    with col_sections:
        st.markdown('<div class="sh">📋 Story Sections</div>', unsafe_allow_html=True)
        for section in digest.get("sections", []):
            st.markdown(f"""
<div class="digest-section">
  <div class="digest-cat">{section.get('category','')}</div>
  <div class="digest-headline">{section.get('headline','')}</div>
  {''.join([f'<div style="display:flex;gap:8px;margin-bottom:6px;"><span style="color:#10B981;margin-top:2px;">▸</span><div style="font-size:0.83rem;color:#94A3B8;"><strong style="color:#CBD5E1;">{s.get("title","")}:</strong> {s.get("insight","")}</div></div>' for s in section.get('stories',[])])}
  <div class="takeaway">💡 {section.get('takeaway','')}</div>
</div>
""", unsafe_allow_html=True)

    with col_signals:
        st.markdown('<div class="sh">📡 Market Signals</div>', unsafe_allow_html=True)
        for sig in digest.get("market_signals", []):
            st.markdown(f"""
<div style="background:#0F1521;border:1px solid #1A2438;border-left:3px solid #10B981;
            border-radius:8px;padding:10px 14px;margin-bottom:6px;font-size:0.83rem;color:#94A3B8;">
  📊 {sig}
</div>""", unsafe_allow_html=True)

        st.markdown('<div class="sh" style="margin-top:16px;">✅ Action Items</div>', unsafe_allow_html=True)
        for i, action in enumerate(digest.get("action_items", []), 1):
            st.markdown(f"""
<div style="background:#0A1F14;border:1px solid #10B98122;border-radius:8px;
            padding:10px 14px;margin-bottom:6px;font-size:0.83rem;color:#6EE7B7;">
  <span style="color:#059669;font-weight:700;">→</span> {action}
</div>""", unsafe_allow_html=True)

        # Download
        st.markdown("")
        if digest.get("full_text"):
            st.download_button(
                "📥 Download Brief (.txt)",
                data=digest["full_text"],
                file_name=f"digest_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

    # Past digests
    past = database.get_digests(limit=5)
    if len(past) > 1:
        st.markdown('<div class="sh">🗂️ Past Digests</div>', unsafe_allow_html=True)
        for d in past[1:]:
            with st.expander(f"📅 {d.get('title','')[:60]} · {d.get('created_at','')[:10]}"):
                st.markdown(d.get("summary","")[:500])


# ═══════════════════════════════════════════════════════════════════════════════
#  HIGH SIGNAL
# ═══════════════════════════════════════════════════════════════════════════════
if page == "high_signal":
    st.markdown("""
<div style='margin-bottom:18px;'>
  <div style='font-size:1.6rem;font-weight:800;color:#F1F5F9;'>🔥 High-Signal Stories</div>
  <div style='font-size:0.83rem;color:#4B5563;'>Stories that matter most — signal score ≥ 7.0</div>
</div>""", unsafe_allow_html=True)

    articles = current_articles(limit=100)
    high = [a for a in articles if float(a.get("signal_score",0)) >= 7.0 and not a.get("is_duplicate")]
    high.sort(key=lambda x: float(x.get("signal_score",0)), reverse=True)

    c1, c2, c3 = st.columns(3)
    with c1: mc(len(high), "High-Signal Stories")
    with c2: mc(sum(1 for a in high if a.get("sentiment")=="positive"), "Positive 📈")
    with c3: mc(sum(1 for a in high if a.get("sentiment")=="negative"), "Negative 📉")

    st.markdown("")

    if not high:
        st.info("No high-signal stories found. Run a news fetch or enable Demo Mode.")
    else:
        # Top 3 featured
        st.markdown('<div class="sh">🏆 Top Stories Today</div>', unsafe_allow_html=True)
        featured = high[:3]
        feat_cols = st.columns(len(featured))
        for i, art in enumerate(featured):
            with feat_cols[i]:
                score = float(art.get("signal_score",0))
                st.markdown(f"""
<div style="background:linear-gradient(135deg,#0F1521,#0A1F14);border:1px solid #10B98133;
            border-radius:14px;padding:18px;height:100%;">
  <div style="font-size:1.6rem;font-weight:900;color:#10B981;">{score:.1f}</div>
  <div style="font-size:0.72rem;color:#10B981;text-transform:uppercase;font-weight:700;margin:4px 0;">
    {art.get('source','')}
  </div>
  <div style="font-size:0.9rem;font-weight:700;color:#F1F5F9;line-height:1.4;margin-bottom:8px;">
    <a href="{art.get('url','#')}" target="_blank" style="color:inherit;text-decoration:none;">
      {art['title'][:100]}</a>
  </div>
  <div style="font-size:0.78rem;color:#64748B;">{art.get('summary','')[:160]}</div>
  {f'<div style="margin-top:10px;font-size:0.76rem;color:#6EE7B7;background:#0A1F14;padding:8px;border-radius:6px;">💡 {art.get("why_matters","")}</div>' if art.get("why_matters") else ""}
</div>
""", unsafe_allow_html=True)

        # Rest as cards
        if len(high) > 3:
            st.markdown('<div class="sh" style="margin-top:20px;">📋 All High-Signal Stories</div>', unsafe_allow_html=True)

            # Detect trends if AI available
            if ai_ok() and st.button("🤖 Detect Emerging Themes", use_container_width=False):
                with st.spinner("Detecting trends..."):
                    themes = agent.detect_trending_themes(high)
                    st.session_state.trends = themes

            trends = st.session_state.get("trends", [])
            if trends:
                st.markdown('<div class="sh" style="font-size:0.9rem;">📈 Emerging Themes</div>', unsafe_allow_html=True)
                trend_cols = st.columns(min(len(trends), 5))
                for i, theme in enumerate(trends[:5]):
                    with trend_cols[i]:
                        momentum_color = "#10B981" if theme.get("momentum")=="rising" else "#F59E0B" if theme.get("momentum")=="stable" else "#64748B"
                        st.markdown(f"""
<div style="background:#0F1521;border:1px solid #1A2438;border-top:3px solid {momentum_color};
            border-radius:10px;padding:12px;text-align:center;">
  <div style="font-size:0.75rem;font-weight:700;color:{momentum_color};">{theme.get('momentum','').upper()}</div>
  <div style="font-weight:700;color:#E2E8F0;font-size:0.88rem;margin:4px 0;">{theme.get('theme','')}</div>
  <div style="font-size:0.72rem;color:#4B5563;">{theme.get('summary','')[:80]}</div>
</div>""", unsafe_allow_html=True)

            for art in high[3:]:
                st.markdown(news_card_html(art), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
if page == "analytics":
    st.markdown("""
<div style='margin-bottom:18px;'>
  <div style='font-size:1.6rem;font-weight:800;color:#F1F5F9;'>📊 News Analytics</div>
  <div style='font-size:0.83rem;color:#4B5563;'>Patterns, trends, and insights from your news feed</div>
</div>""", unsafe_allow_html=True)

    articles = current_articles(limit=200)

    # Metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    total = len(articles)
    unique = [a for a in articles if not a.get("is_duplicate")]
    high_sig = [a for a in unique if float(a.get("signal_score",0)) >= 7]
    pos_count = sum(1 for a in unique if a.get("sentiment")=="positive")
    neg_count = sum(1 for a in unique if a.get("sentiment")=="negative")

    with c1: mc(total, "Total Articles")
    with c2: mc(len(unique), "Unique Stories")
    with c3: mc(len(high_sig), "High Signal 🔥")
    with c4: mc(pos_count, "Positive 📈")
    with c5: mc(neg_count, "Negative 📉")

    st.markdown("")
    col_l, col_r = st.columns(2)

    with col_l:
        # Topic distribution
        st.markdown('<div class="sh">📂 Topic Distribution</div>', unsafe_allow_html=True)
        topic_counts: dict = {}
        for a in unique:
            for t in (a.get("topics") or []):
                topic_counts[t] = topic_counts.get(t, 0) + 1

        if topic_counts:
            sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            fig = go.Figure(go.Bar(
                x=[t[1] for t in sorted_topics],
                y=[t[0] for t in sorted_topics],
                orientation="h",
                marker_color="#10B981",
                text=[t[1] for t in sorted_topics],
                textposition="outside",
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#E2E8F0", height=300,
                xaxis=dict(showgrid=False, color="#374151"),
                yaxis=dict(showgrid=False, color="#94A3B8"),
                margin=dict(l=0, r=40, t=10, b=0),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

        # Source distribution
        st.markdown('<div class="sh">📡 Top Sources</div>', unsafe_allow_html=True)
        source_counts: dict = {}
        for a in unique:
            s = a.get("source", "Unknown")
            source_counts[s] = source_counts.get(s, 0) + 1

        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        for name, count in top_sources:
            pct = int(count / max(total, 1) * 100)
            st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
  <div style="font-size:0.8rem;color:#E2E8F0;width:150px;overflow:hidden;
              text-overflow:ellipsis;white-space:nowrap;">{name}</div>
  <div style="flex:1;background:#1A2438;border-radius:4px;height:5px;">
    <div style="width:{pct}%;height:100%;background:#10B981;border-radius:4px;"></div>
  </div>
  <div style="font-size:0.72rem;color:#374151;width:24px;">{count}</div>
</div>""", unsafe_allow_html=True)

    with col_r:
        # Sentiment pie
        st.markdown('<div class="sh">😐 Sentiment Overview</div>', unsafe_allow_html=True)
        sent_counts = {
            "Positive": sum(1 for a in unique if a.get("sentiment")=="positive"),
            "Neutral": sum(1 for a in unique if a.get("sentiment")=="neutral"),
            "Negative": sum(1 for a in unique if a.get("sentiment")=="negative"),
        }
        fig2 = go.Figure(go.Pie(
            labels=list(sent_counts.keys()),
            values=list(sent_counts.values()),
            hole=0.55,
            marker_colors=["#10B981", "#3B82F6", "#EF4444"],
        ))
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#E2E8F0", height=260,
            legend=dict(font=dict(color="#94A3B8"), x=1, y=0.5),
            margin=dict(l=0, r=80, t=0, b=0),
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Signal score distribution
        st.markdown('<div class="sh">📈 Signal Score Distribution</div>', unsafe_allow_html=True)
        scores = [float(a.get("signal_score", 0)) for a in unique]
        if scores:
            fig3 = go.Figure(go.Histogram(
                x=scores, nbinsx=10,
                marker_color="#10B981", opacity=0.8,
            ))
            fig3.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#E2E8F0", height=220,
                xaxis=dict(title="Signal Score", showgrid=False, color="#374151"),
                yaxis=dict(showgrid=True, gridcolor="#1A2438", color="#374151"),
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig3, use_container_width=True)

    # Avg signal by topic table
    st.markdown('<div class="sh">📊 Signal by Topic</div>', unsafe_allow_html=True)
    topic_signal: dict = {}
    topic_count2: dict = {}
    for a in unique:
        for t in (a.get("topics") or []):
            topic_signal[t] = topic_signal.get(t, 0) + float(a.get("signal_score", 0))
            topic_count2[t] = topic_count2.get(t, 0) + 1

    rows = []
    for t in topic_counts:
        avg = topic_signal.get(t, 0) / max(topic_count2.get(t, 1), 1)
        rows.append({"Topic": t, "Stories": topic_count2.get(t, 0), "Avg Signal": round(avg, 1)})

    if rows:
        df = pd.DataFrame(rows).sort_values("Avg Signal", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  SAVED STORIES
# ═══════════════════════════════════════════════════════════════════════════════
if page == "saved":
    st.markdown("""
<div style='margin-bottom:18px;'>
  <div style='font-size:1.6rem;font-weight:800;color:#F1F5F9;'>🔖 Saved Stories</div>
  <div style='font-size:0.83rem;color:#4B5563;'>Your personal reading list</div>
</div>""", unsafe_allow_html=True)

    saved = database.get_saved_stories()

    if not saved:
        st.info("No saved stories yet. Click 🔖 Save Story in the news feed to bookmark articles.")
    else:
        for s in saved:
            col_card, col_del = st.columns([6, 1])
            with col_card:
                score = float(s.get("signal_score") or 0)
                st.markdown(f"""
<div class="news-card {'high' if score>=7 else 'medium'}">
  <div class="nc-source">{s.get('source','')}</div>
  <div class="nc-title"><a href="{s.get('url','#')}" target="_blank" style="color:inherit;text-decoration:none;">{s.get('title','')}</a></div>
  <div class="nc-summary">{s.get('summary','')[:180]}</div>
  <div class="nc-meta">{sig_badge(score)} {sent_badge(s.get('sentiment','neutral'))}
    <span style="color:#374151;">Saved: {s.get('saved_at','')[:10]}</span>
  </div>
</div>""", unsafe_allow_html=True)
            with col_del:
                if st.button("🗑️", key=f"del_saved_{s['id']}", use_container_width=True):
                    database.remove_saved(s["id"])
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  PREFERENCES
# ═══════════════════════════════════════════════════════════════════════════════
if page == "preferences":
    st.markdown("""
<div style='margin-bottom:18px;'>
  <div style='font-size:1.6rem;font-weight:800;color:#F1F5F9;'>⚙️ News Preferences</div>
  <div style='font-size:0.83rem;color:#4B5563;'>Personalise your news feed and digest</div>
</div>""", unsafe_allow_html=True)

    prefs = database.get_preferences()

    with st.form("prefs_form"):
        col1, col2 = st.columns(2)
        with col1:
            topics_val = ", ".join(prefs.get("topics", []))
            new_topics = st.text_area("📌 Topics (comma-separated)",
                value=topics_val, height=80,
                help="e.g. Technology, AI, Finance, Science, Health, Politics")

            keywords_val = ", ".join(prefs.get("keywords", []))
            new_keywords = st.text_area("🔍 Keywords to track",
                value=keywords_val, height=80,
                help="e.g. GPT-5, interest rates, NVIDIA, quantum computing")

            companies_val = ", ".join(prefs.get("companies", []))
            new_companies = st.text_area("🏢 Companies to follow",
                value=companies_val, height=80,
                help="e.g. Apple, Google, OpenAI, Tesla")

        with col2:
            industries_val = ", ".join(prefs.get("industries", []))
            new_industries = st.text_area("🏭 Industries",
                value=industries_val, height=80,
                help="e.g. Technology, Finance, Healthcare, Energy")

            countries_val = ", ".join(prefs.get("countries", []))
            new_countries = st.text_area("🌍 Countries / Regions",
                value=countries_val, height=80,
                help="e.g. United States, India, European Union")

            all_sources = list(__import__("modules.fetcher", fromlist=["RSS_FEEDS"]).RSS_FEEDS.keys())
            selected_sources = st.multiselect(
                "📡 RSS Sources",
                options=all_sources,
                default=prefs.get("sources", all_sources[:6]),
            )

        submitted = st.form_submit_button("💾 Save Preferences", use_container_width=True)

    if submitted:
        def _parse(text: str) -> list:
            return [t.strip() for t in text.split(",") if t.strip()]

        database.save_preferences({
            "topics": _parse(new_topics),
            "keywords": _parse(new_keywords),
            "industries": _parse(new_industries),
            "companies": _parse(new_companies),
            "countries": _parse(new_countries),
            "sources": selected_sources,
        })
        st.success("✅ Preferences saved!")
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  DELIVERY
# ═══════════════════════════════════════════════════════════════════════════════
if page == "delivery":
    st.markdown("""
<div style='margin-bottom:18px;'>
  <div style='font-size:1.6rem;font-weight:800;color:#F1F5F9;'>📬 Digest Delivery</div>
  <div style='font-size:0.83rem;color:#4B5563;'>Send your AI brief via Email or WhatsApp</div>
</div>""", unsafe_allow_html=True)

    from modules import delivery as dlv

    tab_email, tab_wa = st.tabs(["📧 Email", "💬 WhatsApp"])

    digest = st.session_state.get("digest") or (get_demo_digest() if use_demo() else {})
    articles = current_articles(limit=20)

    with tab_email:
        col1, col2 = st.columns(2)
        with col1:
            to_email = st.text_input("Recipient Email", placeholder="you@company.com")
            smtp_host = st.text_input("SMTP Host", value=os.environ.get("SMTP_HOST","smtp.gmail.com"))
            smtp_user = st.text_input("SMTP Username", value=os.environ.get("SMTP_USER",""))
            smtp_pass = st.text_input("SMTP Password", type="password", value=os.environ.get("SMTP_PASS",""))

        with col2:
            st.markdown("**📧 Email Preview:**")
            if digest:
                st.markdown(f"""
<div style="background:#0F1521;border:1px solid #1A2438;border-radius:10px;padding:14px;
            font-size:0.82rem;color:#94A3B8;line-height:1.6;">
  <strong style="color:#10B981;">Subject:</strong> {digest.get('title','Daily Brief')}<br><br>
  {digest.get('overview','')[:300]}...
</div>""", unsafe_allow_html=True)

        send_email = st.button("📧 Send Email Digest", use_container_width=False,
                               disabled=not (to_email and (smtp_user or use_demo())))
        if send_email:
            if use_demo() or not smtp_user:
                ok, msg = dlv.demo_send("email", to_email, digest.get("overview",""))
            else:
                html_body = dlv.build_html_digest(digest, articles)
                ok, msg = dlv.send_email_digest(
                    to_email, digest.get("title","Daily Brief"),
                    digest.get("full_text",""), html_body,
                    smtp_host=smtp_host, smtp_user=smtp_user, smtp_pass=smtp_pass
                )
            st.success(msg) if ok else st.error(msg)

    with tab_wa:
        phone = st.text_input("WhatsApp Number (with country code)", placeholder="+1234567890")
        if digest:
            msg = dlv.build_whatsapp_message(digest, articles)
            st.text_area("Message Preview", value=msg, height=200)

            if phone:
                wa_link = dlv.get_whatsapp_link(phone, msg)
                st.markdown(f"**[📱 Open WhatsApp & Send]({wa_link})**")
                st.caption("Opens WhatsApp with the message pre-filled — click Send in WhatsApp.")

            if st.button("📋 Copy Message", use_container_width=False):
                st.code(msg)


# ═══════════════════════════════════════════════════════════════════════════════
#  SCHEDULER
# ═══════════════════════════════════════════════════════════════════════════════
if page == "scheduler":
    st.markdown("""
<div style='margin-bottom:18px;'>
  <div style='font-size:1.6rem;font-weight:800;color:#F1F5F9;'>🕐 Scheduler</div>
  <div style='font-size:0.83rem;color:#4B5563;'>Automate your daily news digest</div>
</div>""", unsafe_allow_html=True)

    from modules import scheduler as sched

    sched_config = database.get_schedule()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
<div style="background:#0F1521;border:1px solid #1A2438;border-radius:14px;padding:20px;margin-bottom:16px;">
  <div style="font-size:0.9rem;font-weight:700;color:#E2E8F0;margin-bottom:14px;">⏰ Schedule Settings</div>
""", unsafe_allow_html=True)

        enabled = st.toggle("Enable Scheduler", value=bool(sched_config.get("enabled", True)))
        time_utc = st.time_input("Delivery Time (UTC)", value=datetime.strptime(
            sched_config.get("time_utc","06:00"), "%H:%M"
        ).time())
        frequency = st.selectbox("Frequency", ["daily", "twice_daily", "hourly"],
                                 index=["daily","twice_daily","hourly"].index(
                                     sched_config.get("frequency","daily")))

        if st.button("💾 Save Schedule", use_container_width=True):
            time_str = time_utc.strftime("%H:%M")
            database.save_schedule(enabled, time_str, frequency)
            next_run = sched.get_next_run(time_str)
            database.update_schedule_run(
                datetime.now().isoformat(), next_run
            )
            st.success(f"✅ Schedule saved! Next run: {next_run}")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        next_r = sched_config.get("next_run", "Not scheduled")
        last_r = sched_config.get("last_run", "Never")
        is_running = sched.is_running()

        st.markdown(f"""
<div style="background:#0F1521;border:1px solid #1A2438;border-radius:14px;padding:20px;">
  <div style="font-size:0.9rem;font-weight:700;color:#E2E8F0;margin-bottom:14px;">📊 Status</div>
  <div style="display:grid;gap:12px;">
    <div>
      <div style="font-size:0.7rem;color:#4B5563;text-transform:uppercase;">Scheduler Status</div>
      <div style="font-size:0.9rem;color:{'#10B981' if is_running else '#EF4444'};">
        {'🟢 Running' if is_running else '🔴 Stopped'}
      </div>
    </div>
    <div>
      <div style="font-size:0.7rem;color:#4B5563;text-transform:uppercase;">Next Scheduled Run</div>
      <div style="font-size:0.9rem;color:#CBD5E1;">{next_r}</div>
    </div>
    <div>
      <div style="font-size:0.7rem;color:#4B5563;text-transform:uppercase;">Last Run</div>
      <div style="font-size:0.9rem;color:#CBD5E1;">{last_r}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

        if st.button("▶ Run Fetch Now", use_container_width=True):
            with st.spinner("Fetching news..."):
                try:
                    from modules import fetcher
                    prefs = database.get_preferences()
                    newsapi_key = os.environ.get("NEWS_API_KEY","")
                    raw = fetcher.fetch_all_news(prefs, newsapi_key=newsapi_key)
                    classified = agent.classify_topics(raw)
                    deduped = agent.detect_duplicates(classified)
                    inserted = database.upsert_articles(deduped)
                    st.success(f"✅ Fetched {len(raw)} articles, {inserted} new unique stories saved!")
                    database.update_schedule_run(
                        datetime.now().isoformat(),
                        sched.get_next_run(sched_config.get("time_utc","06:00"))
                    )
                    st.session_state.demo_mode = False
                except Exception as e:
                    st.error(f"Fetch failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#  ASK THE NEWS
# ═══════════════════════════════════════════════════════════════════════════════
if page == "ask":
    st.markdown("""
<div style='margin-bottom:18px;'>
  <div style='font-size:1.6rem;font-weight:800;color:#F1F5F9;'>❓ Ask the News</div>
  <div style='font-size:0.83rem;color:#4B5563;'>Ask GPT-4o anything about today's stories</div>
</div>""", unsafe_allow_html=True)

    if not ai_ok():
        st.warning("Add your OpenAI API key in Settings to use this feature.")
    else:
        articles = current_articles(limit=50)

        # Suggested questions
        st.markdown("**💡 Suggested questions:**")
        suggestions = [
            "What are the most important business stories today?",
            "Which AI developments should I pay attention to?",
            "What are the key market signals today?",
            "What geopolitical events might affect global markets?",
            "Summarise today's tech news in 3 bullet points",
        ]
        cols = st.columns(len(suggestions))
        for i, q in enumerate(suggestions):
            with cols[i]:
                if st.button(q[:35] + "..." if len(q) > 35 else q,
                             key=f"sugg_{i}", use_container_width=True):
                    st.session_state.ask_question = q

        question = st.text_input("Ask a question about today's news",
                                 value=st.session_state.get("ask_question",""),
                                 placeholder="e.g. What should I know about AI this week?",
                                 key="ask_input")

        if st.button("🤖 Ask AI", use_container_width=False) and question:
            with st.spinner("Searching news and thinking..."):
                answer = agent.ask_about_news(question, articles)
                st.session_state.ask_answer = answer
                if "ask_history" not in st.session_state:
                    st.session_state.ask_history = []
                st.session_state.ask_history.append({"q": question, "a": answer})

        if st.session_state.get("ask_answer"):
            st.markdown(f"""
<div style="background:#0A1F14;border:1px solid #10B98133;border-radius:12px;padding:20px;margin-top:16px;">
  <div style="font-size:0.72rem;font-weight:700;color:#10B981;text-transform:uppercase;margin-bottom:10px;">🤖 AI Answer</div>
  <div style="font-size:0.9rem;color:#D1FAE5;line-height:1.7;">{st.session_state.ask_answer}</div>
</div>""", unsafe_allow_html=True)

        # History
        history = st.session_state.get("ask_history", [])
        if len(history) > 1:
            st.markdown('<div class="sh" style="margin-top:20px;">💬 Previous Questions</div>', unsafe_allow_html=True)
            for item in reversed(history[:-1]):
                with st.expander(f"Q: {item['q'][:60]}"):
                    st.markdown(item["a"])


# ═══════════════════════════════════════════════════════════════════════════════
#  SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
if page == "settings":
    st.markdown("""
<div style='margin-bottom:18px;'>
  <div style='font-size:1.6rem;font-weight:800;color:#F1F5F9;'>⚙️ Settings</div>
</div>""", unsafe_allow_html=True)

    tab_api, tab_prefs2, tab_db, tab_about = st.tabs(["🔑 API Keys", "🎛️ Preferences", "🗄️ Database", "ℹ️ About"])

    with tab_api:
        col1, col2 = st.columns([3,1])
        with col1:
            new_oai = st.text_input("OpenAI API Key", type="password",
                                    value=os.environ.get("OPENAI_API_KEY",""),
                                    placeholder="sk-proj-...")
        with col2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("💾 Save", key="save_oai"):
                if new_oai.startswith("sk-"):
                    os.environ["OPENAI_API_KEY"] = new_oai
                    st.success("✅ Key saved!")
                else:
                    st.error("Must start with sk-")

        if os.environ.get("OPENAI_API_KEY"):
            k = os.environ["OPENAI_API_KEY"]
            st.markdown(f'<div style="background:#0A1F14;border:1px solid #10B98133;border-radius:8px;padding:10px 14px;font-size:0.82rem;color:#6EE7B7;">✅ Active: <code>{k[:8]}...{k[-4:]}</code></div>', unsafe_allow_html=True)
            if st.button("🧪 Test Connection"):
                with st.spinner("Testing..."):
                    try:
                        from openai import OpenAI
                        OpenAI(api_key=k).models.list()
                        st.success("✅ GPT-4o ready!")
                    except Exception as e:
                        st.error(f"❌ {e}")

        st.markdown("---")
        col1, col2 = st.columns([3,1])
        with col1:
            new_na = st.text_input("NewsAPI.org Key (optional)",
                                   value=os.environ.get("NEWS_API_KEY",""),
                                   placeholder="Get free key at newsapi.org")
        with col2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("💾 Save", key="save_na"):
                os.environ["NEWS_API_KEY"] = new_na
                st.success("Saved!")

    with tab_prefs2:
        st.markdown("**Feed Settings:**")
        max_articles = st.slider("Max articles per fetch", 50, 500, 200)
        st.session_state.max_articles = max_articles
        dedup = st.toggle("Auto-remove duplicates", value=True)
        st.session_state.auto_dedup = dedup
        ai_enrich = st.toggle("AI enrich articles on fetch (uses API credits)", value=False)
        st.session_state.ai_enrich = ai_enrich
        min_signal_global = st.slider("Minimum signal score to save", 0.0, 10.0, 0.0, 0.5)
        st.session_state.min_signal_global = min_signal_global

    with tab_db:
        stats = database.get_article_stats()
        c1, c2, c3, c4 = st.columns(4)
        with c1: mc(stats["total"], "Articles")
        with c2: mc(stats["today"], "Today")
        with c3: mc(stats["high_signal"], "High Signal")
        with c4: mc(stats["dupes"], "Duplicates")

        st.markdown("")
        ca, cb = st.columns(2)
        with ca:
            if st.button("📤 Export Articles (JSON)", use_container_width=True):
                arts = database.get_articles(limit=500)
                st.download_button("⬇️ Download",
                    data=json.dumps(arts, indent=2, default=str),
                    file_name=f"news_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json")
        with cb:
            with st.expander("⚠️ Clear Article Cache"):
                if st.button("🗑️ Clear All Articles", type="primary"):
                    import sqlite3 as sl
                    c2 = sl.connect("data/news_agent.db")
                    c2.execute("DELETE FROM articles")
                    c2.commit()
                    c2.close()
                    st.success("Cache cleared.")
                    st.rerun()

    with tab_about:
        st.markdown("""
<div style="background:linear-gradient(135deg,#0F1521,#0A1F14);border:1px solid #10B98133;
            border-radius:16px;padding:24px;display:grid;grid-template-columns:1fr 1fr;gap:16px;">
  <div><div style="font-size:0.72rem;color:#10B981;font-weight:700;text-transform:uppercase;">Application</div>
    <div style="color:#E2E8F0;font-weight:600;margin-top:3px;">AI News Summary Agent</div>
    <div style="color:#374151;font-size:0.8rem;">v1.0.0</div></div>
  <div><div style="font-size:0.72rem;color:#10B981;font-weight:700;text-transform:uppercase;">AI Engine</div>
    <div style="color:#E2E8F0;font-weight:600;margin-top:3px;">OpenAI GPT-4o</div>
    <div style="color:#374151;font-size:0.8rem;">8 specialised prompts</div></div>
  <div><div style="font-size:0.72rem;color:#10B981;font-weight:700;text-transform:uppercase;">Sources</div>
    <div style="color:#E2E8F0;font-weight:600;margin-top:3px;">RSS · NewsAPI · HN · Reddit</div>
    <div style="color:#374151;font-size:0.8rem;">20+ feeds supported</div></div>
  <div><div style="font-size:0.72rem;color:#10B981;font-weight:700;text-transform:uppercase;">Storage</div>
    <div style="color:#E2E8F0;font-weight:600;margin-top:3px;">SQLite (local)</div>
    <div style="color:#374151;font-size:0.8rem;">7 tables · zero config</div></div>
</div>""", unsafe_allow_html=True)


# ── Footer ──
st.markdown("""
<hr style='border-color:#0F1A12;margin-top:40px;'>
<div style='text-align:center;font-size:0.68rem;color:#1A2438;padding-bottom:14px;'>
  📰 AI News Agent · GPT-4o · RSS · NewsAPI · Streamlit
</div>
""", unsafe_allow_html=True)
