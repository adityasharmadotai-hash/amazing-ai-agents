"""
app.py — AI SEO Audit Agent
Beautiful Streamlit dashboard for full website SEO analysis.
"""

import os
import sys

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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html,body,[class*="css"]{ font-family:'Inter',sans-serif; }

/* Sidebar */
[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#0a0f1e 0%,#111827 55%,#0d1b2a 100%) !important;
}
[data-testid="stSidebar"]>div:first-child{background:transparent !important;}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,[data-testid="stSidebar"] label{color:#e2e8f0 !important;}
[data-testid="stSidebar"] .stButton>button{
    background:rgba(255,255,255,0.07) !important;
    border:1px solid rgba(255,255,255,0.12) !important;
    border-radius:10px !important;color:#e2e8f0 !important;
    font-size:14px !important;font-weight:500 !important;
    padding:10px 14px !important;width:100% !important;
    margin:2px 0 !important;text-align:left !important;
}
[data-testid="stSidebar"] .stButton>button p{color:#e2e8f0 !important;}
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
    box-shadow:0 4px 16px rgba(79,70,229,0.4) !important;
    transform:translateX(3px) !important;
}
[data-testid="stSidebar"] .nav-active>button p{color:white !important;}
.nav-div{height:1px;background:rgba(255,255,255,0.08);margin:10px 0;}

/* Score gauge */
.score-gauge{
    text-align:center;padding:28px 20px;
    background:white;border-radius:20px;
    box-shadow:0 4px 20px rgba(0,0,0,0.08);
    border:1px solid #e2e8f0;
}
.score-number{font-size:72px;font-weight:900;line-height:1;}
.score-label{font-size:18px;font-weight:700;margin-top:6px;}
.score-sub{font-size:13px;color:#64748b;margin-top:4px;}

/* Category score card */
.cat-card{
    background:white;border-radius:14px;padding:18px 20px;
    border:1px solid #e2e8f0;box-shadow:0 2px 6px rgba(0,0,0,0.05);
    margin-bottom:10px;transition:transform 0.15s;
}
.cat-card:hover{transform:translateY(-2px);box-shadow:0 4px 14px rgba(0,0,0,0.1);}
.cat-score{font-size:28px;font-weight:800;}
.cat-label{font-size:13px;font-weight:600;color:#374151;margin-top:2px;}
.cat-bar{height:6px;border-radius:3px;margin-top:8px;background:#f1f5f9;}
.cat-bar-fill{height:6px;border-radius:3px;}

/* Issue cards */
.issue-critical{background:#fef2f2;border:1px solid #fecaca;border-left:4px solid #ef4444;border-radius:10px;padding:12px 16px;margin:6px 0;}
.issue-warning {background:#fffbeb;border:1px solid #fde68a;border-left:4px solid #f59e0b;border-radius:10px;padding:12px 16px;margin:6px 0;}
.issue-info    {background:#eff6ff;border:1px solid #bfdbfe;border-left:4px solid #3b82f6;border-radius:10px;padding:12px 16px;margin:6px 0;}
.issue-pass    {background:#f0fdf4;border:1px solid #bbf7d0;border-left:4px solid #22c55e;border-radius:10px;padding:12px 16px;margin:6px 0;}
.issue-title   {font-size:13px;font-weight:600;color:#0f172a;}
.issue-fix     {font-size:12px;color:#64748b;margin-top:4px;}

/* AI suggestion cards */
.ai-card{
    background:white;border:1px solid #e2e8f0;border-radius:14px;
    padding:16px 18px;margin:8px 0;
    box-shadow:0 2px 6px rgba(0,0,0,0.05);
}
.ai-card-title{font-size:14px;font-weight:700;color:#0f172a;margin-bottom:6px;}
.ai-card-body {font-size:13px;color:#374151;line-height:1.6;}
.impact-high  {background:#fef2f2;color:#dc2626;border:1px solid #fecaca;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:700;}
.impact-med   {background:#fffbeb;color:#d97706;border:1px solid #fde68a;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:700;}
.impact-low   {background:#f0fdf4;color:#16a34a;border:1px solid #bbf7d0;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:700;}

/* Keyword badge */
.kw-badge{display:inline-block;background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;margin:3px;}

/* Section header */
.sec-hdr{background:linear-gradient(90deg,#4f46e5,#7c3aed);color:white;border-radius:12px;padding:12px 18px;margin:18px 0 14px;font-size:15px;font-weight:600;}

/* URL bar */
.url-display{background:#f1f5f9;border:1px solid #e2e8f0;border-radius:10px;padding:10px 16px;font-size:14px;font-weight:500;color:#374151;word-break:break-all;}

/* Metric row */
.metric-row{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0;}
.metric-box{background:white;border:1px solid #e2e8f0;border-radius:12px;padding:14px 18px;flex:1;min-width:140px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,0.06);}
.metric-val{font-size:24px;font-weight:800;color:#0f172a;}
.metric-lbl{font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;margin-top:3px;}

#MainMenu,footer{visibility:hidden;}
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

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {
    "page": "🔍 Audit",
    "raw_data": None,
    "audit": None,
    "ai": None,
    "user_api_key": "",
    "auditing": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


def _active_key() -> str:
    sk = st.session_state.get("user_api_key","").strip()
    if sk: return sk
    try: return st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY","")
    except: return os.environ.get("OPENAI_API_KEY","")


def _sync_key():
    k = _active_key()
    if k: os.environ["OPENAI_API_KEY"] = k

_sync_key()

# ── Navigation ────────────────────────────────────────────────────────────────
NAV = [
    ("🔍","Audit"), ("📊","Dashboard"), ("🤖","AI Suggestions"),
    ("📈","Keywords"), ("⚙️","Technical"), ("📤","Export"), ("🔑","Settings"),
]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    has_key = bool(_active_key())
    has_audit = st.session_state.audit is not None
    score = st.session_state.audit.get("overall_score",0) if has_audit else 0
    lbl, col = score_label(score) if has_audit else ("","#6b7280")

    st.markdown(f"""
    <div style="padding:20px 4px 16px;text-align:center;">
        <div style="width:56px;height:56px;background:linear-gradient(135deg,#4f46e5,#7c3aed);
                    border-radius:14px;margin:0 auto;display:flex;align-items:center;
                    justify-content:center;font-size:26px;box-shadow:0 4px 14px rgba(79,70,229,0.4);">🔍</div>
        <div style="font-size:16px;font-weight:800;color:white;margin-top:10px;">SEO Audit Agent</div>
        <div style="font-size:11px;color:#475569;margin-top:3px;">Powered by OpenAI GPT-4o</div>
        {"<div style='margin-top:10px;background:rgba(79,70,229,0.2);border-radius:8px;padding:6px;'><span style='font-size:22px;font-weight:900;color:"+col+";'>"+str(score)+"</span><span style='font-size:11px;color:#94a3b8;'>/100 — "+lbl+"</span></div>" if has_audit else ""}
    </div>
    <div class="nav-div"></div>
    <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:0.1em;font-weight:600;padding:0 4px;margin-bottom:6px;">Navigation</div>
    """, unsafe_allow_html=True)

    current = st.session_state.get("page","🔍 Audit")
    for icon, label in NAV:
        full = f"{icon} {label}"
        is_active = (current == full)
        disabled = (not has_audit and label not in ("Audit","Settings"))
        if is_active:
            st.markdown('<div class="nav-active">', unsafe_allow_html=True)
        btn_lbl = f"✦  {icon}  {label}" if is_active else f"{icon}  {label}"
        if st.button(btn_lbl, key=f"nav_{label}", use_container_width=True, disabled=disabled):
            st.session_state.page = full
            st.rerun()
        if is_active:
            st.markdown('</div>', unsafe_allow_html=True)

    page = st.session_state.get("page","🔍 Audit")

    if has_audit:
        raw = st.session_state.raw_data
        st.markdown(f"""
        <div class="nav-div"></div>
        <div style="background:rgba(79,70,229,0.15);border:1px solid rgba(79,70,229,0.3);
                    border-radius:10px;padding:11px 13px;">
            <div style="font-size:10px;color:#818cf8;text-transform:uppercase;font-weight:600;">Audited Site</div>
            <div style="font-size:12px;font-weight:600;color:white;margin-top:4px;word-break:break-all;">{raw.get('domain','')}</div>
            <div style="font-size:11px;color:#475569;margin-top:4px;">
                ⏱ {raw.get('load_time_seconds',0)}s ·
                📝 {raw.get('word_count',0):,} words ·
                {'🔒' if raw.get('is_https') else '⚠️'} {'HTTPS' if raw.get('is_https') else 'HTTP'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="nav-div"></div>
    <div style="font-size:11px;color:#334155;text-align:center;padding:4px 0 8px;">
        Built with ❤️ by
        <a href="https://www.adityasharma.ai" target="_blank" style="color:#818cf8;text-decoration:none;">adityasharma.ai</a>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: AUDIT
# ─────────────────────────────────────────────────────────────────────────────
if page == "🔍 Audit":
    st.markdown("""
    <div style="padding:4px 0 20px;">
        <h1 style="font-size:28px;font-weight:800;color:#0f172a;margin:0;">🔍 AI SEO Audit Agent</h1>
        <p style="color:#64748b;font-size:15px;margin-top:6px;">
            Enter any website URL to get a complete SEO audit with AI-powered recommendations
        </p>
    </div>
    """, unsafe_allow_html=True)

    # URL input
    col_url, col_btn = st.columns([5, 1])
    with col_url:
        url_input = st.text_input(
            "Website URL", placeholder="https://example.com",
            label_visibility="collapsed",
            help="Enter the full URL including https://",
        )
    with col_btn:
        run_audit = st.button("🔍 Audit", type="primary", use_container_width=True)

    # Options
    with st.expander("⚙️ Audit Options"):
        oc1, oc2 = st.columns(2)
        with oc1:
            run_ai = st.checkbox("Run AI Analysis (GPT-4o)", value=True,
                                 help="Requires OpenAI API key in Settings")
        with oc2:
            show_passes = st.checkbox("Show passed checks", value=False)

    if run_audit and url_input:
        if run_ai and not _active_key():
            st.warning("⚠️ No OpenAI API key. Go to 🔑 Settings to add one, or uncheck 'Run AI Analysis'.")
            st.stop()

        with st.status("🔍 Running SEO Audit...", expanded=True) as status:
            st.write("📡 Fetching website...")
            page_data = fetch_page(url_input)
            if "error" in page_data:
                st.error(f"❌ {page_data['error']}")
                st.stop()

            st.write("🔎 Extracting SEO data...")
            raw = extract_raw_data(page_data)
            if "error" in raw:
                st.error(f"❌ {raw['error']}")
                st.stop()

            st.write("📊 Analysing meta tags, headings, keywords...")
            meta_r  = analyse_meta(raw)
            head_r  = analyse_headings(raw)
            kw_r    = analyse_keywords(raw)

            st.write("⚙️ Running technical & accessibility audit...")
            tech_r  = analyse_technical(raw)
            img_r   = analyse_images(raw)
            link_r  = analyse_links(raw)

            audit = {
                "meta": meta_r, "headings": head_r, "keywords": kw_r,
                "technical": tech_r, "images": img_r, "links": link_r,
            }
            audit["overall_score"] = calculate_overall(audit)

            ai_results = {"improvements":{},"content":{},"technical":{},"ux":{},"keywords":{}}

            if run_ai and _active_key():
                st.write("🤖 GPT-4o: Generating SEO improvement plan...")
                ai_results["improvements"] = seo_improvements(raw, audit)
                st.write("✍️ GPT-4o: Optimising content & meta tags...")
                ai_results["content"] = content_optimisation(raw, audit)
                st.write("🔧 GPT-4o: Technical guidance...")
                ai_results["technical"] = technical_guidance(raw, audit)
                st.write("🎨 GPT-4o: UX recommendations...")
                ai_results["ux"] = ux_suggestions(raw, audit)
                st.write("📈 GPT-4o: Keyword strategy...")
                ai_results["keywords"] = keyword_strategy(raw, audit)

            st.session_state.raw_data = raw
            st.session_state.audit    = audit
            st.session_state.ai       = ai_results
            status.update(label="✅ Audit Complete!", state="complete")

        # Auto-navigate to dashboard
        st.session_state.page = "📊 Dashboard"
        st.rerun()

    # Landing state
    if not st.session_state.audit:
        f1, f2, f3 = st.columns(3)
        for col, icon, title, desc in [
            (f1,"🔍","6-Category Audit","Meta, headings, keywords, technical, images, links"),
            (f2,"🤖","AI Recommendations","GPT-4o powered fix suggestions with priority ranking"),
            (f3,"📥","Export Reports","Download PDF or Markdown audit reports"),
        ]:
            with col:
                st.markdown(f"""
                <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;
                            padding:24px 18px;text-align:center;box-shadow:0 2px 6px rgba(0,0,0,0.05);">
                    <div style="font-size:36px;">{icon}</div>
                    <div style="font-weight:700;color:#0f172a;margin:10px 0 6px;font-size:14px;">{title}</div>
                    <div style="font-size:12px;color:#64748b;line-height:1.5;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📊 Dashboard":
    import plotly.graph_objects as go

    raw   = st.session_state.raw_data
    audit = st.session_state.audit
    ai    = st.session_state.ai or {}
    score = audit["overall_score"]
    lbl, col = score_label(score)
    counts = issue_counts(audit)

    st.markdown(f'<h1 style="color:#0f172a;font-size:26px;">📊 SEO Dashboard</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="url-display">🌐 {raw["url"]}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Score + issue counts
    sc1, sc2, sc3, sc4, sc5 = st.columns([2,1,1,1,1])

    with sc1:
        st.markdown(f"""
        <div class="score-gauge">
            <div class="score-number" style="color:{col};">{score}</div>
            <div class="score-label" style="color:{col};">{lbl}</div>
            <div class="score-sub">Overall SEO Score / 100</div>
        </div>
        """, unsafe_allow_html=True)

    for col_w, sev, icon, color in [
        (sc2,"critical","❌","#ef4444"),
        (sc3,"warning","⚠️","#f59e0b"),
        (sc4,"info","ℹ️","#3b82f6"),
        (sc5,"pass","✅","#22c55e"),
    ]:
        with col_w:
            st.markdown(f"""
            <div style="background:white;border-radius:14px;padding:20px;text-align:center;
                        border:1px solid #e2e8f0;box-shadow:0 2px 6px rgba(0,0,0,0.05);">
                <div style="font-size:28px;">{icon}</div>
                <div style="font-size:28px;font-weight:800;color:{color};">{counts[sev]}</div>
                <div style="font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;">{sev.title()}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Radar chart + category scores
    ch1, ch2 = st.columns([3, 2])

    with ch1:
        cats_order = ["Meta","Headings","Keywords","Technical","Images","Links"]
        cat_keys   = ["meta","headings","keywords","technical","images","links"]
        scores_list = [audit[k]["score"] for k in cat_keys]

        fig = go.Figure(go.Scatterpolar(
            r=scores_list + [scores_list[0]],
            theta=cats_order + [cats_order[0]],
            fill="toself",
            fillcolor="rgba(79,70,229,0.15)",
            line=dict(color="#4f46e5", width=2),
            marker=dict(size=6, color="#4f46e5"),
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0,100], gridcolor="#f1f5f9"),
                       angularaxis=dict(gridcolor="#e2e8f0")),
            showlegend=False, margin=dict(l=40,r=40,t=30,b=30),
            height=320, paper_bgcolor="white", plot_bgcolor="white",
        )
        st.markdown('<div class="sec-hdr">📡 SEO Radar</div>', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)

    with ch2:
        st.markdown('<div class="sec-hdr">📂 Category Scores</div>', unsafe_allow_html=True)
        for cat, key in zip(cats_order, cat_keys):
            s = audit[key]["score"]
            bar_color = "#22c55e" if s>=70 else ("#f59e0b" if s>=50 else "#ef4444")
            st.markdown(f"""
            <div class="cat-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div class="cat-label">{cat}</div>
                    <div class="cat-score" style="color:{bar_color};">{s}</div>
                </div>
                <div class="cat-bar">
                    <div class="cat-bar-fill" style="width:{s}%;background:{bar_color};"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Page metrics
    st.markdown('<div class="sec-hdr">📋 Page Metrics</div>', unsafe_allow_html=True)
    m1,m2,m3,m4,m5,m6 = st.columns(6)
    for col_w, val, lbl_ in [
        (m1, f"{raw.get('load_time_seconds',0)}s","Load Time"),
        (m2, raw.get("status_code",0),"HTTP Status"),
        (m3, f"{raw.get('html_size_kb',0)} KB","HTML Size"),
        (m4, f"{raw.get('word_count',0):,}","Word Count"),
        (m5, len(raw.get("images",[])), "Images"),
        (m6, len(raw.get("internal_links",[])), "Int. Links"),
    ]:
        with col_w:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-val">{val}</div>
                <div class="metric-lbl">{lbl_}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Issues breakdown bar chart
    st.markdown('<div class="sec-hdr">🔎 Issues by Category</div>', unsafe_allow_html=True)
    cat_crits = {cat: sum(1 for i in audit[key].get("issues",[]) if i["severity"]=="critical")
                 for cat, key in zip(cats_order, cat_keys)}
    cat_warns = {cat: sum(1 for i in audit[key].get("issues",[]) if i["severity"]=="warning")
                 for cat, key in zip(cats_order, cat_keys)}

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="Critical", x=cats_order,
                          y=[cat_crits[c] for c in cats_order],
                          marker_color="#ef4444", marker_line_width=0))
    fig2.add_trace(go.Bar(name="Warning", x=cats_order,
                          y=[cat_warns[c] for c in cats_order],
                          marker_color="#f59e0b", marker_line_width=0))
    fig2.update_layout(barmode="stack", plot_bgcolor="white", paper_bgcolor="white",
                       margin=dict(l=20,r=20,t=20,b=20), height=250,
                       xaxis=dict(showgrid=False),
                       yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                       legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig2, use_container_width=True)

    # Issue list
    st.markdown('<div class="sec-hdr">🐛 All Issues</div>', unsafe_allow_html=True)
    severity_order = ["critical","warning","info","pass"]
    filter_sev = st.multiselect("Show severities:", ["critical","warning","info","pass"],
                                default=["critical","warning"])

    for cat, key in zip(cats_order, cat_keys):
        issues_to_show = [i for i in audit[key].get("issues",[])
                          if i.get("severity") in filter_sev]
        if issues_to_show:
            with st.expander(f"{cat} — {audit[key]['score']}/100 ({len(issues_to_show)} shown)"):
                for iss in issues_to_show:
                    sev = iss.get("severity","info")
                    icons = {"critical":"❌","warning":"⚠️","info":"ℹ️","pass":"✅"}
                    css   = {"critical":"issue-critical","warning":"issue-warning","info":"issue-info","pass":"issue-pass"}
                    safe  = iss["message"].replace("<","&lt;").replace(">","&gt;")
                    fix   = iss.get("fix","").replace("<","&lt;")
                    st.markdown(f"""
                    <div class="{css[sev]}">
                        <div class="issue-title">{icons[sev]} {safe}</div>
                        {"<div class='issue-fix'>→ " + fix + "</div>" if fix else ""}
                    </div>
                    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: AI SUGGESTIONS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🤖 AI Suggestions":
    ai    = st.session_state.ai or {}
    audit = st.session_state.audit

    st.markdown('<h1 style="color:#0f172a;font-size:26px;">🤖 AI SEO Recommendations</h1>', unsafe_allow_html=True)

    if not ai or not ai.get("improvements"):
        st.info("AI analysis was not run. Go to 🔍 Audit and enable 'Run AI Analysis'.")
        st.stop()

    impr = ai.get("improvements", {})
    if impr.get("error"):
        st.error(f"AI error: {impr['error']}")
    else:
        # Grade banner
        grade = impr.get("overall_grade","?")
        grade_color = {"A":"#22c55e","B":"#84cc16","C":"#f59e0b","D":"#f97316","F":"#ef4444"}.get(grade,"#6b7280")
        st.markdown(f"""
        <div style="background:white;border:2px solid {grade_color};border-radius:16px;
                    padding:20px 24px;margin-bottom:20px;display:flex;align-items:center;gap:20px;">
            <div style="font-size:64px;font-weight:900;color:{grade_color};line-height:1;">{grade}</div>
            <div>
                <div style="font-size:18px;font-weight:700;color:#0f172a;">SEO Grade</div>
                <div style="font-size:14px;color:#374151;margin-top:4px;line-height:1.6;">
                    {impr.get('executive_summary','')}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Top 3 priorities
        priorities = impr.get("top_3_priorities",[])
        if priorities:
            st.markdown('<div class="sec-hdr">🎯 Top 3 Priorities</div>', unsafe_allow_html=True)
            for i, p in enumerate(priorities, 1):
                st.markdown(f"""
                <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;
                            padding:14px 18px;margin:6px 0;display:flex;align-items:center;gap:14px;">
                    <div style="width:30px;height:30px;background:#4f46e5;color:white;border-radius:50%;
                                display:flex;align-items:center;justify-content:center;font-weight:800;flex-shrink:0;">{i}</div>
                    <div style="font-size:14px;font-weight:600;color:#0f172a;">{p}</div>
                </div>
                """, unsafe_allow_html=True)

    # Tabs
    t1, t2, t3 = st.tabs(["⚡ Quick Wins & Actions", "✍️ Content Optimisation", "🎨 UX Improvements"])

    with t1:
        impr = ai.get("improvements",{})
        st.markdown('<div class="sec-hdr">⚡ Quick Wins — Fix Today</div>', unsafe_allow_html=True)
        for qw in impr.get("quick_wins",[]):
            imp = qw.get("impact","Medium")
            imp_cls = {"High":"impact-high","Medium":"impact-med","Low":"impact-low"}.get(imp,"impact-med")
            st.markdown(f"""
            <div class="ai-card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div class="ai-card-title">⚡ {qw.get('action','')}</div>
                    <span class="{imp_cls}">{imp}</span>
                </div>
                <div class="ai-card-body">{qw.get('detail','')}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="sec-hdr">📅 Short-Term (1-4 weeks)</div>', unsafe_allow_html=True)
        for item in impr.get("short_term",[]):
            imp = item.get("impact","Medium")
            imp_cls = {"High":"impact-high","Medium":"impact-med","Low":"impact-low"}.get(imp,"impact-med")
            st.markdown(f"""
            <div class="ai-card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div class="ai-card-title">📅 {item.get('action','')}</div>
                    <span class="{imp_cls}">{imp}</span>
                </div>
                <div class="ai-card-body">{item.get('detail','')}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="sec-hdr">🚀 Long-Term Strategy</div>', unsafe_allow_html=True)
        for item in impr.get("long_term",[]):
            st.markdown(f"""
            <div class="ai-card">
                <div class="ai-card-title">🚀 {item.get('action','')}</div>
                <div class="ai-card-body">{item.get('detail','')}</div>
            </div>
            """, unsafe_allow_html=True)

    with t2:
        content = ai.get("content",{})
        if content.get("error"):
            st.error(f"AI error: {content['error']}")
        else:
            st.markdown('<div class="sec-hdr">📝 Recommended Title Options</div>', unsafe_allow_html=True)
            for i, t_ in enumerate(content.get("title_options",[]), 1):
                chars = len(t_)
                color = "#22c55e" if 50 <= chars <= 60 else "#f59e0b"
                st.markdown(f"""
                <div style="background:white;border:1px solid #e2e8f0;border-radius:10px;padding:12px 16px;margin:6px 0;">
                    <div style="font-weight:600;color:#0f172a;">{i}. {t_}</div>
                    <div style="font-size:12px;color:{color};margin-top:4px;">{chars} characters</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div class="sec-hdr">📄 Recommended Meta Descriptions</div>', unsafe_allow_html=True)
            for i, d_ in enumerate(content.get("description_options",[]), 1):
                chars = len(d_)
                color = "#22c55e" if 150 <= chars <= 160 else "#f59e0b"
                st.markdown(f"""
                <div style="background:white;border:1px solid #e2e8f0;border-radius:10px;padding:12px 16px;margin:6px 0;">
                    <div style="font-size:13px;color:#0f172a;">{i}. {d_}</div>
                    <div style="font-size:12px;color:{color};margin-top:4px;">{chars} characters</div>
                </div>
                """, unsafe_allow_html=True)

            cc1, cc2 = st.columns(2)
            with cc1:
                st.markdown('<div class="sec-hdr">💡 Content Suggestions</div>', unsafe_allow_html=True)
                for s in content.get("content_suggestions",[]):
                    st.markdown(f'<div class="ai-card"><div class="ai-card-body">💡 {s}</div></div>', unsafe_allow_html=True)
            with cc2:
                st.markdown('<div class="sec-hdr">📢 CTA Improvements</div>', unsafe_allow_html=True)
                for c in content.get("cta_improvements",[]):
                    st.markdown(f'<div class="ai-card"><div class="ai-card-body">📢 {c}</div></div>', unsafe_allow_html=True)

            if content.get("primary_keyword"):
                st.markdown(f"""
                <div style="background:#eff6ff;border:2px solid #bfdbfe;border-radius:12px;padding:16px 20px;margin-top:12px;">
                    <div style="font-weight:700;color:#1d4ed8;">🎯 Recommended Primary Keyword: <span style="font-size:18px;">'{content['primary_keyword']}'</span></div>
                    <div style="font-size:13px;color:#374151;margin-top:6px;">{content.get('keyword_reasoning','')}</div>
                </div>
                """, unsafe_allow_html=True)

    with t3:
        ux = ai.get("ux",{})
        if ux.get("error"):
            st.error(f"AI error: {ux['error']}")
        else:
            ux1, ux2 = st.columns(2)
            with ux1:
                for hdr, key in [("📖 Readability","readability_tips"),("📱 Mobile UX","mobile_ux_tips")]:
                    st.markdown(f'<div class="sec-hdr">{hdr}</div>', unsafe_allow_html=True)
                    for tip in ux.get(key,[]):
                        st.markdown(f'<div class="ai-card"><div class="ai-card-body">• {tip}</div></div>', unsafe_allow_html=True)
            with ux2:
                for hdr, key in [("🧭 Navigation","navigation_suggestions"),("🤝 Trust Signals","trust_signals")]:
                    st.markdown(f'<div class="sec-hdr">{hdr}</div>', unsafe_allow_html=True)
                    for tip in ux.get(key,[]):
                        st.markdown(f'<div class="ai-card"><div class="ai-card-body">• {tip}</div></div>', unsafe_allow_html=True)

            if ux.get("page_structure_advice"):
                st.markdown(f"""
                <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:12px;padding:16px 20px;margin-top:12px;">
                    <div style="font-weight:700;color:#15803d;margin-bottom:6px;">🏗️ Page Structure Advice</div>
                    <div style="font-size:13px;color:#374151;">{ux['page_structure_advice']}</div>
                </div>
                """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: KEYWORDS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📈 Keywords":
    import plotly.graph_objects as go

    audit = st.session_state.audit
    ai    = st.session_state.ai or {}
    kw_data = audit.get("keywords",{})
    ai_kw   = ai.get("keywords",{})

    st.markdown('<h1 style="color:#0f172a;font-size:26px;">📈 Keyword Analysis</h1>', unsafe_allow_html=True)

    kk1, kk2 = st.columns([3,2])

    with kk1:
        top = kw_data.get("top_keywords",[])
        if top:
            st.markdown('<div class="sec-hdr">🔤 Top Keywords Found on Page</div>', unsafe_allow_html=True)
            words = [k for k,_ in top[:15]]
            freqs = [c for _,c in top[:15]]
            colors_list = ["#4f46e5"]*3 + ["#7c3aed"]*3 + ["#818cf8"]*9
            fig = go.Figure(go.Bar(x=freqs, y=words, orientation="h",
                                   marker_color=colors_list[:len(words)],
                                   marker_line_width=0))
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                              margin=dict(l=10,r=20,t=10,b=20), height=400,
                              xaxis=dict(showgrid=True, gridcolor="#f1f5f9", title="Frequency"),
                              yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)

    with kk2:
        st.markdown('<div class="sec-hdr">📊 Keyword Stats</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="metric-box" style="margin-bottom:8px;">
            <div class="metric-val">{kw_data.get('word_count',0):,}</div>
            <div class="metric-lbl">Total Words</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Keywords in title:**")
        for k in kw_data.get("keywords_in_title",[]):
            st.markdown(f'<span class="kw-badge">✅ {k}</span>', unsafe_allow_html=True)
        if not kw_data.get("keywords_in_title"):
            st.warning("No top keywords found in title")

        st.markdown("**Keywords in description:**")
        for k in kw_data.get("keywords_in_desc",[]):
            st.markdown(f'<span class="kw-badge">✅ {k}</span>', unsafe_allow_html=True)
        if not kw_data.get("keywords_in_desc"):
            st.info("No top keywords in meta description")

        if kw_data.get("density_issues"):
            st.markdown("**⚠️ Density Issues:**")
            for d in kw_data["density_issues"]:
                st.warning(d)

    # AI Keyword Strategy
    if ai_kw and not ai_kw.get("error"):
        st.markdown('<div class="sec-hdr">🤖 AI Keyword Strategy</div>', unsafe_allow_html=True)
        sk1, sk2 = st.columns(2)
        with sk1:
            st.markdown("**🎯 Target Keywords**")
            for kw in ai_kw.get("primary_keywords",[]):
                diff_color = {"Low":"#22c55e","Medium":"#f59e0b","High":"#ef4444"}.get(kw.get("difficulty","Medium"),"#6b7280")
                st.markdown(f"""
                <div class="ai-card">
                    <div style="display:flex;justify-content:space-between;">
                        <span style="font-weight:700;color:#0f172a;">{kw.get('keyword','')}</span>
                        <span style="font-size:11px;font-weight:600;color:{diff_color};">{kw.get('difficulty','')} difficulty</span>
                    </div>
                    <div style="font-size:11px;color:#94a3b8;margin-top:2px;">{kw.get('type','')}</div>
                    <div style="font-size:12px;color:#374151;margin-top:6px;">{kw.get('rationale','')}</div>
                </div>
                """, unsafe_allow_html=True)

        with sk2:
            st.markdown("**🔍 Long-tail Opportunities**")
            for lt in ai_kw.get("long_tail_opportunities",[]):
                st.markdown(f'<div class="ai-card"><div class="ai-card-body">🔍 {lt}</div></div>', unsafe_allow_html=True)

            st.markdown("**🔗 Semantic Keywords**")
            sem_html = "".join(f'<span class="kw-badge">{s}</span>' for s in ai_kw.get("semantic_keywords",[]))
            st.markdown(sem_html, unsafe_allow_html=True)

        if ai_kw.get("content_ideas"):
            st.markdown('<div class="sec-hdr">💡 Content Ideas</div>', unsafe_allow_html=True)
            for idea in ai_kw.get("content_ideas",[]):
                st.markdown(f"""
                <div class="ai-card">
                    <div class="ai-card-title">📝 {idea.get('title','')}</div>
                    <div style="font-size:12px;color:#64748b;">
                        Target: <strong>{idea.get('target_keyword','')}</strong> ·
                        Type: {idea.get('type','')}
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: TECHNICAL
# ─────────────────────────────────────────────────────────────────────────────
elif page == "⚙️ Technical":
    raw   = st.session_state.raw_data
    audit = st.session_state.audit
    ai    = st.session_state.ai or {}
    tech  = audit.get("technical",{})
    imgs  = audit.get("images",{})
    links = audit.get("links",{})
    ai_tech = ai.get("technical",{})

    st.markdown('<h1 style="color:#0f172a;font-size:26px;">⚙️ Technical SEO Audit</h1>', unsafe_allow_html=True)

    # Tech metrics
    tm1,tm2,tm3,tm4 = st.columns(4)
    for col_w, val, lbl_, ok in [
        (tm1, f"{tech.get('load_time_seconds',0)}s","Load Time", tech.get('load_time_seconds',9) < 3),
        (tm2, tech.get('status_code',0),"HTTP Status", tech.get('status_code',0)==200),
        (tm3, "✅ Yes" if tech.get('is_https') else "❌ No","HTTPS", tech.get('is_https',False)),
        (tm4, "✅ Yes" if tech.get('has_schema') else "❌ No","Schema.org", tech.get('has_schema',False)),
    ]:
        with col_w:
            color = "#22c55e" if ok else "#ef4444"
            st.markdown(f"""
            <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px;text-align:center;border-top:3px solid {color};">
                <div style="font-size:22px;font-weight:800;color:{color};">{val}</div>
                <div style="font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;margin-top:4px;">{lbl_}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tc1, tc2 = st.columns(2)

    with tc1:
        st.markdown('<div class="sec-hdr">⚙️ Technical Issues</div>', unsafe_allow_html=True)
        for iss in tech.get("issues",[]):
            sev = iss.get("severity","info")
            icons = {"critical":"❌","warning":"⚠️","info":"ℹ️","pass":"✅"}
            css   = {"critical":"issue-critical","warning":"issue-warning","info":"issue-info","pass":"issue-pass"}
            safe  = iss["message"].replace("<","&lt;")
            fix   = iss.get("fix","").replace("<","&lt;")
            st.markdown(f"""
            <div class="{css.get(sev,'issue-info')}">
                <div class="issue-title">{icons.get(sev,'ℹ️')} {safe}</div>
                {"<div class='issue-fix'>→ " + fix + "</div>" if fix else ""}
            </div>
            """, unsafe_allow_html=True)

    with tc2:
        st.markdown('<div class="sec-hdr">🖼️ Image & Link Stats</div>', unsafe_allow_html=True)
        stats = [
            ("Total Images", imgs.get("total_images",0)),
            ("Missing Alt Text", imgs.get("missing_alt",0)),
            ("Lazy Loaded", imgs.get("lazy_loaded",0)),
            ("Internal Links", links.get("internal_count",0)),
            ("External Links", links.get("external_count",0)),
            ("Empty Anchors", links.get("empty_anchor",0)),
            ("Redirect Chain", tech.get("redirect_count",0)),
            ("HTML Size", f"{tech.get('html_size_kb',0)} KB"),
        ]
        for lbl_, val in stats:
            is_bad = (lbl_ in ("Missing Alt Text","Empty Anchors","Redirect Chain") and val > 0)
            color = "#ef4444" if is_bad else "#0f172a"
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:8px 0;
                        border-bottom:1px solid #f1f5f9;">
                <span style="font-size:13px;color:#374151;">{lbl_}</span>
                <strong style="font-size:13px;color:{color};">{val}</strong>
            </div>
            """, unsafe_allow_html=True)

    # AI Technical guidance
    if ai_tech and not ai_tech.get("error"):
        st.markdown('<div class="sec-hdr">🤖 AI Technical Guidance</div>', unsafe_allow_html=True)
        atc1, atc2 = st.columns(2)
        with atc1:
            st.markdown("**⚡ Performance Fixes**")
            for fix in ai_tech.get("performance_fixes",[]):
                pri = fix.get("priority","Medium")
                color = {"High":"#ef4444","Medium":"#f59e0b","Low":"#22c55e"}.get(pri,"#6b7280")
                st.markdown(f"""
                <div class="ai-card">
                    <div style="display:flex;justify-content:space-between;">
                        <div class="ai-card-title">⚡ {fix.get('fix','')}</div>
                        <span style="font-size:11px;font-weight:600;color:{color};">{pri}</span>
                    </div>
                    <div class="ai-card-body">{fix.get('instruction','')}</div>
                </div>
                """, unsafe_allow_html=True)

            if ai_tech.get("schema_recommendation"):
                st.markdown("**📊 Schema.org Recommendation**")
                st.markdown(f'<div class="ai-card"><div class="ai-card-body">{ai_tech["schema_recommendation"]}</div></div>', unsafe_allow_html=True)

        with atc2:
            st.markdown("**🖼️ Image Optimisation**")
            for tip in ai_tech.get("image_optimisation",[]):
                st.markdown(f'<div class="ai-card"><div class="ai-card-body">🖼️ {tip}</div></div>', unsafe_allow_html=True)

            st.markdown("**📐 Core Web Vitals**")
            for cwv in ai_tech.get("core_web_vitals",[]):
                st.markdown(f"""
                <div class="ai-card">
                    <div class="ai-card-title">{cwv.get('metric','')}</div>
                    <div class="ai-card-body">{cwv.get('tip','')}</div>
                </div>
                """, unsafe_allow_html=True)

            for lbl_, key in [("🤖 Robots.txt","robots_txt"),("🗺️ Sitemap","sitemap")]:
                if ai_tech.get(key):
                    st.markdown(f"**{lbl_}**")
                    st.markdown(f'<div class="ai-card"><div class="ai-card-body">{ai_tech[key]}</div></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: EXPORT
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📤 Export":
    raw   = st.session_state.raw_data
    audit = st.session_state.audit
    ai    = st.session_state.ai or {}

    st.markdown('<h1 style="color:#0f172a;font-size:26px;">📤 Export Audit Report</h1>', unsafe_allow_html=True)

    score = audit.get("overall_score",0)
    lbl, col = score_label(score)
    url   = raw.get("url","")

    st.markdown(f"""
    <div style="background:white;border:1px solid #e2e8f0;border-radius:16px;padding:20px 24px;margin-bottom:24px;">
        <div style="font-size:16px;font-weight:700;color:#0f172a;">Audit Summary</div>
        <div style="font-size:14px;color:#64748b;margin-top:6px;">🌐 {url}</div>
        <div style="font-size:14px;color:#64748b;">Score: <strong style="color:{col};">{score}/100 — {lbl}</strong></div>
    </div>
    """, unsafe_allow_html=True)

    ex1, ex2 = st.columns(2)

    with ex1:
        st.markdown("""
        <div style="background:white;border:1px solid #e2e8f0;border-radius:16px;padding:24px;text-align:center;margin-bottom:12px;">
            <div style="font-size:48px;">📄</div>
            <div style="font-weight:700;font-size:16px;margin:10px 0 6px;">PDF Report</div>
            <div style="font-size:13px;color:#64748b;">Professional formatted report with charts, issues, and AI recommendations</div>
        </div>
        """, unsafe_allow_html=True)
        with st.spinner("Generating PDF..."):
            pdf_bytes = export_pdf(raw, audit, ai)
        domain = raw.get("domain","site").replace(".","_")
        st.download_button(
            "⬇️ Download PDF Report",
            data=pdf_bytes,
            file_name=f"seo_audit_{domain}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )

    with ex2:
        st.markdown("""
        <div style="background:white;border:1px solid #e2e8f0;border-radius:16px;padding:24px;text-align:center;margin-bottom:12px;">
            <div style="font-size:48px;">📝</div>
            <div style="font-weight:700;font-size:16px;margin:10px 0 6px;">Markdown Report</div>
            <div style="font-size:13px;color:#64748b;">Clean Markdown for Notion, Obsidian, GitHub, or any docs tool</div>
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

    # Preview
    st.markdown('<div class="sec-hdr">👁️ Markdown Preview</div>', unsafe_allow_html=True)
    st.text_area("", value=md_text, height=400, label_visibility="collapsed")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🔑 Settings":
    st.markdown('<h1 style="color:#0f172a;font-size:26px;">🔑 Settings</h1>', unsafe_allow_html=True)

    current_key = _active_key()
    if current_key:
        src = "Your key (entered below)" if st.session_state.get("user_api_key","").strip() else "Server-configured"
        st.markdown(f"""
        <div style="background:#f0fdf4;border:2px solid #86efac;border-radius:12px;
                    padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px;">
            <div style="font-size:24px;">🟢</div>
            <div><div style="font-weight:700;color:#15803d;">API Key Active</div>
            <div style="font-size:12px;color:#166534;">Source: {src}</div></div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#fef2f2;border:2px solid #fca5a5;border-radius:12px;
                    padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px;">
            <div style="font-size:24px;">🔴</div>
            <div><div style="font-weight:700;color:#dc2626;">No API Key</div>
            <div style="font-size:12px;color:#991b1b;">AI suggestions will not be available without a key.</div></div>
        </div>
        """, unsafe_allow_html=True)

    s1, s2 = st.columns([3,2])

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
                    st.success("✅ Key saved!")
                    st.rerun()
                elif entered.strip():
                    st.error("Keys start with 'sk-'")
                else:
                    st.error("Please enter a key.")
        with c2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.user_api_key = ""
                os.environ.pop("OPENAI_API_KEY",None)
                st.rerun()

        st.markdown("""
        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;
                    padding:12px 14px;margin-top:10px;font-size:13px;color:#78350f;">
            🔒 Stored in browser session only — never saved to any server.
        </div>
        """, unsafe_allow_html=True)

    with s2:
        st.markdown('<div class="sec-hdr">📋 Get an API Key</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px;">
            <div style="font-size:13px;color:#374151;line-height:2.1;">
                1. Visit <a href="https://platform.openai.com/api-keys" target="_blank"
                   style="color:#4f46e5;font-weight:600;">platform.openai.com/api-keys</a><br>
                2. Sign in or create account<br>
                3. Click <strong>+ Create new secret key</strong><br>
                4. Copy (starts with <code>sk-</code>)<br>
                5. Paste above and save
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sec-hdr">💰 Cost Estimate</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px;font-size:13px;color:#374151;line-height:2.0;">
            GPT-4o: ~$0.005/analysis call<br>
            5 AI calls per audit × $0.005 = <strong>~$0.025/audit</strong><br>
            Very affordable for comprehensive analysis.
        </div>
        """, unsafe_allow_html=True)

    if current_key:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 Start SEO Audit →", type="primary"):
            st.session_state.page = "🔍 Audit"
            st.rerun()
