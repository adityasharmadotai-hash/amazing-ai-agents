"""
app.py — AI SEO Audit Agent  (improved UX & features)
7-page Streamlit dashboard: Audit · Dashboard · AI Suggestions ·
Keywords · Technical · SERP Preview · Export · Settings
"""

import os, sys
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="AI SEO Audit Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
html,body,[class*="css"]{ font-family:'Inter',sans-serif; }

/* ── Sidebar ── */
[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#07090f 0%,#0d1117 55%,#0a0e1a 100%) !important;
}
[data-testid="stSidebar"]>div:first-child{background:transparent !important;}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,[data-testid="stSidebar"] label{color:#e2e8f0 !important;}
[data-testid="stSidebar"] .stButton>button{
    background:rgba(255,255,255,0.06) !important;
    border:1px solid rgba(255,255,255,0.1) !important;
    border-radius:10px !important;color:#eef0ff !important;
    font-size:15px !important;font-weight:600 !important;
    padding:11px 15px !important;width:100% !important;
    margin:2px 0 !important;text-align:left !important;
    transition:all 0.18s !important;letter-spacing:.01em;
}
[data-testid="stSidebar"] .stButton>button p{color:#eef0ff !important;font-size:15px !important;font-weight:600 !important;}
[data-testid="stSidebar"] .stButton>button:hover{
    background:rgba(79,70,229,0.28) !important;
    border-color:rgba(79,70,229,0.5) !important;color:white !important;
}
[data-testid="stSidebar"] .nav-active>button{
    background:linear-gradient(135deg,#4f46e5,#7c3aed) !important;
    border-left:4px solid #a78bfa !important;
    border-top:1px solid rgba(167,139,250,0.3) !important;
    border-right:1px solid rgba(167,139,250,0.15) !important;
    border-bottom:1px solid rgba(167,139,250,0.15) !important;
    color:white !important;font-weight:700 !important;
    box-shadow:0 4px 18px rgba(79,70,229,0.45) !important;
    transform:translateX(3px) !important;
}
[data-testid="stSidebar"] .nav-active>button p{color:white !important;}
.nav-div{height:1px;background:rgba(255,255,255,0.08);margin:10px 0;}

/* ── Score gauge ── */
.score-gauge{
    text-align:center;padding:30px 20px;background:#0e1120;
    border-radius:20px;box-shadow:0 6px 24px rgba(0,0,0,0.08);
    border:1px solid rgba(140,120,255,.18);
}
.score-number{font-size:80px;font-weight:900;line-height:1;letter-spacing:-4px;}
.score-label{font-size:18px;font-weight:700;margin-top:8px;}
.score-sub{font-size:13px;color:#64748b;margin-top:4px;}
.score-ring{
    width:140px;height:140px;border-radius:50%;margin:0 auto 12px;
    display:flex;align-items:center;justify-content:center;
    font-size:56px;font-weight:900;line-height:1;
}

/* ── Category cards ── */
.cat-card{
    background:#0e1120;border-radius:14px;padding:16px 20px;
    border:1px solid rgba(140,120,255,.18);box-shadow:0 2px 6px rgba(0,0,0,0.04);
    margin-bottom:10px;cursor:default;transition:all 0.15s;
}
.cat-card:hover{transform:translateY(-2px);box-shadow:0 6px 16px rgba(0,0,0,0.09);}
.cat-bar{height:7px;border-radius:4px;margin-top:10px;background:#1c2036;}
.cat-bar-fill{height:7px;border-radius:4px;transition:width 0.6s ease;}

/* ── Issue cards ── */
.iss-critical{background:rgba(251,113,133,.12);border:1px solid #fecaca;border-left:4px solid #ef4444;border-radius:10px;padding:12px 16px;margin:5px 0;}
.iss-warning {background:rgba(251,191,36,.12);border:1px solid #fde68a;border-left:4px solid #f59e0b;border-radius:10px;padding:12px 16px;margin:5px 0;}
.iss-info    {background:rgba(96,165,250,.12);border:1px solid #bfdbfe;border-left:4px solid #3b82f6;border-radius:10px;padding:12px 16px;margin:5px 0;}
.iss-pass    {background:rgba(52,211,153,.12);border:1px solid #bbf7d0;border-left:4px solid #22c55e;border-radius:10px;padding:12px 16px;margin:5px 0;}
.iss-title   {font-size:13px;font-weight:600;color:#eef0ff;margin-bottom:4px;}
.iss-fix     {font-size:12px;color:#64748b;}

/* ── AI suggestion cards ── */
.ai-card{
    background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:12px;
    padding:16px 18px;margin:7px 0;
    box-shadow:0 1px 4px rgba(0,0,0,0.05);
}
.ai-title{font-size:14px;font-weight:700;color:#eef0ff;margin-bottom:6px;}
.ai-body {font-size:13px;color:#c9cdf2;line-height:1.65;}
.badge-high{background:rgba(251,113,133,.12);color:#dc2626;border:1px solid #fecaca;
    padding:2px 9px;border-radius:10px;font-size:11px;font-weight:700;}
.badge-med {background:rgba(251,191,36,.12);color:#d97706;border:1px solid #fde68a;
    padding:2px 9px;border-radius:10px;font-size:11px;font-weight:700;}
.badge-low {background:rgba(52,211,153,.12);color:#16a34a;border:1px solid #bbf7d0;
    padding:2px 9px;border-radius:10px;font-size:11px;font-weight:700;}

/* ── SERP preview ── */
.serp-box{
    background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:12px;
    padding:20px 24px;margin:10px 0;
    box-shadow:0 2px 8px rgba(0,0,0,0.06);
    font-family:'Arial',sans-serif;
}
.serp-title{color:#8ab4f8;font-size:20px;font-weight:400;cursor:pointer;
    text-decoration:none;line-height:1.3;}
.serp-title:hover{text-decoration:underline;}
.serp-url  {color:#006621;font-size:14px;margin:2px 0;}
.serp-desc {color:#4d5156;font-size:14px;line-height:1.58;margin-top:2px;}
.serp-title-long{color:#c0392b !important;}

/* ── OG preview ── */
.og-card{
    border:1px solid rgba(140,120,255,.18);border-radius:12px;overflow:hidden;
    max-width:500px;box-shadow:0 2px 8px rgba(0,0,0,0.07);
}
.og-domain{font-size:12px;color:#65676B;text-transform:uppercase;
    padding:10px 12px 4px;background:#0e1120;}
.og-title {font-size:16px;font-weight:700;color:#eef0ff;
    padding:0 12px 4px;background:#0e1120;}
.og-desc  {font-size:14px;color:#65676B;padding:0 12px 12px;background:#0e1120;}

/* ── Sample URL pills ── */
.sample-pill{
    display:inline-block;padding:5px 14px;border-radius:20px;
    background:#1c2036;border:1px solid rgba(140,120,255,.18);
    font-size:12px;font-weight:500;color:#c9cdf2;
    cursor:pointer;margin:4px;transition:all 0.15s;
}
.sample-pill:hover{background:rgba(96,165,250,.12);border-color:#bfdbfe;color:#1d4ed8;}

/* ── Metric cards ── */
.metric-box{
    background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:12px;
    padding:16px;text-align:center;
    box-shadow:0 1px 4px rgba(0,0,0,0.06);
}
.metric-val{font-size:24px;font-weight:800;color:#eef0ff;}
.metric-lbl{font-size:11px;color:#64748b;font-weight:600;
    text-transform:uppercase;letter-spacing:0.05em;margin-top:3px;}

/* ── Section header ── */
.sec-hdr{
    background:linear-gradient(90deg,#4f46e5,#7c3aed);color:white;
    border-radius:10px;padding:11px 18px;margin:18px 0 12px;
    font-size:14px;font-weight:600;
}

/* ── KW badge ── */
.kw-badge{display:inline-block;background:rgba(96,165,250,.12);color:#2563eb;
    border:1px solid #bfdbfe;padding:3px 10px;border-radius:12px;
    font-size:12px;font-weight:600;margin:3px;}

/* ── Comparison bar ── */
.comp-row{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #f1f5f9;}
.comp-lbl{min-width:120px;font-size:13px;font-weight:500;color:#c9cdf2;}
.comp-bar-wrap{flex:1;background:#1c2036;border-radius:4px;height:8px;}
.comp-bar-fill{height:8px;border-radius:4px;transition:width 0.5s;}
.comp-val{min-width:40px;text-align:right;font-size:12px;font-weight:700;}

/* ── Score history spark ── */
.score-trend{font-size:22px;margin-left:8px;}

/* ── Copy button ── */
.copy-btn{
    background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:8px;
    padding:4px 12px;font-size:12px;font-weight:500;color:#c9cdf2;
    cursor:pointer;transition:all 0.15s;float:right;
}
.copy-btn:hover{background:rgba(96,165,250,.12);color:#4f46e5;border-color:#bfdbfe;}

/* ── Page header ── */
.page-hdr{padding:4px 0 20px;}
.page-hdr h1{font-size:26px;font-weight:800;color:#eef0ff;margin:0;}
.page-hdr p{color:#64748b;font-size:14px;margin-top:5px;}

/* ── URL bar ── */
.url-bar{
    background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:10px;
    padding:10px 16px;font-size:14px;font-weight:500;color:#c9cdf2;
    word-break:break-all;margin-bottom:16px;
    display:flex;align-items:center;gap:8px;
}

/* ── Progress steps ── */
.step-row{display:flex;align-items:center;gap:10px;padding:6px 0;font-size:13px;}
.step-done{color:#22c55e;font-size:16px;}
.step-spin{color:#4f46e5;font-size:16px;}

/* ── Tag ── */
.tag{display:inline-block;padding:2px 8px;border-radius:6px;
    font-size:11px;font-weight:600;margin-right:4px;}
.tag-green{background:rgba(52,211,153,.12);color:#16a34a;border:1px solid #bbf7d0;}
.tag-red  {background:rgba(251,113,133,.12);color:#dc2626;border:1px solid #fecaca;}
.tag-blue {background:rgba(96,165,250,.12);color:#2563eb;border:1px solid #bfdbfe;}
.tag-gray {background:#0e1120;color:#64748b;border:1px solid rgba(140,120,255,.18);}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"]{background:#1c2036;border-radius:10px;padding:3px;gap:2px;}
.stTabs [data-baseweb="tab"]{border-radius:8px;font-weight:500;font-size:13px;}
.stTabs [aria-selected="true"]{background:#0e1120 !important;box-shadow:0 1px 4px rgba(0,0,0,0.1);}

/* ── Text area (export) ── */
[data-testid="stTextArea"] textarea{
    background:#0f172a !important;color:#e2e8f0 !important;
    font-size:12px !important;border-radius:10px !important;
    border:1px solid #1e293b !important;font-family:monospace !important;
}

/* ── Input ── */
[data-testid="stTextInput"] input{
    border-radius:10px !important;font-size:15px !important;
    padding:12px 16px !important;border:2px solid rgba(140,120,255,.18) !important;
}
[data-testid="stTextInput"] input:focus{border-color:#4f46e5 !important;}

#MainMenu,footer{visibility:hidden;}

/* ── Fix guide panel ── */
.fix-panel{
    background:linear-gradient(135deg,#f8faff,#f0f4ff);
    border:2px solid #c7d2fe;border-radius:14px;
    padding:20px 24px;margin-top:10px;
}
.fix-step{
    display:flex;gap:12px;padding:8px 0;
    border-bottom:1px solid rgba(99,102,241,0.1);
    align-items:flex-start;
}
.fix-step-num{
    width:24px;height:24px;border-radius:50%;
    background:#4f46e5;color:white;
    font-size:12px;font-weight:700;flex-shrink:0;
    display:flex;align-items:center;justify-content:center;
}
.fix-step-text{font-size:13px;color:#c9cdf2;line-height:1.5;padding-top:3px;}
.fix-badge{
    display:inline-block;padding:3px 10px;border-radius:12px;
    font-size:11px;font-weight:700;margin-right:6px;
}
.fix-easy  {background:rgba(52,211,153,.12);color:#16a34a;border:1px solid #bbf7d0;}
.fix-medium{background:rgba(251,191,36,.12);color:#d97706;border:1px solid #fde68a;}
.fix-hard  {background:rgba(251,113,133,.12);color:#dc2626;border:1px solid #fecaca;}
.fix-code{
    background:#0f172a;border-radius:10px;padding:14px 16px;
    font-family:monospace;font-size:12px;color:#a5f3fc;
    line-height:1.7;overflow-x:auto;margin:10px 0;
    white-space:pre;
}
.fix-list-item{
    font-size:12px;color:#c9cdf2;padding:3px 0;
    display:flex;align-items:flex-start;gap:6px;
}

</style>
""", unsafe_allow_html=True)

# ── Imports ───────────────────────────────────────────────────────────────────
from modules.scraper import fetch_page, extract_raw_data
from modules.analyser import (
    analyse_meta, analyse_headings, analyse_keywords,
    analyse_technical, analyse_images, analyse_links,
    calculate_overall, score_label, issue_counts,
)
from modules.ai_advisor import (
    is_configured, seo_improvements, content_optimisation,
    technical_guidance, ux_suggestions, keyword_strategy,
)
from modules.exporter import export_markdown, export_pdf
from modules.fixes import get_fix_guide, FIX_GUIDES
from modules import ui
import streamlit.components.v1 as components
from modules import dark_ui, projections, history, rankings, suggestions
from datetime import datetime

# Inject the agentic animation layer (keyframes, Scout, gauges, pulse line…)
st.markdown(ui.animations_css(), unsafe_allow_html=True)

# Dark-theme override for the legacy GPT-4o pages. Only class-based rules here —
# attribute-substring matching on inline styles does NOT work (the browser serialises
# inline styles with spaces and rgb(), so [style*="background:#0e1120"] never matches).
# The inline-styled markup in those pages is converted at the source below instead.
st.markdown("""
<style>
.cat-card:hover{ box-shadow:0 6px 16px rgba(99,102,241,.25) !important; }
.cat-bar,.comp-bar-wrap{ background:#1c2036 !important; }
.serp-title{ color:#8ab4f8 !important; } .serp-url{ color:#6ee7a8 !important; }
.metric-lbl{ color:#8a90bf !important; }
.stTabs [data-baseweb="tab-list"]{ background:#0e1120 !important; }
.stTabs [aria-selected="true"]{ background:#1c2036 !important; }
.iss-info{ background:rgba(59,130,246,.12) !important; }
.iss-pass{ background:rgba(34,197,94,.12) !important; }
.iss-warning{ background:rgba(245,158,11,.12) !important; }
.iss-critical{ background:rgba(239,68,68,.12) !important; }
.fix-step-text,.fix-list-item{ color:#c9cdf2 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {
    "page":"💓 Live Pulse","raw_data":None,"audit":None,"ai":None,
    "user_api_key":"","serp_api_key":"","audit_history":[],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

def _active_key() -> str:
    sk = st.session_state.get("user_api_key","").strip()
    if sk: return sk
    try: return st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY","")
    except: return os.environ.get("OPENAI_API_KEY","")

def _sync():
    k = _active_key()
    if k: os.environ["OPENAI_API_KEY"] = k
_sync()

def _sync_serp():
    """Make the SerpAPI key available to modules.rankings (in-app field, secret, or env)."""
    k = st.session_state.get("serp_api_key", "").strip()
    if not k:
        try: k = st.secrets.get("SERPAPI_KEY") or ""
        except Exception: k = ""
    k = k or os.environ.get("SERPAPI_KEY", "")
    if k: os.environ["SERPAPI_KEY"] = k
_sync_serp()

# ── Live site monitor ─────────────────────────────────────────────────────────
LIVE_SITE = "https://futrbridge.com"

@st.cache_data(ttl=1800, show_spinner=False)
def run_live_audit(url: str) -> dict:
    """Rule-based audit of a site, cached for 30 min. No API key needed."""
    page = fetch_page(url)
    if "error" in page:
        return {"error": page["error"]}
    raw = extract_raw_data(page)
    if "error" in raw:
        return {"error": raw["error"]}
    audit = {
        "meta":      analyse_meta(raw),    "headings":  analyse_headings(raw),
        "keywords":  analyse_keywords(raw), "technical": analyse_technical(raw),
        "images":    analyse_images(raw),   "links":     analyse_links(raw),
    }
    audit["overall_score"] = calculate_overall(audit)
    return {"raw": raw, "audit": audit}


def live_audit_or_stop():
    """Run (cached) live audit of the tracked site; render an error + stop on failure."""
    with st.spinner("📡 Scout is scanning the live site…"):
        res = run_live_audit(LIVE_SITE)
    if res.get("error"):
        st.markdown(ui.scout_svg("worried", size=140), unsafe_allow_html=True)
        st.error(f"😟 Scout couldn't reach {LIVE_SITE}: {res['error']}")
        st.stop()
    history.record(LIVE_SITE, res["audit"])
    return res["raw"], res["audit"]


def dark_page_header(title, subtitle, with_rescan=False):
    """A dark-theme-friendly page header; returns True if the rescan button was clicked."""
    clicked = False
    if with_rescan:
        c1, c2 = st.columns([5, 1])
    else:
        c1 = st.container(); c2 = None
    with c1:
        st.markdown(
            f"<div style='font-family:Space Grotesk,sans-serif;font-weight:700;font-size:25px;color:#eef0ff;'>{title}</div>"
            f"<div style='color:#8a90bf;font-size:13.5px;margin-top:3px;'>{subtitle}</div>",
            unsafe_allow_html=True)
    if c2 is not None:
        with c2:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            clicked = st.button("🔄 Re-scan", use_container_width=True)
    return clicked

# Friendly page titles for the live site's ranking pages. FutrBridge is a
# single-page site today, so the landing page is the one that ranks.
PAGE_NAMES = {"/": "Landing page — Hire the Top 1% AI Talent"}
CAT_PAGE_DESC = {
    "meta": "Title, description, canonical and social tags — how search engines and social platforms read your page.",
    "headings": "Your heading hierarchy (H1–H6) — how content is structured for readers and crawlers.",
    "keywords": "The terms your page targets, their placement and density.",
    "technical": "Performance, security, crawlability and structured data — the engine room of SEO.",
    "images": "Alt text, lazy-loading and dimensions — accessibility, image search traffic and layout stability.",
    "links": "Internal and external links, anchor-text quality and crawl paths.",
}

# ── Navigation ────────────────────────────────────────────────────────────────
# Each item: (icon, label, page_id). Dark pages use clean ids; category health
# pages use "cat:<key>"; legacy GPT-4o pages keep their original "icon label" ids.
NAV_GROUPS = [
    ("Monitor", [
        ("💓", "Live Pulse",       "💓 Live Pulse"),
        ("🚀", "Improvements",     "🚀 Improvements"),
    ]),
    ("Search Rankings", [
        ("🔑", "Keyword Rankings", "🔑 Keyword Rankings"),
        ("📄", "Pages",            "📄 Pages"),
        ("💡", "Keyword Ideas",    "💡 Keyword Ideas"),
        ("🏆", "Competitors",      "🏆 Competitors"),
    ]),
    ("Page Health", [
        ("🏷️", "Meta Tags",  "cat:meta"),
        ("📝", "Headings",   "cat:headings"),
        ("🗝️", "Keywords",   "cat:keywords"),
        ("⚙️", "Technical",  "cat:technical"),
        ("🖼️", "Images",     "cat:images"),
        ("🔗", "Links",      "cat:links"),
    ]),
    ("Full Audit · GPT-4o", [
        ("🔍", "Run Audit",     "🔍 Audit"),
        ("📊", "Dashboard",     "📊 Dashboard"),
        ("🤖", "AI Suggestions","🤖 AI Suggestions"),
        ("👁️", "SERP Preview",  "👁️ SERP Preview"),
        ("🔧", "Fix Guides",    "🔧 Fix Guides"),
        ("📤", "Export",        "📤 Export"),
        ("🔑", "Settings",      "🔑 Settings"),
    ]),
]
# Pages that never require a manual audit (they run on the live site).
ALWAYS_OPEN = {"💓 Live Pulse", "🚀 Improvements", "🔑 Keyword Rankings", "📄 Pages",
               "💡 Keyword Ideas", "🏆 Competitors", "🔍 Audit", "🔑 Settings"}

# ── Fix guide renderer ────────────────────────────────────────────────────────
def _render_fix_guide(guide: dict):
    """Render a comprehensive fix guide inline."""
    diff  = guide.get("difficulty","Medium")
    time_ = guide.get("time","")
    impact = guide.get("impact","Medium")
    diff_cls  = {"Easy":"fix-easy","Medium":"fix-medium","Hard":"fix-hard"}.get(diff,"fix-medium")
    impact_color = {"High":"#dc2626","Medium":"#d97706","Low":"#16a34a"}.get(impact,"#64748b")

    st.markdown(f"""
    <div class="fix-panel">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:14px;">
            <span class="fix-badge {diff_cls}">🎯 {diff} difficulty</span>
            <span class="fix-badge" style="background:rgba(96,165,250,.12);color:#2563eb;border:1px solid #bfdbfe;">
                ⏱ {time_}
            </span>
            <span class="fix-badge" style="background:rgba(251,113,133,.12);color:{impact_color};border:1px solid #fecaca;">
                ⚡ {impact} impact
            </span>
        </div>
        <div style="font-size:13px;color:#c9cdf2;line-height:1.7;margin-bottom:16px;
                    background:#0e1120;border-radius:8px;padding:12px 14px;border:1px solid rgba(140,120,255,.18);">
            {guide.get('summary','')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Steps
    steps = guide.get("steps",[])
    if steps:
        st.markdown("**📋 Step-by-Step Instructions:**")
        for i, step in enumerate(steps, 1):
            st.markdown(f"""
            <div class="fix-step">
                <div class="fix-step-num">{i}</div>
                <div class="fix-step-text">{step}</div>
            </div>
            """, unsafe_allow_html=True)

    # Code example
    code = guide.get("code","")
    if code:
        st.markdown("**💻 Code Example:**")
        st.code(code, language="html")

    # Do / Don't
    dos   = guide.get("do",[])
    donts = guide.get("dont",[])
    if dos or donts:
        dc1, dc2 = st.columns(2)
        with dc1:
            if dos:
                st.markdown("**✅ Do:**")
                for d in dos:
                    st.markdown(f"""
                    <div class="fix-list-item">
                        <span style="color:#22c55e;flex-shrink:0;">✓</span>
                        <span>{d}</span>
                    </div>
                    """, unsafe_allow_html=True)
        with dc2:
            if donts:
                st.markdown("**❌ Don't:**")
                for d in donts:
                    st.markdown(f"""
                    <div class="fix-list-item">
                        <span style="color:#ef4444;flex-shrink:0;">✗</span>
                        <span>{d}</span>
                    </div>
                    """, unsafe_allow_html=True)



# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    has_key   = bool(_active_key())
    has_audit = st.session_state.audit is not None
    score     = st.session_state.audit.get("overall_score",0) if has_audit else 0
    lbl, scol = score_label(score) if has_audit else ("","#6b7280")

    st.markdown(f"""
    <div style="padding:14px 4px 10px;text-align:center;">
        {ui.scout_mini(ui.mascot_mood(score) if has_audit else "content", size=58)}
        <div style="font-size:17px;font-weight:800;color:white;margin-top:7px;">Scout · SEO Agent</div>
        <div style="font-size:12px;color:#9aa0c8;margin-top:3px;">Live audits · Powered by GPT-4o</div>
        {"<div style='margin-top:10px;background:rgba(79,70,229,0.2);border-radius:8px;padding:8px 4px;'><div style='font-size:26px;font-weight:900;color:"+scol+";line-height:1;'>"+str(score)+"<span style=\"font-size:12px;color:#94a3b8;font-weight:500;\">/100</span></div><div style='font-size:11px;color:"+scol+";font-weight:700;'>"+lbl+"</div></div>" if has_audit else ""}
    </div>
    <div class="nav-div"></div>
    <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:0.1em;font-weight:600;padding:0 4px;margin-bottom:6px;">Navigation</div>
    """, unsafe_allow_html=True)

    current = st.session_state.get("page","💓 Live Pulse")
    for group_title, items in NAV_GROUPS:
        st.markdown(f'<div style="font-size:12px;color:#a0a6cf;text-transform:uppercase;'
                    f'letter-spacing:0.12em;font-weight:800;padding:12px 4px 5px;">{group_title}</div>',
                    unsafe_allow_html=True)
        for icon, label, pid in items:
            active = (current == pid)
            locked = (pid not in ALWAYS_OPEN) and (not pid.startswith("cat:")) and (not has_audit)
            if active: st.markdown('<div class="nav-active">', unsafe_allow_html=True)
            btn_lbl = f"✦  {icon}  {label}" if active else f"{icon}  {label}"
            if st.button(btn_lbl, key=f"nav_{pid}", use_container_width=True, disabled=locked):
                st.session_state.page = pid; st.rerun()
            if active: st.markdown('</div>', unsafe_allow_html=True)

    page = st.session_state.get("page","💓 Live Pulse")

    # Active audit card
    if has_audit:
        raw = st.session_state.raw_data
        counts = issue_counts(st.session_state.audit)
        st.markdown(f"""
        <div class="nav-div"></div>
        <div style="background:rgba(79,70,229,0.15);border:1px solid rgba(79,70,229,0.3);
                    border-radius:10px;padding:10px 12px;">
            <div style="font-size:10px;color:#818cf8;text-transform:uppercase;font-weight:600;">✅ Audited</div>
            <div style="font-size:11px;font-weight:600;color:white;margin-top:4px;word-break:break-all;">{raw.get('domain','')}</div>
            <div style="font-size:11px;color:#64748b;margin-top:5px;display:flex;gap:6px;flex-wrap:wrap;">
                <span style="color:#ef4444;">❌{counts['critical']}</span>
                <span style="color:#f59e0b;">⚠️{counts['warning']}</span>
                <span style="color:#22c55e;">✅{counts['pass']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        # New audit button
        if st.button("🔄 New Audit", use_container_width=True):
            st.session_state.page = "🔍 Audit"; st.rerun()

    st.markdown("""
    <div class="nav-div"></div>
    <div style="font-size:11px;color:#334155;text-align:center;padding:2px 0 8px;">
        Built with ❤️ by <a href="https://www.adityasharma.ai" target="_blank"
        style="color:#818cf8;text-decoration:none;">adityasharma.ai</a>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: LIVE PULSE  — always-on agentic monitor for futrbridge.com
# ══════════════════════════════════════════════════════════════════════════════
if page == "💓 Live Pulse":
    site = LIVE_SITE.replace("https://", "")
    if dark_page_header(f"💓 Live Pulse <span style='color:#a78bfa;font-size:15px'>· {site}</span>",
                        "Scout watches your site 24/7 — auto-refreshed every 30 minutes.",
                        with_rescan=True):
        run_live_audit.clear(); st.rerun()

    raw, audit = live_audit_or_stop()
    score = audit["overall_score"]
    counts = issue_counts(audit)
    trend = history.overall_points(LIVE_SITE)
    html = dark_ui.render_overview(
        audit, counts, raw.get("load_time_seconds", 0),
        ui.scout_line(score, audit), trend, datetime.now().strftime("%H:%M"))
    components.html(html, height=980, scrolling=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: IMPROVEMENTS (roadmap)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🚀 Improvements":
    if dark_page_header("🚀 Improvement Roadmap",
                        "If you apply every fix Scout found, here's where your score goes — and the order to do it in.",
                        with_rescan=True):
        run_live_audit.clear(); st.rerun()
    raw, audit = live_audit_or_stop()
    proj = projections.project(audit)
    html = dark_ui.render_roadmap(proj, projections.roadmap(audit))
    components.html(html, height=1000, scrolling=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: KEYWORD RANKINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔑 Keyword Rankings":
    has_serp = rankings.has_key()
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(
            "<div style='font-family:Space Grotesk,sans-serif;font-weight:700;font-size:25px;color:#eef0ff;'>🔑 Keyword Rankings</div>"
            "<div style='color:#8a90bf;font-size:13.5px;margin-top:3px;'>Where futrbridge.com ranks in Google "
            "🇺🇸 US &amp; 🌉 SF Bay Area for your target keywords.</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        refresh = st.button("🔄 Refresh", use_container_width=True, disabled=not has_serp)

    cache = rankings.load_cache()
    if has_serp and refresh:
        bar = st.progress(0.0, text="Querying Google…")
        def _prog(done, total, label):
            bar.progress(done / total, text=f"SerpAPI · {label}  ({done}/{total})")
        cache = rankings.refresh(progress=_prog)
        bar.empty(); st.rerun()
    if has_serp and not cache:
        st.info("No rankings cached yet — hit **🔄 Refresh** to fetch live positions "
                f"({len(rankings.DEFAULT_KEYWORDS)} keywords × 2 locations = "
                f"{len(rankings.DEFAULT_KEYWORDS)*2} SerpAPI searches).")

    updated = cache.get("updated", "never").replace("T", " ") if cache else "never"
    html = dark_ui.render_rankings(rankings.rows(cache), rankings.summary(cache),
                                   updated, has_serp, rankings.locations(), LIVE_SITE)
    components.html(html, height=640, scrolling=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PAGES (keywords each page ranks for)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📄 Pages":
    dark_page_header("📄 Pages",
                     "Every ranking page and the keywords driving traffic to it — with position and location.")
    cache = rankings.load_cache()
    if not rankings.has_key():
        st.info("Connect **SERPAPI_KEY** in Settings and refresh **Keyword Rankings** to populate this view.")
    by_page = {}
    for r in rankings.rows(cache):
        by_page.setdefault(r["page"], []).append(r)
    html = dark_ui.render_pages(by_page, PAGE_NAMES, rankings.locations(), LIVE_SITE)
    components.html(html, height=620, scrolling=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: COMPETITORS (who else ranks for your keywords)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏆 Competitors":
    has_serp = rankings.has_key()
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(
            "<div style='font-family:Space Grotesk,sans-serif;font-weight:700;font-size:25px;color:#eef0ff;'>🏆 Competitors</div>"
            "<div style='color:#8a90bf;font-size:13.5px;margin-top:3px;'>Companies ranking in Google's top 10 for your "
            "AI-staffing keywords (US &amp; SF Bay Area) — and which keywords each one wins.</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        refresh = st.button("🔄 Refresh", use_container_width=True, disabled=not has_serp)

    cache = rankings.load_cache()
    if has_serp and refresh:
        bar = st.progress(0.0, text="Scanning Google SERPs…")
        def _prog(done, total, label):
            bar.progress(done / total, text=f"SerpAPI · {label}  ({done}/{total})")
        cache = rankings.refresh(progress=_prog)
        bar.empty(); st.rerun()
    if has_serp and not cache:
        st.info("No SERP data yet — hit **🔄 Refresh** (also populates Keyword Rankings).")

    comps = rankings.competitors(cache)
    updated = cache.get("updated", "never").replace("T", " ") if cache else "never"
    html = dark_ui.render_competitors(comps, has_serp, updated,
                                      rankings.competitor_summary(cache))
    n = len(comps)
    components.html(html, height=(240 + 132 * n) if n else 420, scrolling=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: KEYWORD IDEAS (long-tail suggestions + how to rank)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💡 Keyword Ideas":
    has_serp = rankings.has_key()
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(
            "<div style='font-family:Space Grotesk,sans-serif;font-weight:700;font-size:25px;color:#eef0ff;'>💡 Keyword Ideas</div>"
            "<div style='color:#8a90bf;font-size:13.5px;margin-top:3px;'>Winnable long-tail keywords Scout mined from "
            "Google — each with a plan for how to rank.</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        gen = st.button("✨ Generate", use_container_width=True, disabled=not has_serp)

    cache = suggestions.load_cache()
    if has_serp and gen:
        bar = st.progress(0.0, text="Mining Google…")
        def _p(done, total, label):
            bar.progress(done / total, text=f"SerpAPI · expanding “{label}”  ({done}/{total})")
        cache = suggestions.generate(progress=_p)
        bar.empty(); st.rerun()
    if has_serp and not cache:
        st.info(f"No ideas yet — hit **✨ Generate** to mine winnable keywords "
                f"({len(suggestions.DISCOVERY_SEEDS)} SerpAPI searches).")

    updated = cache.get("updated", "never").replace("T", " ") if cache else "never"
    html = dark_ui.render_suggestions(cache.get("items", []), suggestions.counts(cache),
                                      updated, has_serp)
    n = len(cache.get("items", []))
    components.html(html, height=(180 + 188 * n) if n else 420, scrolling=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: CATEGORY HEALTH (cat:<key>) — page-by-page improvement view
# ══════════════════════════════════════════════════════════════════════════════
elif page.startswith("cat:"):
    cat = page.split(":", 1)[1]
    name, icon = projections.CAT_META.get(cat, (cat.title(), "📋"))
    if dark_page_header(f"{icon} {name}",
                        f"Page health & exact fixes for {name.lower()} on {LIVE_SITE.replace('https://','')}.",
                        with_rescan=True):
        run_live_audit.clear(); st.rerun()
    raw, audit = live_audit_or_stop()
    cd = audit.get(cat, {})
    proj_cat = projections.project_category(cat, cd)
    fixes = projections.category_fixes(audit, cat)
    html = dark_ui.render_category(cat, name, icon, CAT_PAGE_DESC.get(cat, ""),
                                   cd.get("score", 0), proj_cat, fixes)
    components.html(html, height=(360 + 220 * ((len(fixes) + 1) // 2)) if fixes else 420, scrolling=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AUDIT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Audit":

    st.markdown("""
    <div class="page-hdr">
        <h1>🔍 AI Website SEO Audit</h1>
        <p>Instant 6-category audit with AI recommendations · No signup required · Free to run</p>
    </div>
    """, unsafe_allow_html=True)

    # ── URL Input ──────────────────────────────────────────────────────────────
    col_url, col_btn = st.columns([5, 1])
    with col_url:
        url_input = st.text_input(
            "URL", placeholder="🌐  https://yourwebsite.com",
            label_visibility="collapsed",
        )
    with col_btn:
        run_audit = st.button("🔍 Audit Now", type="primary", use_container_width=True)

    # ── Sample URLs ────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-top:8px;">
        <span style="font-size:12px;color:#94a3b8;font-weight:500;">Try an example: </span>
    </div>
    """, unsafe_allow_html=True)
    samples = ["https://openai.com", "https://stripe.com", "https://notion.so", "https://linear.app"]
    scols = st.columns(len(samples))
    for col, url in zip(scols, samples):
        with col:
            if st.button(url.replace("https://",""), key=f"sample_{url}", use_container_width=True):
                st.session_state["_sample_url"] = url
                st.rerun()
    if st.session_state.get("_sample_url"):
        url_input = st.session_state.pop("_sample_url")
        run_audit = True

    # ── Options ───────────────────────────────────────────────────────────────
    with st.expander("⚙️ Audit Options", expanded=False):
        oc1, oc2, oc3 = st.columns(3)
        with oc1:
            run_ai = st.checkbox("🤖 AI Analysis (GPT-4o)", value=True,
                                 help="5 GPT-4o calls — ~$0.025 per audit")
        with oc2:
            show_passes = st.checkbox("Show ✅ passed checks", value=False)
        with oc3:
            lang_hint = st.selectbox("Content language", ["auto","English","Spanish","French","German","Hindi"])

    # ── Audit execution ────────────────────────────────────────────────────────
    if run_audit and url_input:
        if run_ai and not _active_key():
            st.warning("⚠️ No OpenAI key. Go to 🔑 Settings or uncheck AI Analysis.")
            st.stop()

        STEPS = [
            ("📡","Fetching website & measuring load time..."),
            ("🔍","Extracting HTML: meta, headings, images, links..."),
            ("📊","Scoring: Meta tags & Open Graph..."),
            ("📝","Scoring: Headings & keyword analysis..."),
            ("⚙️","Scoring: Technical SEO & performance..."),
            ("🖼️","Scoring: Images & accessibility..."),
            ("🔗","Scoring: Internal & external links..."),
        ]
        if run_ai:
            STEPS += [
                ("🤖","GPT-4o: Generating improvement plan..."),
                ("✍️","GPT-4o: Optimising content & meta tags..."),
                ("🔧","GPT-4o: Technical guidance & CWV..."),
                ("🎨","GPT-4o: UX & engagement suggestions..."),
                ("📈","GPT-4o: Keyword strategy & content ideas..."),
            ]

        progress_bar = st.progress(0)
        status_text  = st.empty()
        step_count   = len(STEPS)

        def update(i):
            icon, msg = STEPS[i]
            progress_bar.progress((i+1)/step_count)
            status_text.markdown(f"""
            <div style="background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:10px;
                        padding:12px 16px;font-size:13px;color:#c9cdf2;">
                {icon} <strong>Step {i+1}/{step_count}:</strong> {msg}
            </div>""", unsafe_allow_html=True)

        try:
            update(0)
            page_data = fetch_page(url_input)
            if "error" in page_data:
                progress_bar.empty(); status_text.empty()
                st.error(f"❌ {page_data['error']}"); st.stop()

            update(1)
            raw = extract_raw_data(page_data)
            if "error" in raw:
                progress_bar.empty(); status_text.empty()
                st.error(f"❌ {raw['error']}"); st.stop()

            update(2); meta_r  = analyse_meta(raw)
            update(3); head_r  = analyse_headings(raw); kw_r = analyse_keywords(raw)
            update(4); tech_r  = analyse_technical(raw)
            update(5); img_r   = analyse_images(raw)
            update(6); link_r  = analyse_links(raw)

            audit = {
                "meta":meta_r,"headings":head_r,"keywords":kw_r,
                "technical":tech_r,"images":img_r,"links":link_r,
            }
            audit["overall_score"] = calculate_overall(audit)

            ai_results = {"improvements":{},"content":{},"technical":{},"ux":{},"keywords":{}}
            if run_ai and _active_key():
                update(7);  ai_results["improvements"] = seo_improvements(raw, audit)
                update(8);  ai_results["content"]      = content_optimisation(raw, audit)
                update(9);  ai_results["technical"]    = technical_guidance(raw, audit)
                update(10); ai_results["ux"]           = ux_suggestions(raw, audit)
                update(11); ai_results["keywords"]     = keyword_strategy(raw, audit)

            st.session_state.raw_data = raw
            st.session_state.audit    = audit
            st.session_state.ai       = ai_results

            # Save to history
            hist = st.session_state.audit_history
            hist.insert(0,{"url":raw["url"],"score":audit["overall_score"],"domain":raw["domain"]})
            if len(hist) > 10: hist.pop()

            progress_bar.progress(1.0)
            status_text.markdown(f"""
            <div style="background:rgba(52,211,153,.12);border:2px solid #86efac;border-radius:10px;
                        padding:12px 16px;font-size:14px;font-weight:600;color:#6ee7b7;">
                ✅ Audit complete! Score: {audit['overall_score']}/100 — navigating to dashboard...
            </div>""", unsafe_allow_html=True)
            import time; time.sleep(0.8)
            progress_bar.empty(); status_text.empty()
            st.session_state.page = "📊 Dashboard"; st.rerun()

        except Exception as e:
            progress_bar.empty(); status_text.empty()
            st.error(f"❌ Unexpected error: {e}")

    # ── Landing ───────────────────────────────────────────────────────────────
    if not st.session_state.audit:
        st.markdown("<br>", unsafe_allow_html=True)

        # How it works
        st.markdown('<div class="sec-hdr">🚀 How It Works — 3 Steps, 60 Seconds</div>', unsafe_allow_html=True)
        hw1, hw2, hw3 = st.columns(3)
        for col, num, icon, title, desc in [
            (hw1,"1","🌐","Paste Any URL","Enter your website or a competitor's URL — any public webpage"),
            (hw2,"2","⚡","Instant Analysis","6-category rule-based audit runs in seconds, no API key needed"),
            (hw3,"3","🤖","AI Recommendations","GPT-4o generates your personalised fix plan, content & keyword strategy"),
        ]:
            with col:
                st.markdown(f"""
                <div style="background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:16px;
                            padding:24px 18px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.05);">
                    <div style="width:40px;height:40px;background:linear-gradient(135deg,#4f46e5,#7c3aed);
                                color:white;border-radius:50%;font-weight:900;font-size:18px;
                                margin:0 auto 14px;display:flex;align-items:center;justify-content:center;">{num}</div>
                    <div style="font-size:28px;margin-bottom:10px;">{icon}</div>
                    <div style="font-weight:700;color:#eef0ff;font-size:14px;margin-bottom:6px;">{title}</div>
                    <div style="font-size:12px;color:#64748b;line-height:1.6;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)

        # What you get
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="sec-hdr">📋 What You Get in Every Audit</div>', unsafe_allow_html=True)
        wg1, wg2 = st.columns(2)
        left_items = [
            ("🏷️","Meta Tags Analysis","Title length, description, OG tags, Twitter cards, canonical URL"),
            ("📝","Heading Structure","H1-H6 hierarchy, keyword placement, empty tag detection"),
            ("🔑","Keyword Analysis","Top keywords, density, keyword-in-title/H1/description check"),
            ("⚙️","Technical SEO","HTTPS, load time, HTML size, schema markup, security headers"),
        ]
        right_items = [
            ("🖼️","Image & Accessibility","Alt text coverage, lazy loading, width/height attributes"),
            ("🔗","Link Analysis","Internal/external count, anchor text quality, nofollow ratio"),
            ("🤖","AI Action Plan","Quick wins, short-term & long-term improvements with impact ratings"),
            ("📥","Export Reports","Professional PDF + Markdown for clients and teams"),
        ]
        with wg1:
            for icon, title, desc in left_items:
                st.markdown(f"""
                <div style="display:flex;gap:12px;padding:12px 0;border-bottom:1px solid #f1f5f9;">
                    <div style="font-size:22px;width:32px;flex-shrink:0;">{icon}</div>
                    <div>
                        <div style="font-weight:600;font-size:13px;color:#eef0ff;">{title}</div>
                        <div style="font-size:12px;color:#64748b;margin-top:2px;">{desc}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        with wg2:
            for icon, title, desc in right_items:
                st.markdown(f"""
                <div style="display:flex;gap:12px;padding:12px 0;border-bottom:1px solid #f1f5f9;">
                    <div style="font-size:22px;width:32px;flex-shrink:0;">{icon}</div>
                    <div>
                        <div style="font-weight:600;font-size:13px;color:#eef0ff;">{title}</div>
                        <div style="font-size:12px;color:#64748b;margin-top:2px;">{desc}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Audit history
        hist = st.session_state.audit_history
        if hist:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="sec-hdr">🕐 Recent Audits</div>', unsafe_allow_html=True)
            for h in hist[:5]:
                _, hcol = score_label(h["score"])
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:10px 16px;background:#0e1120;border:1px solid rgba(140,120,255,.18);
                            border-radius:10px;margin:5px 0;">
                    <div>
                        <div style="font-size:13px;font-weight:600;color:#eef0ff;">{h['domain']}</div>
                        <div style="font-size:11px;color:#64748b;">{h['url'][:50]}...</div>
                    </div>
                    <div style="font-size:20px;font-weight:800;color:{hcol};">{h['score']}</div>
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Dashboard":
    import plotly.graph_objects as go
    import plotly.express as px

    raw   = st.session_state.raw_data
    audit = st.session_state.audit
    ai    = st.session_state.ai or {}
    score = audit["overall_score"]
    lbl, scol = score_label(score)
    counts = issue_counts(audit)

    # Header
    st.markdown(f"""
    <div class="page-hdr">
        <h1>📊 SEO Dashboard</h1>
    </div>
    <div class="url-bar">
        <span>🌐</span>
        <span>{raw['url']}</span>
        <span style="margin-left:auto;display:flex;gap:8px;">
            <span class="tag {'tag-green' if raw.get('is_https') else 'tag-red'}">
                {'🔒 HTTPS' if raw.get('is_https') else '⚠️ HTTP'}
            </span>
            <span class="tag tag-blue">HTTP {raw.get('status_code',0)}</span>
            <span class="tag tag-gray">⏱ {raw.get('load_time_seconds',0)}s</span>
        </span>
    </div>
    """, unsafe_allow_html=True)

    # ── Score + issue counts ──────────────────────────────────────────────────
    sc1, sc2, sc3, sc4, sc5 = st.columns([2,1,1,1,1])
    with sc1:
        bar_color = scol
        # Progress ring via SVG
        pct = score / 100
        r = 52; cx = cy = 60; stroke = 10
        circumf = 2 * 3.14159 * r
        dash_arr = f"{circumf * pct:.1f} {circumf}"
        grade = ai.get("improvements",{}).get("overall_grade","?") if ai else "?"
        st.markdown(f"""
        <div class="score-gauge">
            <svg width="120" height="120" viewBox="0 0 120 120" style="margin:0 auto;display:block;">
                <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#f1f5f9" stroke-width="{stroke}"/>
                <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{bar_color}"
                    stroke-width="{stroke}" stroke-dasharray="{dash_arr}"
                    stroke-dashoffset="{circumf*0.25:.1f}"
                    stroke-linecap="round" transform="rotate(-90 {cx} {cy})"/>
                <text x="{cx}" y="{cy+6}" text-anchor="middle"
                    font-size="28" font-weight="900" fill="{bar_color}">{score}</text>
            </svg>
            <div class="score-label" style="color:{bar_color};">{lbl}</div>
            <div class="score-sub">SEO Score / 100{(' · Grade ' + grade) if grade != '?' else ''}</div>
        </div>
        """, unsafe_allow_html=True)

    for cw, sev, icon, color in [
        (sc2,"critical","❌","#ef4444"),
        (sc3,"warning","⚠️","#f59e0b"),
        (sc4,"info","ℹ️","#3b82f6"),
        (sc5,"pass","✅","#22c55e"),
    ]:
        with cw:
            st.markdown(f"""
            <div style="background:#0e1120;border-radius:14px;padding:20px;text-align:center;
                        border:1px solid rgba(140,120,255,.18);box-shadow:0 2px 6px rgba(0,0,0,0.05);
                        border-top:3px solid {color};">
                <div style="font-size:26px;">{icon}</div>
                <div style="font-size:30px;font-weight:900;color:{color};line-height:1;">{counts[sev]}</div>
                <div style="font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;margin-top:4px;">{sev}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Radar + Category scores ───────────────────────────────────────────────
    ch1, ch2 = st.columns([3,2])
    cats_order = ["Meta","Headings","Keywords","Technical","Images","Links"]
    cat_keys   = ["meta","headings","keywords","technical","images","links"]
    cat_icons  = ["🏷️","📝","🔑","⚙️","🖼️","🔗"]
    scores_list = [audit[k]["score"] for k in cat_keys]

    with ch1:
        fig = go.Figure(go.Scatterpolar(
            r=scores_list + [scores_list[0]],
            theta=cats_order + [cats_order[0]],
            fill="toself", fillcolor="rgba(79,70,229,0.12)",
            line=dict(color="#4f46e5",width=2.5),
            marker=dict(size=7,color="#4f46e5",
                        symbol="circle",
                        line=dict(width=2,color="white")),
            hovertemplate="%{theta}: %{r}/100<extra></extra>",
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True,range=[0,100],
                                gridcolor="rgba(140,120,255,.14)",tickfont=dict(size=10,color="#8a90bf")),
                angularaxis=dict(gridcolor="rgba(140,120,255,.14)",
                                 tickfont=dict(size=12,color="#c9cdf2"))
            ),
            showlegend=False,
            margin=dict(l=40,r=40,t=30,b=30),
            height=320, paper_bgcolor="rgba(0,0,0,0)",
        )
        st.markdown('<div class="sec-hdr">📡 SEO Performance Radar</div>', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)

    with ch2:
        st.markdown('<div class="sec-hdr">📂 Category Breakdown</div>', unsafe_allow_html=True)
        for cat, key, icon in zip(cats_order, cat_keys, cat_icons):
            s = audit[key]["score"]
            bar_c = "#22c55e" if s>=70 else ("#f59e0b" if s>=50 else "#ef4444")
            crit = sum(1 for i in audit[key]["issues"] if i["severity"]=="critical")
            warn = sum(1 for i in audit[key]["issues"] if i["severity"]=="warning")
            badges = ""
            if crit: badges += f'<span style="font-size:10px;color:#ef4444;font-weight:700;">❌{crit}</span> '
            if warn: badges += f'<span style="font-size:10px;color:#f59e0b;font-weight:700;">⚠️{warn}</span>'
            st.markdown(f"""
            <div class="cat-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-size:13px;font-weight:600;color:#c9cdf2;">{icon} {cat}</div>
                        <div style="margin-top:2px;">{badges}</div>
                    </div>
                    <div style="font-size:26px;font-weight:800;color:{bar_c};">{s}</div>
                </div>
                <div class="cat-bar">
                    <div class="cat-bar-fill" style="width:{s}%;background:{bar_c};"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Page metrics ──────────────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr">📋 Page Metrics</div>', unsafe_allow_html=True)
    m1,m2,m3,m4,m5,m6,m7 = st.columns(7)
    lt = raw.get("load_time_seconds",0)
    lt_color = "#22c55e" if lt<1.5 else ("#f59e0b" if lt<3 else "#ef4444")
    for cw, val, lbl_, vc in [
        (m1, f"{lt}s","Load Time", lt_color),
        (m2, raw.get("status_code",0),"HTTP Status","#22c55e" if raw.get("status_code")==200 else "#ef4444"),
        (m3, f"{raw.get('html_size_kb',0)} KB","HTML Size","#0f172a"),
        (m4, f"{raw.get('word_count',0):,}","Word Count","#0f172a"),
        (m5, len(raw.get("images",[])),"Images","#0f172a"),
        (m6, len(raw.get("internal_links",[])),"Int. Links","#0f172a"),
        (m7, len(raw.get("external_links",[])),"Ext. Links","#0f172a"),
    ]:
        with cw:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-val" style="color:{vc};">{val}</div>
                <div class="metric-lbl">{lbl_}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Issue chart ───────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    ic1, ic2 = st.columns([3,2])
    with ic1:
        st.markdown('<div class="sec-hdr">🔎 Issues by Category</div>', unsafe_allow_html=True)
        fig2 = go.Figure()
        for sev, color in [("critical","#ef4444"),("warning","#f59e0b"),("info","#3b82f6")]:
            vals = [sum(1 for i in audit[k].get("issues",[]) if i["severity"]==sev) for k in cat_keys]
            fig2.add_trace(go.Bar(name=sev.title(), x=cats_order, y=vals,
                                  marker_color=color, marker_line_width=0))
        fig2.update_layout(barmode="stack",plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
                           margin=dict(l=20,r=20,t=10,b=20),height=240,
                           xaxis=dict(showgrid=False),
                           yaxis=dict(showgrid=True,gridcolor="rgba(140,120,255,.10)"),
                           legend=dict(orientation="h",yanchor="bottom",y=1.02,
                                       font=dict(size=12)))
        st.plotly_chart(fig2, use_container_width=True)

    with ic2:
        st.markdown('<div class="sec-hdr">🎯 Score vs Benchmark</div>', unsafe_allow_html=True)
        benchmarks = {"Your Site":score,"Industry Avg":62,"Good":75,"Excellent":85}
        for name, val in benchmarks.items():
            bc = "#4f46e5" if name=="Your Site" else ("#22c55e" if val>=75 else "#94a3b8")
            st.markdown(f"""
            <div class="comp-row">
                <div class="comp-lbl">{name}</div>
                <div class="comp-bar-wrap">
                    <div class="comp-bar-fill" style="width:{val}%;background:{bc};"></div>
                </div>
                <div class="comp-val" style="color:{bc};">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Issues list ───────────────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr">🐛 Full Issue Report</div>', unsafe_allow_html=True)
    sev_filter = st.multiselect(
        "Show:", ["critical","warning","info","pass"],
        default=["critical","warning"],
        format_func=lambda x: {"critical":"❌ Critical","warning":"⚠️ Warning",
                                "info":"ℹ️ Info","pass":"✅ Passed"}[x],
    )
    for cat, key, icon in zip(cats_order, cat_keys, cat_icons):
        shown = [i for i in audit[key].get("issues",[]) if i.get("severity") in sev_filter]
        if not shown: continue
        score_ = audit[key]["score"]
        sc_ = "#22c55e" if score_>=70 else ("#f59e0b" if score_>=50 else "#ef4444")
        with st.expander(f"{icon} {cat}  —  {score_}/100  ({len(shown)} shown)"):
            for i_iss, iss in enumerate(shown):
                sev   = iss.get("severity","info")
                icons = {"critical":"❌","warning":"⚠️","info":"ℹ️","pass":"✅"}
                css   = {"critical":"iss-critical","warning":"iss-warning","info":"iss-info","pass":"iss-pass"}
                safe  = iss["message"].replace("<","&lt;").replace(">","&gt;")
                fix_  = iss.get("fix","").replace("<","&lt;")
                guide = get_fix_guide(iss["message"])

                st.markdown(f"""
                <div class="{css.get(sev,'iss-info')}">
                    <div class="iss-title">{icons.get(sev,'ℹ️')} {safe}</div>
                    {"<div class='iss-fix'>🔧 " + fix_ + "</div>" if fix_ else ""}
                </div>
                """, unsafe_allow_html=True)

                # Show "How to Fix" guide for actionable issues
                if guide and sev in ("critical","warning"):
                    with st.expander(f"📖 How to Fix This →  {guide['title']}", expanded=False):
                        _render_fix_guide(guide)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AI SUGGESTIONS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🤖 AI Suggestions":
    ai    = st.session_state.ai or {}
    audit = st.session_state.audit

    st.markdown('<div class="page-hdr"><h1>🤖 AI SEO Recommendations</h1><p>GPT-4o powered action plan — prioritised by impact and effort</p></div>', unsafe_allow_html=True)

    if not ai or not any(ai.values()):
        st.info("💡 AI analysis was not run. Go to 🔍 Audit and enable 'AI Analysis'.")
        st.stop()

    impr = ai.get("improvements",{})

    if not impr.get("error") and impr:
        grade = impr.get("overall_grade","?")
        grade_color = {"A":"#22c55e","B":"#84cc16","C":"#f59e0b","D":"#f97316","F":"#ef4444"}.get(grade,"#6b7280")
        summary = impr.get("executive_summary","")
        priorities = impr.get("top_3_priorities",[])

        # Grade + summary
        st.markdown(f"""
        <div style="background:#0e1120;border:2px solid {grade_color};border-radius:16px;
                    padding:20px 24px;margin-bottom:20px;
                    box-shadow:0 4px 16px rgba(0,0,0,0.07);">
            <div style="display:flex;align-items:flex-start;gap:20px;">
                <div style="text-align:center;flex-shrink:0;">
                    <div style="font-size:56px;font-weight:900;color:{grade_color};line-height:1;">{grade}</div>
                    <div style="font-size:11px;color:#94a3b8;font-weight:600;">SEO GRADE</div>
                </div>
                <div>
                    <div style="font-size:16px;font-weight:700;color:#eef0ff;margin-bottom:6px;">Executive Summary</div>
                    <div style="font-size:14px;color:#c9cdf2;line-height:1.7;">{summary}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Top 3 priorities
        if priorities:
            st.markdown('<div class="sec-hdr">🎯 Top 3 Priorities — Fix These First</div>', unsafe_allow_html=True)
            pc = st.columns(3)
            for i, (col, p) in enumerate(zip(pc, priorities), 1):
                with col:
                    colors_p = ["#ef4444","#f59e0b","#3b82f6"]
                    st.markdown(f"""
                    <div style="background:#0e1120;border:2px solid {colors_p[i-1]};border-radius:14px;
                                padding:18px;text-align:center;height:100%;
                                box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                        <div style="font-size:28px;font-weight:900;color:{colors_p[i-1]};margin-bottom:8px;">#{i}</div>
                        <div style="font-size:13px;font-weight:600;color:#eef0ff;line-height:1.5;">{p}</div>
                    </div>
                    """, unsafe_allow_html=True)

    # Tabs
    t1, t2, t3 = st.tabs(["⚡ Action Plan", "✍️ Content & Copy", "🎨 UX & Engagement"])

    with t1:
        def _action_cards(items, icon):
            for item in items:
                imp = item.get("impact","Medium")
                imp_cls = {"High":"badge-high","Medium":"badge-med","Low":"badge-low"}.get(imp,"badge-med")
                detail = item.get("detail","")
                st.markdown(f"""
                <div class="ai-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;">
                        <div class="ai-title">{icon} {item.get('action','')}</div>
                        <div style="display:flex;gap:6px;flex-shrink:0;">
                            <span class="{imp_cls}">{imp} impact</span>
                        </div>
                    </div>
                    <div class="ai-body">{detail}</div>
                </div>
                """, unsafe_allow_html=True)

        qw = impr.get("quick_wins",[])
        st_term = impr.get("short_term",[])
        lt_term = impr.get("long_term",[])

        st.markdown('<div class="sec-hdr">⚡ Quick Wins — Do These Today (Low Effort, High Impact)</div>', unsafe_allow_html=True)
        _action_cards(qw, "⚡") if qw else st.info("No quick wins data.")

        ac1, ac2 = st.columns(2)
        with ac1:
            st.markdown('<div class="sec-hdr">📅 Short-Term (1-4 Weeks)</div>', unsafe_allow_html=True)
            _action_cards(st_term, "📅") if st_term else st.info("No short-term data.")
        with ac2:
            st.markdown('<div class="sec-hdr">🚀 Long-Term Strategy</div>', unsafe_allow_html=True)
            _action_cards(lt_term, "🚀") if lt_term else st.info("No long-term data.")

    with t2:
        content = ai.get("content",{})
        if content.get("error"):
            st.error(f"AI error: {content['error']}")
        elif content:
            cc1, cc2 = st.columns(2)
            with cc1:
                st.markdown('<div class="sec-hdr">📝 Optimised Title Options</div>', unsafe_allow_html=True)
                for i, t_ in enumerate(content.get("title_options",[]), 1):
                    chars = len(t_)
                    ok = 50 <= chars <= 60
                    color = "#22c55e" if ok else "#f59e0b"
                    tag   = "✅ Optimal" if ok else f"⚠️ {chars} chars"
                    st.markdown(f"""
                    <div style="background:#0e1120;border:1px solid {'#bbf7d0' if ok else '#fde68a'};
                                border-radius:10px;padding:14px 16px;margin:6px 0;">
                        <div style="font-size:13px;font-weight:600;color:#eef0ff;margin-bottom:4px;">
                            Option {i}
                        </div>
                        <div style="font-size:14px;color:#8ab4f8;">{t_}</div>
                        <div style="font-size:11px;color:{color};margin-top:5px;font-weight:600;">{tag}</div>
                    </div>
                    """, unsafe_allow_html=True)

            with cc2:
                st.markdown('<div class="sec-hdr">📄 Meta Description Options</div>', unsafe_allow_html=True)
                for i, d_ in enumerate(content.get("description_options",[]), 1):
                    chars = len(d_)
                    ok = 150 <= chars <= 160
                    color = "#22c55e" if ok else "#f59e0b"
                    tag   = "✅ Optimal" if ok else f"⚠️ {chars} chars"
                    st.markdown(f"""
                    <div style="background:#0e1120;border:1px solid {'#bbf7d0' if ok else '#fde68a'};
                                border-radius:10px;padding:14px 16px;margin:6px 0;">
                        <div style="font-size:13px;font-weight:600;color:#eef0ff;margin-bottom:4px;">
                            Option {i}
                        </div>
                        <div style="font-size:13px;color:#4d5156;line-height:1.5;">{d_}</div>
                        <div style="font-size:11px;color:{color};margin-top:5px;font-weight:600;">{tag}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            co1, co2 = st.columns(2)
            with co1:
                st.markdown('<div class="sec-hdr">💡 Content Improvements</div>', unsafe_allow_html=True)
                for s in content.get("content_suggestions",[]):
                    st.markdown(f'<div class="ai-card"><div class="ai-body">💡 {s}</div></div>', unsafe_allow_html=True)
                if content.get("content_gaps"):
                    st.markdown('<div class="sec-hdr">🕳️ Content Gaps to Fill</div>', unsafe_allow_html=True)
                    for g in content.get("content_gaps",[]):
                        st.markdown(f'<div class="ai-card"><div class="ai-body">📌 {g}</div></div>', unsafe_allow_html=True)
            with co2:
                st.markdown('<div class="sec-hdr">📢 CTA Improvements</div>', unsafe_allow_html=True)
                for c in content.get("cta_improvements",[]):
                    st.markdown(f'<div class="ai-card"><div class="ai-body">📢 {c}</div></div>', unsafe_allow_html=True)
                if content.get("primary_keyword"):
                    st.markdown(f"""
                    <div style="background:linear-gradient(135deg,#eff6ff,#e0f2fe);
                                border:2px solid #bfdbfe;border-radius:12px;padding:16px 20px;margin-top:12px;">
                        <div style="font-weight:700;color:#1d4ed8;margin-bottom:4px;">🎯 Primary Keyword Target</div>
                        <div style="font-size:20px;font-weight:800;color:#1e40af;">"{content['primary_keyword']}"</div>
                        <div style="font-size:13px;color:#c9cdf2;margin-top:6px;">{content.get('keyword_reasoning','')}</div>
                    </div>
                    """, unsafe_allow_html=True)

    with t3:
        ux = ai.get("ux",{})
        if ux.get("error"):
            st.error(f"AI error: {ux['error']}")
        elif ux:
            ux1, ux2 = st.columns(2)
            with ux1:
                for hdr, key, icon in [
                    ("📖 Readability Tips","readability_tips","📖"),
                    ("📱 Mobile UX","mobile_ux_tips","📱"),
                ]:
                    st.markdown(f'<div class="sec-hdr">{hdr}</div>', unsafe_allow_html=True)
                    for tip in ux.get(key,[]):
                        st.markdown(f'<div class="ai-card"><div class="ai-body">• {tip}</div></div>', unsafe_allow_html=True)
            with ux2:
                for hdr, key in [
                    ("🧭 Navigation","navigation_suggestions"),
                    ("🤝 Trust Signals","trust_signals"),
                    ("🎯 Engagement","engagement_improvements"),
                ]:
                    tips = ux.get(key,[])
                    if tips:
                        st.markdown(f'<div class="sec-hdr">{hdr}</div>', unsafe_allow_html=True)
                        for tip in tips:
                            st.markdown(f'<div class="ai-card"><div class="ai-body">• {tip}</div></div>', unsafe_allow_html=True)

            if ux.get("page_structure_advice"):
                st.markdown(f"""
                <div style="background:rgba(52,211,153,.12);border:1px solid #86efac;border-radius:12px;
                            padding:16px 20px;margin-top:14px;">
                    <div style="font-weight:700;color:#6ee7b7;margin-bottom:6px;">🏗️ Page Structure Advice</div>
                    <div style="font-size:13px;color:#c9cdf2;line-height:1.65;">{ux['page_structure_advice']}</div>
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: KEYWORDS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Keywords":
    import plotly.graph_objects as go

    audit  = st.session_state.audit
    ai     = st.session_state.ai or {}
    kw_data = audit.get("keywords",{})
    ai_kw   = ai.get("keywords",{})

    st.markdown('<div class="page-hdr"><h1>📈 Keyword Analysis</h1><p>Keywords found on your page + AI-suggested targets</p></div>', unsafe_allow_html=True)

    kk1, kk2 = st.columns([3,2])
    with kk1:
        top = kw_data.get("top_keywords",[])
        if top:
            st.markdown('<div class="sec-hdr">🔤 Top 15 Keywords Found on Page</div>', unsafe_allow_html=True)
            words = [k for k,_ in top[:15]]
            freqs = [c for _,c in top[:15]]
            max_f = max(freqs) if freqs else 1
            norm  = [f/max_f for f in freqs]
            bar_colors = [f"rgba(79,70,229,{0.4 + 0.6*n:.2f})" for n in norm]
            fig = go.Figure(go.Bar(
                x=freqs, y=words, orientation="h",
                marker_color=bar_colors, marker_line_width=0,
                hovertemplate="%{y}: %{x} occurrences<extra></extra>",
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10,r=20,t=10,b=20), height=420,
                xaxis=dict(showgrid=True,gridcolor="rgba(140,120,255,.10)",title="Frequency"),
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig, use_container_width=True)

    with kk2:
        st.markdown('<div class="sec-hdr">📊 Keyword Health</div>', unsafe_allow_html=True)
        wc = kw_data.get("word_count",0)
        wc_color = "#22c55e" if wc>=1500 else ("#f59e0b" if wc>=500 else "#ef4444")
        st.markdown(f"""
        <div class="metric-box" style="margin-bottom:10px;border-top:3px solid {wc_color};">
            <div class="metric-val" style="color:{wc_color};">{wc:,}</div>
            <div class="metric-lbl">Total Words on Page</div>
            <div style="font-size:11px;color:#94a3b8;margin-top:4px;">
                {'✅ Long-form' if wc>=1500 else ('⚠️ Medium' if wc>=500 else '❌ Too short')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Keyword placement checks
        checks = [
            ("In Title", bool(kw_data.get("keywords_in_title"))),
            ("In Description", bool(kw_data.get("keywords_in_desc"))),
            ("Density OK", not bool(kw_data.get("density_issues"))),
        ]
        for lbl_, ok in checks:
            icon = "✅" if ok else "❌"
            color = "#22c55e" if ok else "#ef4444"
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:9px 14px;
                        background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:8px;margin:4px 0;">
                <span style="font-size:13px;font-weight:500;color:#c9cdf2;">{lbl_}</span>
                <span style="font-size:14px;color:{color};font-weight:700;">{icon}</span>
            </div>
            """, unsafe_allow_html=True)

        if kw_data.get("density_issues"):
            st.markdown('<div class="sec-hdr">⚠️ Density Issues</div>', unsafe_allow_html=True)
            for d in kw_data["density_issues"]:
                st.warning(d)

    # AI Keyword strategy
    if ai_kw and not ai_kw.get("error"):
        st.markdown('<div class="sec-hdr">🤖 AI Keyword Strategy</div>', unsafe_allow_html=True)
        sk1, sk2 = st.columns(2)
        with sk1:
            st.markdown("**🎯 Recommended Target Keywords**")
            for kw in ai_kw.get("primary_keywords",[]):
                diff = kw.get("difficulty","Medium")
                diff_c = {"Low":"#22c55e","Medium":"#f59e0b","High":"#ef4444"}.get(diff,"#6b7280")
                kw_type = kw.get("type","")
                st.markdown(f"""
                <div class="ai-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <div>
                            <div style="font-size:15px;font-weight:700;color:#eef0ff;">"{kw.get('keyword','')}"</div>
                            <div style="font-size:11px;color:#94a3b8;margin-top:2px;">{kw_type}</div>
                        </div>
                        <span style="font-size:11px;font-weight:600;color:{diff_c};white-space:nowrap;">
                            {diff} difficulty
                        </span>
                    </div>
                    <div class="ai-body" style="margin-top:8px;">{kw.get('rationale','')}</div>
                </div>
                """, unsafe_allow_html=True)

        with sk2:
            st.markdown("**🔍 Long-tail Opportunities**")
            for lt in ai_kw.get("long_tail_opportunities",[]):
                st.markdown(f'<div class="ai-card"><div class="ai-body">🔍 {lt}</div></div>', unsafe_allow_html=True)
            if ai_kw.get("semantic_keywords"):
                st.markdown("**🔗 Semantic / LSI Keywords**")
                html = "".join(f'<span class="kw-badge">{s}</span>' for s in ai_kw.get("semantic_keywords",[]))
                st.markdown(html, unsafe_allow_html=True)

        if ai_kw.get("content_ideas"):
            st.markdown('<div class="sec-hdr">💡 Content Ideas to Target These Keywords</div>', unsafe_allow_html=True)
            ci_cols = st.columns(2)
            for i, idea in enumerate(ai_kw.get("content_ideas",[])):
                with ci_cols[i%2]:
                    st.markdown(f"""
                    <div class="ai-card">
                        <div class="ai-title">📝 {idea.get('title','')}</div>
                        <div style="font-size:12px;color:#94a3b8;margin-bottom:4px;">{idea.get('type','')}</div>
                        <div style="font-size:12px;color:#c9cdf2;">
                            Target: <span class="kw-badge" style="font-size:11px;">{idea.get('target_keyword','')}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        if ai_kw.get("local_seo_tip"):
            st.markdown(f"""
            <div style="background:rgba(251,191,36,.12);border:1px solid #fde68a;border-radius:12px;
                        padding:14px 18px;margin-top:12px;">
                <div style="font-weight:700;color:#fcd34d;margin-bottom:4px;">📍 Local SEO Tip</div>
                <div style="font-size:13px;color:#c9cdf2;">{ai_kw['local_seo_tip']}</div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: TECHNICAL
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Technical":
    raw   = st.session_state.raw_data
    audit = st.session_state.audit
    ai    = st.session_state.ai or {}
    tech  = audit.get("technical",{})
    imgs  = audit.get("images",{})
    links = audit.get("links",{})
    ai_tech = ai.get("technical",{})

    st.markdown('<div class="page-hdr"><h1>⚙️ Technical SEO Audit</h1><p>Performance, security, crawlability, and accessibility</p></div>', unsafe_allow_html=True)

    # Tech score cards
    tc1,tc2,tc3,tc4,tc5 = st.columns(5)
    lt = tech.get("load_time_seconds",0)
    for cw, val, lbl_, good in [
        (tc1, f"{lt}s","Load Time", lt<3),
        (tc2, tech.get("status_code",0),"HTTP Status", tech.get("status_code",0)==200),
        (tc3, "✅ Yes" if tech.get("is_https") else "❌ No","HTTPS", tech.get("is_https",False)),
        (tc4, "✅ Yes" if tech.get("has_schema") else "❌ No","Schema.org", tech.get("has_schema",False)),
        (tc5, f"{tech.get('html_size_kb',0)} KB","HTML Size", tech.get("html_size_kb",0)<300),
    ]:
        with cw:
            color = "#22c55e" if good else "#ef4444"
            st.markdown(f"""
            <div style="background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:12px;
                        padding:16px;text-align:center;border-top:3px solid {color};">
                <div style="font-size:20px;font-weight:800;color:{color};">{val}</div>
                <div style="font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;margin-top:4px;">{lbl_}</div>
            </div>
            """, unsafe_allow_html=True)

    # Speed indicator
    st.markdown("<br>", unsafe_allow_html=True)
    speed_pct = max(0, min(100, int((3 - lt) / 3 * 100))) if lt <= 3 else 0
    speed_color = "#22c55e" if lt<1.5 else ("#f59e0b" if lt<3 else "#ef4444")
    speed_label = "🚀 Excellent" if lt<1.5 else ("✅ Good" if lt<3 else ("⚠️ Slow" if lt<5 else "❌ Very Slow"))
    st.markdown(f"""
    <div style="background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:14px;padding:20px 24px;margin-bottom:16px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <div style="font-weight:700;color:#eef0ff;">⏱ Page Load Speed</div>
            <div style="font-size:18px;font-weight:800;color:{speed_color};">{lt}s — {speed_label}</div>
        </div>
        <div style="background:#1c2036;border-radius:6px;height:10px;">
            <div style="width:{speed_pct}%;background:{speed_color};border-radius:6px;height:10px;transition:width 0.5s;"></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:11px;color:#94a3b8;margin-top:5px;">
            <span>0s</span><span>1.5s (target)</span><span>3s</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tcol1, tcol2 = st.columns(2)
    with tcol1:
        st.markdown('<div class="sec-hdr">⚙️ Technical Issues</div>', unsafe_allow_html=True)
        for iss in tech.get("issues",[]):
            sev = iss.get("severity","info")
            ic  = {"critical":"❌","warning":"⚠️","info":"ℹ️","pass":"✅"}.get(sev,"ℹ️")
            cs  = {"critical":"iss-critical","warning":"iss-warning","info":"iss-info","pass":"iss-pass"}.get(sev,"iss-info")
            safe = iss["message"].replace("<","&lt;")
            fix  = iss.get("fix","").replace("<","&lt;")
            st.markdown(f"""
            <div class="{cs}">
                <div class="iss-title">{ic} {safe}</div>
                {"<div class='iss-fix'>🔧 "+fix+"</div>" if fix else ""}
            </div>
            """, unsafe_allow_html=True)

    with tcol2:
        st.markdown('<div class="sec-hdr">🖼️ Images & Links</div>', unsafe_allow_html=True)
        stats = [
            ("🖼️ Total Images", imgs.get("total_images",0), False),
            ("⚠️ Missing Alt Text", imgs.get("missing_alt",0), True),
            ("✅ Lazy Loaded", imgs.get("lazy_loaded",0), False),
            ("📏 Missing Width/Height", imgs.get("no_size",0), True),
            ("🔗 Internal Links", links.get("internal_count",0), False),
            ("🌐 External Links", links.get("external_count",0), False),
            ("❌ Empty Anchors", links.get("empty_anchor",0), True),
            ("🔄 Redirect Hops", tech.get("redirect_count",0), True),
        ]
        for lbl_, val, is_bad in stats:
            color = "#ef4444" if (is_bad and val > 0) else "#0f172a"
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:8px 14px;
                        background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:8px;margin:3px 0;">
                <span style="font-size:13px;color:#c9cdf2;">{lbl_}</span>
                <strong style="font-size:13px;color:{color};">{val}</strong>
            </div>
            """, unsafe_allow_html=True)

    # AI guidance
    if ai_tech and not ai_tech.get("error"):
        st.markdown('<div class="sec-hdr">🤖 AI Technical Guidance</div>', unsafe_allow_html=True)
        atc1, atc2 = st.columns(2)
        with atc1:
            st.markdown("**⚡ Performance Fixes**")
            for fix in ai_tech.get("performance_fixes",[]):
                pri = fix.get("priority","Medium")
                pc  = {"High":"#ef4444","Medium":"#f59e0b","Low":"#22c55e"}.get(pri,"#6b7280")
                st.markdown(f"""
                <div class="ai-card">
                    <div style="display:flex;justify-content:space-between;gap:8px;">
                        <div class="ai-title">⚡ {fix.get('fix','')}</div>
                        <span style="font-size:11px;color:{pc};font-weight:700;white-space:nowrap;">{pri}</span>
                    </div>
                    <div class="ai-body">{fix.get('instruction','')}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("**📐 Core Web Vitals**")
            for cwv in ai_tech.get("core_web_vitals",[]):
                st.markdown(f"""
                <div class="ai-card">
                    <div class="ai-title">{cwv.get('metric','')}</div>
                    <div class="ai-body">{cwv.get('tip','')}</div>
                </div>
                """, unsafe_allow_html=True)

        with atc2:
            st.markdown("**🖼️ Image Optimisation**")
            for tip in ai_tech.get("image_optimisation",[]):
                st.markdown(f'<div class="ai-card"><div class="ai-body">🖼️ {tip}</div></div>', unsafe_allow_html=True)

            if ai_tech.get("schema_recommendation"):
                st.markdown("**📊 Schema.org Recommendation**")
                st.markdown(f'<div class="ai-card"><div class="ai-body">{ai_tech["schema_recommendation"]}</div></div>', unsafe_allow_html=True)

            for lbl_, key in [("🤖 Robots.txt","robots_txt"),("🗺️ Sitemap","sitemap")]:
                if ai_tech.get(key):
                    st.markdown(f"**{lbl_}**")
                    st.markdown(f'<div class="ai-card"><div class="ai-body">{ai_tech[key]}</div></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SERP PREVIEW
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👁️ SERP Preview":
    raw   = st.session_state.raw_data
    audit = st.session_state.audit
    ai    = st.session_state.ai or {}

    meta  = audit.get("meta",{})
    content_ai = ai.get("content",{})

    st.markdown('<div class="page-hdr"><h1>👁️ SERP & Social Preview</h1><p>See exactly how your page looks in Google, Facebook, Twitter, and LinkedIn</p></div>', unsafe_allow_html=True)

    # ── Current vs Optimised toggle ───────────────────────────────────────────
    view_mode = st.radio("Show:", ["Current Page", "AI Optimised Version"],
                         horizontal=True, key="serp_mode")

    if view_mode == "AI Optimised Version" and content_ai.get("title_options"):
        title_opts = content_ai.get("title_options", [])
        desc_opts  = content_ai.get("description_options", [])
        display_title = title_opts[0] if title_opts else meta.get("title","")
        display_desc  = desc_opts[0]  if desc_opts  else meta.get("description","")
        st.info("💡 Showing first AI-recommended option. Go to 🤖 AI Suggestions to see all options.")
    else:
        display_title = meta.get("title","")
        display_desc  = meta.get("description","")

    url_display = raw.get("url","")
    domain      = raw.get("domain","")

    # ── Google SERP Preview ───────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr">🔍 Google Search Result Preview</div>', unsafe_allow_html=True)

    title_len = len(display_title)
    desc_len  = len(display_desc)
    title_ok  = 50 <= title_len <= 60
    desc_ok   = 150 <= desc_len <= 160

    # Visual SERP
    title_color = "#1a0dab" if title_len <= 60 else "#c0392b"
    truncated_title = display_title[:57] + "..." if title_len > 60 else display_title
    truncated_desc  = display_desc[:157]  + "..." if desc_len  > 157 else display_desc

    st.markdown(f"""
    <div class="serp-box">
        <div style="font-size:14px;color:#202124;margin-bottom:6px;display:flex;align-items:center;gap:8px;">
            <div style="width:18px;height:18px;background:#4f46e5;border-radius:50%;
                        display:inline-flex;align-items:center;justify-content:center;
                        font-size:10px;color:white;font-weight:700;flex-shrink:0;">G</div>
            <span style="color:#202124;">{domain}</span>
            <span style="color:#70757a;">›</span>
            <span style="color:#70757a;font-size:13px;">{url_display[:50]}{'...' if len(url_display)>50 else ''}</span>
        </div>
        <div class="serp-url">https://{domain}</div>
        <div class="serp-title" style="color:{title_color};">{truncated_title if truncated_title else '(No title set)'}</div>
        <div class="serp-desc">{truncated_desc if truncated_desc else '(No meta description — Google will auto-generate one from page content, which is often less effective.)'}</div>
    </div>
    """, unsafe_allow_html=True)

    # Title & description meter
    mc1, mc2 = st.columns(2)
    with mc1:
        tc = "#22c55e" if title_ok else "#f59e0b"
        st.markdown(f"""
        <div style="background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:10px;padding:14px;margin-top:8px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                <span style="font-size:13px;font-weight:600;color:#c9cdf2;">Title Length</span>
                <span style="font-size:13px;font-weight:700;color:{tc};">{title_len}/60 chars — {'✅ Optimal' if title_ok else '⚠️ Adjust'}</span>
            </div>
            <div style="background:#1c2036;border-radius:4px;height:6px;">
                <div style="width:{min(100,title_len/60*100):.0f}%;background:{tc};border-radius:4px;height:6px;"></div>
            </div>
            <div style="font-size:11px;color:#94a3b8;margin-top:4px;">Target: 50-60 characters</div>
        </div>
        """, unsafe_allow_html=True)
    with mc2:
        dc = "#22c55e" if desc_ok else "#f59e0b"
        st.markdown(f"""
        <div style="background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:10px;padding:14px;margin-top:8px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                <span style="font-size:13px;font-weight:600;color:#c9cdf2;">Description Length</span>
                <span style="font-size:13px;font-weight:700;color:{dc};">{desc_len}/160 chars — {'✅ Optimal' if desc_ok else '⚠️ Adjust'}</span>
            </div>
            <div style="background:#1c2036;border-radius:4px;height:6px;">
                <div style="width:{min(100,desc_len/160*100):.0f}%;background:{dc};border-radius:4px;height:6px;"></div>
            </div>
            <div style="font-size:11px;color:#94a3b8;margin-top:4px;">Target: 150-160 characters</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Social Media Previews ─────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr">📱 Social Media Previews</div>', unsafe_allow_html=True)

    og = meta.get("og_tags",{})
    tw = meta.get("twitter_tags",{})
    og_title = og.get("og:title", display_title)
    og_desc  = og.get("og:description", display_desc)
    og_img   = og.get("og:image","")
    tw_title = tw.get("twitter:title", og_title)
    tw_desc  = tw.get("twitter:description", og_desc)

    sp1, sp2 = st.columns(2)

    with sp1:
        st.markdown("**Facebook / LinkedIn**")
        img_html = f'<div style="height:200px;background:linear-gradient(135deg,#e2e8f0,#f8fafc);display:flex;align-items:center;justify-content:center;font-size:40px;">🖼️</div>' if not og_img else f'<img src="{og_img}" style="width:100%;height:200px;object-fit:cover;" onerror="this.style.display=\'none\'">'
        st.markdown(f"""
        <div class="og-card">
            {img_html}
            <div class="og-domain">{domain.upper()}</div>
            <div class="og-title">{(og_title[:60]+'...') if len(og_title)>60 else og_title}</div>
            <div class="og-desc">{(og_desc[:90]+'...') if len(og_desc)>90 else og_desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if not og.get("og:title"):
            st.warning("⚠️ No og:title tag — Facebook will guess from page content")
        if not og.get("og:image"):
            st.warning("⚠️ No og:image tag — posts may show no image")

    with sp2:
        st.markdown("**Twitter / X**")
        img_html_tw = f'<div style="height:200px;background:linear-gradient(135deg,#e2e8f0,#f8fafc);display:flex;align-items:center;justify-content:center;font-size:40px;">🖼️</div>'
        st.markdown(f"""
        <div style="border:1px solid #cfd9de;border-radius:16px;overflow:hidden;max-width:500px;">
            {img_html_tw}
            <div style="padding:12px 14px;background:#0e1120;">
                <div style="font-size:15px;font-weight:700;color:#eef0ff;">{(tw_title[:60]+'...') if len(tw_title)>60 else tw_title}</div>
                <div style="font-size:14px;color:#536471;margin-top:4px;">{(tw_desc[:80]+'...') if len(tw_desc)>80 else tw_desc}</div>
                <div style="font-size:13px;color:#536471;margin-top:6px;">🔗 {domain}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if not tw:
            st.warning("⚠️ No Twitter Card tags found")

    # ── OG Tag Checklist ──────────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr">✅ Open Graph & Twitter Card Checklist</div>', unsafe_allow_html=True)
    oc1, oc2 = st.columns(2)
    og_checks = [
        ("og:title", og.get("og:title","")),
        ("og:description", og.get("og:description","")),
        ("og:image", og.get("og:image","")),
        ("og:url", og.get("og:url","")),
        ("og:type", og.get("og:type","")),
    ]
    tw_checks = [
        ("twitter:card", tw.get("twitter:card","")),
        ("twitter:title", tw.get("twitter:title","")),
        ("twitter:description", tw.get("twitter:description","")),
        ("twitter:image", tw.get("twitter:image","")),
    ]
    with oc1:
        st.markdown("**Open Graph Tags**")
        for tag, val in og_checks:
            ok = bool(val)
            icon = "✅" if ok else "❌"
            preview = f' = "{val[:30]}..."' if ok and len(val)>30 else (f' = "{val}"' if ok else " — not set")
            color = "#22c55e" if ok else "#ef4444"
            st.markdown(f"""
            <div style="padding:7px 12px;background:#0e1120;border:1px solid rgba(140,120,255,.18);
                        border-radius:8px;margin:3px 0;font-size:12px;font-family:monospace;">
                <span style="color:{color};font-weight:700;">{icon}</span>
                <span style="color:#4f46e5;">{tag}</span>
                <span style="color:#64748b;">{preview}</span>
            </div>
            """, unsafe_allow_html=True)
    with oc2:
        st.markdown("**Twitter Card Tags**")
        for tag, val in tw_checks:
            ok = bool(val)
            icon = "✅" if ok else "❌"
            preview = f' = "{val[:30]}..."' if ok and len(val)>30 else (f' = "{val}"' if ok else " — not set")
            color = "#22c55e" if ok else "#ef4444"
            st.markdown(f"""
            <div style="padding:7px 12px;background:#0e1120;border:1px solid rgba(140,120,255,.18);
                        border-radius:8px;margin:3px 0;font-size:12px;font-family:monospace;">
                <span style="color:{color};font-weight:700;">{icon}</span>
                <span style="color:#1da1f2;">{tag}</span>
                <span style="color:#64748b;">{preview}</span>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: FIX GUIDES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔧 Fix Guides":
    audit = st.session_state.audit

    st.markdown("""
    <div class="page-hdr">
        <h1>🔧 How to Fix Your SEO Issues</h1>
        <p>Step-by-step fix instructions with code examples for every issue found on your site</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Priority: show YOUR issues first ──────────────────────────────────────
    your_issues = []
    for cat_name, cat_data in audit.items():
        if not isinstance(cat_data, dict): continue
        for iss in cat_data.get("issues",[]):
            if iss.get("severity") in ("critical","warning"):
                guide = get_fix_guide(iss["message"])
                if guide:
                    your_issues.append({
                        "severity": iss["severity"],
                        "message": iss["message"],
                        "fix": iss.get("fix",""),
                        "category": cat_name.title(),
                        "guide": guide,
                    })

    if your_issues:
        # Sort: critical first
        your_issues.sort(key=lambda x: (0 if x["severity"]=="critical" else 1))

        st.markdown(f'<div class="sec-hdr">🎯 Fix Guides for YOUR {len(your_issues)} Issues</div>', unsafe_allow_html=True)
        st.info(f"Found **{sum(1 for i in your_issues if i['severity']=='critical')} critical** and **{sum(1 for i in your_issues if i['severity']=='warning')} warning** issues with available fix guides.")

        for item in your_issues:
            sev   = item["severity"]
            guide = item["guide"]
            diff  = guide.get("difficulty","Medium")
            time_ = guide.get("time","")
            diff_cls = {"Easy":"fix-easy","Medium":"fix-medium","Hard":"fix-hard"}.get(diff,"fix-medium")
            sev_icon = "❌" if sev=="critical" else "⚠️"
            sev_color = "#ef4444" if sev=="critical" else "#f59e0b"

            with st.expander(
                f"{sev_icon} [{item['category']}] {item['message'][:70]}{'...' if len(item['message'])>70 else ''}",
                expanded=(sev=="critical")
            ):
                st.markdown(f"""
                <div style="display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap;">
                    <span style="background:{sev_color}22;color:{sev_color};border:1px solid {sev_color}44;
                                 padding:2px 10px;border-radius:10px;font-size:11px;font-weight:700;">
                        {sev.upper()}
                    </span>
                    <span class="fix-badge {diff_cls}">🎯 {diff}</span>
                    <span class="fix-badge" style="background:rgba(96,165,250,.12);color:#2563eb;border:1px solid #bfdbfe;">⏱ {time_}</span>
                    <span class="tag tag-gray">📂 {item['category']}</span>
                </div>
                """, unsafe_allow_html=True)

                if item.get("fix"):
                    st.markdown(f"""
                    <div style="background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:8px;
                                padding:10px 14px;margin-bottom:12px;font-size:13px;color:#c9cdf2;">
                        🔧 <strong>Quick fix:</strong> {item['fix']}
                    </div>
                    """, unsafe_allow_html=True)

                _render_fix_guide(guide)

    else:
        st.success("🎉 No critical or warning issues with fix guides available. Your site looks good!")

    # ── Browse all fix guides ─────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">📚 Browse All Fix Guides</div>', unsafe_allow_html=True)

    # Category filter
    all_guides_by_cat = {
        "Meta Tags": ["No <title> tag","Title too short","Title too long","No meta description",
                      "Meta description too short","Meta description too long",
                      "No canonical URL","No viewport meta tag","Page is NOINDEX",
                      "Missing Open Graph tags"],
        "Headings": ["No H1 tag","Multiple H1 tags found","No H2 tags"],
        "Images": ["images missing alt","images missing width/height","Only X/Y images use lazy loading"],
        "Technical": ["NOT using HTTPS","Load time too slow","No structured data","Missing HTML lang attribute"],
        "Links": ["links have no anchor text","Very few internal links"],
        "Keywords": ["Top keywords not in title","Low word count"],
    }

    selected_cat = st.selectbox("Filter by category:", ["All"] + list(all_guides_by_cat.keys()))

    shown_cats = all_guides_by_cat if selected_cat == "All" else {selected_cat: all_guides_by_cat.get(selected_cat,[])}

    for cat_name, guide_keys in shown_cats.items():
        st.markdown(f"""
        <div style="font-size:14px;font-weight:700;color:#4f46e5;padding:8px 0 4px;
                    border-bottom:2px solid #e0e7ff;margin:16px 0 8px;">
            {cat_name}
        </div>
        """, unsafe_allow_html=True)
        for gkey in guide_keys:
            guide = FIX_GUIDES.get(gkey)
            if not guide: continue
            diff = guide.get("difficulty","Medium")
            diff_cls = {"Easy":"fix-easy","Medium":"fix-medium","Hard":"fix-hard"}.get(diff,"fix-medium")
            time_ = guide.get("time","")
            impact = guide.get("impact","Medium")
            impact_color = {"High":"#dc2626","Medium":"#d97706","Low":"#16a34a"}.get(impact,"#64748b")

            with st.expander(f"📖 {guide['title']}"):
                st.markdown(f"""
                <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;">
                    <span class="fix-badge {diff_cls}">🎯 {diff}</span>
                    <span class="fix-badge" style="background:rgba(96,165,250,.12);color:#2563eb;border:1px solid #bfdbfe;">⏱ {time_}</span>
                    <span class="fix-badge" style="background:rgba(251,113,133,.12);color:{impact_color};border:1px solid #fecaca;">⚡ {impact} impact</span>
                </div>
                """, unsafe_allow_html=True)
                _render_fix_guide(guide)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: EXPORT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📤 Export":
    raw   = st.session_state.raw_data
    audit = st.session_state.audit
    ai    = st.session_state.ai or {}

    score = audit.get("overall_score",0)
    lbl, scol = score_label(score)
    domain = raw.get("domain","site").replace(".","_")
    counts = issue_counts(audit)

    st.markdown('<div class="page-hdr"><h1>📤 Export Audit Report</h1><p>Download your complete SEO audit as PDF or Markdown</p></div>', unsafe_allow_html=True)

    # Summary banner
    st.markdown(f"""
    <div style="background:#0e1120;border:2px solid {scol};border-radius:16px;
                padding:20px 24px;margin-bottom:24px;
                box-shadow:0 4px 16px rgba(0,0,0,0.06);">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;">
            <div>
                <div style="font-size:16px;font-weight:700;color:#eef0ff;">Audit Report Ready</div>
                <div style="font-size:13px;color:#64748b;margin-top:3px;">🌐 {raw.get('url','')}</div>
            </div>
            <div style="display:flex;gap:16px;align-items:center;">
                <div style="text-align:center;">
                    <div style="font-size:36px;font-weight:900;color:{scol};">{score}</div>
                    <div style="font-size:11px;color:#64748b;font-weight:600;">{lbl} · /100</div>
                </div>
                <div style="display:flex;gap:8px;flex-wrap:wrap;">
                    <span class="tag tag-red">❌ {counts['critical']} Critical</span>
                    <span class="tag tag-gray">⚠️ {counts['warning']} Warnings</span>
                    <span class="tag tag-green">✅ {counts['pass']} Passed</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    ex1, ex2 = st.columns(2)

    with ex1:
        st.markdown("""
        <div style="background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:16px;
                    padding:28px;text-align:center;margin-bottom:12px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.05);">
            <div style="font-size:52px;margin-bottom:12px;">📄</div>
            <div style="font-weight:700;font-size:17px;color:#eef0ff;margin-bottom:6px;">PDF Report</div>
            <div style="font-size:13px;color:#64748b;line-height:1.6;">
                Professional formatted report with:<br>
                ✅ Score breakdown table<br>
                ✅ All critical issues with fixes<br>
                ✅ AI quick wins & content options<br>
                ✅ Technical recommendations<br>
                ✅ Clean, client-ready formatting
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.spinner("Generating PDF..."):
            pdf_bytes = export_pdf(raw, audit, ai)
        st.download_button(
            "⬇️ Download PDF Report",
            data=pdf_bytes,
            file_name=f"seo_audit_{domain}.pdf",
            mime="application/pdf",
            use_container_width=True, type="primary",
        )

    with ex2:
        st.markdown("""
        <div style="background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:16px;
                    padding:28px;text-align:center;margin-bottom:12px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.05);">
            <div style="font-size:52px;margin-bottom:12px;">📝</div>
            <div style="font-weight:700;font-size:17px;color:#eef0ff;margin-bottom:6px;">Markdown Report</div>
            <div style="font-size:13px;color:#64748b;line-height:1.6;">
                Clean Markdown for:<br>
                ✅ Notion & Obsidian<br>
                ✅ GitHub / GitLab<br>
                ✅ Confluence & Jira<br>
                ✅ Any documentation tool<br>
                ✅ Full transcript of all findings
            </div>
        </div>
        """, unsafe_allow_html=True)
        md_text = export_markdown(raw, audit, ai)
        st.download_button(
            "⬇️ Download Markdown Report",
            data=md_text,
            file_name=f"seo_audit_{domain}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    # Markdown preview
    st.markdown('<div class="sec-hdr">👁️ Report Preview (Markdown)</div>', unsafe_allow_html=True)
    st.text_area("", value=md_text, height=380, label_visibility="collapsed")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔑 Settings":
    st.markdown('<div class="page-hdr"><h1>🔑 Settings</h1><p>Configure your OpenAI API key to enable AI-powered recommendations</p></div>', unsafe_allow_html=True)

    current_key = _active_key()
    if current_key:
        src = "Your key (entered below)" if st.session_state.get("user_api_key","").strip() else "Server-configured"
        st.markdown(f"""
        <div style="background:rgba(52,211,153,.12);border:2px solid #86efac;border-radius:14px;
                    padding:16px 20px;margin-bottom:20px;display:flex;align-items:center;gap:14px;">
            <div style="font-size:28px;">🟢</div>
            <div>
                <div style="font-weight:700;color:#6ee7b7;font-size:15px;">API Key Active</div>
                <div style="font-size:12px;color:#6ee7b7;margin-top:2px;">Source: {src} · AI recommendations enabled</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(251,113,133,.12);border:2px solid #fca5a5;border-radius:14px;
                    padding:16px 20px;margin-bottom:20px;display:flex;align-items:center;gap:14px;">
            <div style="font-size:28px;">🔴</div>
            <div>
                <div style="font-weight:700;color:#dc2626;font-size:15px;">No API Key</div>
                <div style="font-size:12px;color:#fda4af;margin-top:2px;">
                    Rule-based audit works without a key · AI suggestions require OpenAI key
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    s1, s2 = st.columns([3, 2])
    with s1:
        st.markdown('<div class="sec-hdr">🔑 OpenAI API Key</div>', unsafe_allow_html=True)
        entered = st.text_input("Key", value=st.session_state.get("user_api_key",""),
                                type="password", placeholder="sk-proj-...",
                                label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Save Key", type="primary", use_container_width=True):
                if entered.strip().startswith("sk-"):
                    st.session_state.user_api_key = entered.strip()
                    os.environ["OPENAI_API_KEY"] = entered.strip()
                    st.success("✅ Key saved! AI analysis is now enabled.")
                    st.rerun()
                elif entered.strip():
                    st.error("Keys must start with 'sk-'")
                else:
                    st.error("Please enter a key.")
        with c2:
            if st.button("🗑️ Clear Key", use_container_width=True):
                st.session_state.user_api_key = ""
                os.environ.pop("OPENAI_API_KEY", None)
                st.rerun()

        st.markdown("""
        <div style="background:rgba(251,191,36,.12);border:1px solid #fde68a;border-radius:10px;
                    padding:12px 14px;margin-top:10px;">
            <div style="font-size:12px;font-weight:600;color:#fcd34d;margin-bottom:3px;">🔒 Privacy</div>
            <div style="font-size:12px;color:#fcd34d;line-height:1.6;">
                Your key is stored in browser session memory only.<br>
                Never saved to any database or server. Cleared when you close the tab.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── SerpAPI key (live keyword rankings) ───────────────────────────────
        st.markdown('<div class="sec-hdr">🔑 SerpAPI Key — Live Rankings</div>', unsafe_allow_html=True)
        serp_active = rankings.has_key()
        st.markdown(f"""
        <div style="background:{'rgba(52,211,153,.12)' if serp_active else 'rgba(140,120,255,.10)'};
                    border:1px solid {'rgba(52,211,153,.4)' if serp_active else 'rgba(140,120,255,.3)'};
                    border-radius:10px;padding:10px 14px;margin-bottom:10px;font-size:12.5px;color:#c9cdf2;">
            {'🟢 Connected — Keyword Rankings &amp; Pages can fetch live Google positions.' if serp_active
              else 'Powers the 🔑 Keyword Rankings &amp; 📄 Pages tabs (Google US + SF Bay Area). Get a free key at '
                   '<a href="https://serpapi.com/manage-api-key" target="_blank" style="color:#22d3ee;">serpapi.com</a>.'}
        </div>
        """, unsafe_allow_html=True)
        serp_entered = st.text_input("SerpAPI Key", value=st.session_state.get("serp_api_key", ""),
                                     type="password", placeholder="your SerpAPI key",
                                     label_visibility="collapsed", key="serp_input")
        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button("💾 Save SerpAPI Key", use_container_width=True):
                if serp_entered.strip():
                    st.session_state.serp_api_key = serp_entered.strip()
                    os.environ["SERPAPI_KEY"] = serp_entered.strip()
                    st.success("✅ SerpAPI key saved — rank tracking enabled.")
                    st.rerun()
                else:
                    st.error("Please enter a key.")
        with sc2:
            if st.button("🗑️ Clear SerpAPI Key", use_container_width=True):
                st.session_state.serp_api_key = ""
                os.environ.pop("SERPAPI_KEY", None)
                st.rerun()
        st.caption(f"Budget: a full refresh = {len(rankings.DEFAULT_KEYWORDS)} keywords × 2 locations "
                   f"= {len(rankings.DEFAULT_KEYWORDS)*2} searches. Cached "
                   f"{rankings.REFRESH_AFTER_DAYS} days.")

        st.markdown('<div class="sec-hdr">🔍 What Works Without a Key?</div>', unsafe_allow_html=True)
        no_key_features = [
            ("✅","6-Category Rule-Based Audit","Full scoring — meta, headings, keywords, technical, images, links"),
            ("✅","SEO Score & Radar Chart","Overall score, category breakdown, issue counts"),
            ("✅","SERP & Social Preview","Google preview, OG/Twitter card preview"),
            ("✅","Markdown Export","Full markdown report of rule-based findings"),
            ("❌","AI Improvement Plan","Requires OpenAI key"),
            ("❌","Optimised Title/Description","Requires OpenAI key"),
            ("❌","Keyword Strategy","Requires OpenAI key"),
            ("❌","PDF with AI content","Requires OpenAI key"),
        ]
        for icon, title, desc in no_key_features:
            color = "#22c55e" if icon=="✅" else "#94a3b8"
            st.markdown(f"""
            <div style="display:flex;gap:10px;padding:7px 0;border-bottom:1px solid #f1f5f9;">
                <span style="color:{color};font-size:14px;flex-shrink:0;">{icon}</span>
                <div>
                    <div style="font-size:13px;font-weight:500;color:#eef0ff;">{title}</div>
                    <div style="font-size:11px;color:#64748b;">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with s2:
        st.markdown('<div class="sec-hdr">📋 Get an API Key</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#0e1120;border:1px solid rgba(140,120,255,.18);border-radius:12px;padding:18px;">
            <div style="font-size:13px;color:#c9cdf2;line-height:2.2;">
                1. Visit <a href="https://platform.openai.com/api-keys" target="_blank"
                   style="color:#4f46e5;font-weight:600;">platform.openai.com/api-keys</a><br>
                2. Sign in or create a free account<br>
                3. Click <strong>+ Create new secret key</strong><br>
                4. Name it "SEO Audit Agent"<br>
                5. Copy the key (starts with <code>sk-</code>)<br>
                6. Paste it on the left and save
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sec-hdr">💰 Cost Per Audit</div>', unsafe_allow_html=True)
        costs = [
            ("Web scraping","Free"),
            ("Rule-based analysis","Free"),
            ("GPT-4o improvement plan","~$0.005"),
            ("GPT-4o content optimisation","~$0.005"),
            ("GPT-4o technical guidance","~$0.004"),
            ("GPT-4o UX suggestions","~$0.004"),
            ("GPT-4o keyword strategy","~$0.004"),
            ("Total per full audit","~$0.022"),
        ]
        for item, cost in costs:
            bold = "font-weight:800;color:#4f46e5;" if item.startswith("Total") else ""
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:6px 12px;
                        background:{'#eff6ff' if item.startswith('Total') else 'white'};
                        border:1px solid rgba(140,120,255,.18);border-radius:8px;margin:2px 0;">
                <span style="font-size:12px;color:#c9cdf2;">{item}</span>
                <span style="font-size:12px;{bold}">{cost}</span>
            </div>
            """, unsafe_allow_html=True)

    if current_key:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 Run an Audit Now →", type="primary"):
            st.session_state.page = "🔍 Audit"; st.rerun()
