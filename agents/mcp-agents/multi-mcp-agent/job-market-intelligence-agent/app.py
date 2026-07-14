"""
Job Market Intelligence Agent — Streamlit UI
HireGen.co · Powered by Dice + Indeed + HubSpot MCP
"""

import streamlit as st
import json
import time
from datetime import datetime
from agent import run_agent

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Job Market Intelligence · HireGen.co",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Base */
[data-testid="stAppViewContainer"] { background: #0E0F13; }
[data-testid="stSidebar"] { background: #13141A; border-right: 1px solid #1E2030; }
section[data-testid="stSidebar"] > div { padding-top: 1.5rem; }

/* Typography */
h1, h2, h3 { font-family: 'Inter', sans-serif; }

/* Cards */
.intel-card {
    background: #13141A;
    border: 1px solid #1E2030;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 12px;
}
.intel-card:hover { border-color: #2E3150; }

/* Priority badges */
.badge {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: .04em;
    text-transform: uppercase;
}
.badge-a { background: #2D1F4E; color: #A78BFA; border: 1px solid #4C3580; }
.badge-b { background: #1F2D1F; color: #6EE7B7; border: 1px solid #2D5030; }
.badge-c { background: #2D2515; color: #FCD34D; border: 1px solid #50400F; }

/* Metric tiles */
.metric-tile {
    background: #13141A;
    border: 1px solid #1E2030;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    text-align: center;
}
.metric-value { font-size: 2rem; font-weight: 700; color: #E2E8F0; line-height: 1; }
.metric-label { font-size: 12px; color: #6B7280; margin-top: 4px; text-transform: uppercase; letter-spacing: .05em; }

/* Tool call log */
.tool-log {
    background: #0A0B10;
    border: 1px solid #1A1B2E;
    border-radius: 8px;
    padding: .75rem 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #6EE7B7;
    max-height: 280px;
    overflow-y: auto;
}
.log-line { padding: 2px 0; border-bottom: 1px solid #0E0F1A; }
.log-line.tool { color: #A78BFA; }
.log-line.status { color: #FCD34D; }
.log-line.error { color: #FCA5A5; }

/* Highlights box */
.highlight-box {
    background: linear-gradient(135deg, #1A1B30 0%, #13141A 100%);
    border: 1px solid #2E3150;
    border-left: 3px solid #7C3AED;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    font-size: 14px;
    color: #CBD5E1;
    line-height: 1.7;
    margin-bottom: 1rem;
}

/* Role pill */
.role-pill {
    display: inline-block;
    background: #1E2030;
    color: #94A3B8;
    border-radius: 4px;
    font-size: 11px;
    padding: 2px 8px;
    margin: 2px 2px 2px 0;
}

/* HubSpot badge */
.hs-created { color: #6EE7B7; font-size: 11px; }
.hs-updated { color: #FCD34D; font-size: 11px; }

/* Empty state */
.empty-state {
    text-align: center;
    padding: 3rem;
    color: #4B5563;
}

/* Run button */
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #7C3AED, #4F46E5);
    border: none;
    color: white;
    font-weight: 600;
    padding: .6rem 2rem;
    border-radius: 8px;
    width: 100%;
    font-size: 15px;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #6D28D9, #4338CA);
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = None
if "log_lines" not in st.session_state:
    st.session_state.log_lines = []
if "running" not in st.session_state:
    st.session_state.running = False
if "raw_response" not in st.session_state:
    st.session_state.raw_response = ""

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎯 HireGen.co")
    st.markdown("**Job Market Intelligence Agent**")
    st.markdown("---")

    st.markdown("#### Search configuration")

    default_categories = [
        "Machine Learning Engineer",
        "Backend Engineer",
        "Full Stack Engineer",
        "AI Engineer",
        "Platform Engineer",
        "MLOps Engineer",
        "Data Engineer",
    ]

    selected_categories = st.multiselect(
        "Job categories",
        options=default_categories,
        default=default_categories[:5],
        help="Which engineering roles to monitor across Dice and Indeed",
    )

    custom_cat = st.text_input(
        "Add custom category",
        placeholder="e.g. LLM Infrastructure Engineer",
    )
    if custom_cat and custom_cat not in selected_categories:
        selected_categories.append(custom_cat)

    st.markdown("---")

    location = st.text_input(
        "Target location",
        value="San Francisco, CA",
        help="Primary hiring location filter",
    )

    min_roles = st.slider(
        "Min roles to qualify as prospect",
        min_value=1,
        max_value=10,
        value=3,
        help="Companies posting this many+ roles get flagged as prospects",
    )

    st.markdown("---")
    st.markdown("#### MCP servers")
    st.markdown("""
<div style="font-size:12px; color:#6B7280; line-height:1.8">
✅ <span style="color:#6EE7B7">Dice</span> — job board<br>
✅ <span style="color:#6EE7B7">Indeed</span> — job board + company data<br>
✅ <span style="color:#6EE7B7">HubSpot</span> — CRM sync
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    run_clicked = st.button("▶ Run Intelligence Scan", type="primary")

# ── Main header ───────────────────────────────────────────────────────────────
col_title, col_ts = st.columns([4, 1])
with col_title:
    st.markdown("## Job Market Intelligence")
    st.markdown(
        "<p style='color:#6B7280;font-size:14px;margin-top:-12px'>"
        "Monitor Dice + Indeed · Qualify prospects · Sync to HubSpot CRM"
        "</p>",
        unsafe_allow_html=True,
    )
with col_ts:
    st.markdown(
        f"<p style='color:#4B5563;font-size:12px;text-align:right;padding-top:8px'>"
        f"{datetime.now().strftime('%b %d, %Y %H:%M')}</p>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ── Run agent ─────────────────────────────────────────────────────────────────
if run_clicked and selected_categories:
    st.session_state.running = True
    st.session_state.log_lines = []
    st.session_state.results = None

    log_placeholder = st.empty()
    progress_placeholder = st.empty()

    log_lines = []

    def stream_cb(event_type: str, text: str):
        ts = datetime.now().strftime("%H:%M:%S")
        css = "tool" if event_type == "tool" else ("error" if event_type == "error" else "status")
        log_lines.append(f'<div class="log-line {css}">[{ts}] {text}</div>')
        log_html = "<br>".join(log_lines[-30:])  # last 30 lines
        log_placeholder.markdown(
            f'<div class="tool-log">{log_html}</div>',
            unsafe_allow_html=True,
        )

    stream_cb("status", f"Starting scan for: {', '.join(selected_categories)}")
    stream_cb("status", f"Location: {location} | Min roles: {min_roles}")

    with st.spinner("Agent running — this may take 30–90 seconds..."):
        result = run_agent(
            job_categories=selected_categories,
            location=location,
            min_roles_threshold=min_roles,
            stream_callback=stream_cb,
        )

    st.session_state.results = result.get("result")
    st.session_state.raw_response = result.get("raw_response", "")
    st.session_state.log_lines = log_lines
    st.session_state.running = False

    log_placeholder.empty()
    st.rerun()

# ── Results display ───────────────────────────────────────────────────────────
if st.session_state.results:
    r = st.session_state.results

    # ── Summary metrics ──
    m1, m2, m3, m4, m5 = st.columns(5)
    metrics = [
        (str(r.get("jobs_found", "—")), "Jobs Found"),
        (str(r.get("companies_analyzed", "—")), "Companies"),
        (str(r.get("prospects_created", "—")), "HubSpot Created"),
        (str(r.get("prospects_updated", "—")), "HubSpot Updated"),
        (str(len(r.get("priority_a", []))), "Priority A"),
    ]
    for col, (val, label) in zip([m1, m2, m3, m4, m5], metrics):
        with col:
            st.markdown(
                f'<div class="metric-tile">'
                f'<div class="metric-value">{val}</div>'
                f'<div class="metric-label">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Highlights ──
    if r.get("highlights"):
        st.markdown(
            f'<div class="highlight-box">💡 {r["highlights"]}</div>',
            unsafe_allow_html=True,
        )

    # ── Prospect tabs ──
    tab_a, tab_b, tab_c, tab_raw = st.tabs([
        f"🔴 Priority A ({len(r.get('priority_a', []))})",
        f"🟡 Priority B ({len(r.get('priority_b', []))})",
        f"⚪ Priority C ({len(r.get('priority_c', []))})",
        "📄 Raw response",
    ])

    def render_prospects(prospects: list, badge_class: str, priority_label: str):
        if not prospects:
            st.markdown(
                '<div class="empty-state">No prospects at this priority level</div>',
                unsafe_allow_html=True,
            )
            return

        for p in prospects:
            company = p.get("company", "Unknown")
            roles_count = p.get("roles", p.get("role_count", 0))
            top_roles = p.get("top_roles", p.get("roles_list", []))
            hubspot_id = p.get("hubspot_id", "")
            hubspot_action = p.get("hubspot_action", "")
            industry = p.get("industry", "")
            location_p = p.get("location", p.get("headquarters", ""))
            size = p.get("size", p.get("company_size", ""))

            roles_html = "".join(
                f'<span class="role-pill">{r}</span>'
                for r in (top_roles[:5] if isinstance(top_roles, list) else [])
            )

            hs_html = ""
            if hubspot_id:
                action_class = "hs-created" if "creat" in hubspot_action.lower() else "hs-updated"
                action_icon = "✨" if "creat" in hubspot_action.lower() else "🔄"
                hs_html = f'<span class="{action_class}">{action_icon} HubSpot: {hubspot_action or hubspot_id}</span>'

            meta_parts = [x for x in [industry, location_p, f"{size} employees" if size else ""] if x]
            meta_str = " · ".join(meta_parts)

            st.markdown(f"""
<div class="intel-card">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
    <span class="badge {badge_class}">{priority_label}</span>
    <span style="font-size:16px;font-weight:600;color:#E2E8F0">{company}</span>
    <span style="margin-left:auto;font-size:13px;color:#A78BFA;font-weight:600">{roles_count} open roles</span>
  </div>
  {f'<div style="font-size:12px;color:#6B7280;margin-bottom:8px">{meta_str}</div>' if meta_str else ''}
  <div style="margin-bottom:8px">{roles_html}</div>
  {f'<div style="margin-top:8px">{hs_html}</div>' if hs_html else ''}
</div>
""", unsafe_allow_html=True)

    with tab_a:
        st.markdown(
            "<p style='font-size:13px;color:#6B7280;margin-bottom:12px'>"
            "5+ open roles — urgent outreach recommended this week</p>",
            unsafe_allow_html=True,
        )
        render_prospects(r.get("priority_a", []), "badge-a", "Priority A")

    with tab_b:
        st.markdown(
            "<p style='font-size:13px;color:#6B7280;margin-bottom:12px'>"
            "3–4 open roles — reach out this week</p>",
            unsafe_allow_html=True,
        )
        render_prospects(r.get("priority_b", []), "badge-b", "Priority B")

    with tab_c:
        st.markdown(
            "<p style='font-size:13px;color:#6B7280;margin-bottom:12px'>"
            "1–2 open roles — add to pipeline for next sprint</p>",
            unsafe_allow_html=True,
        )
        render_prospects(r.get("priority_c", []), "badge-c", "Priority C")

    with tab_raw:
        st.markdown("**Full agent response**")
        st.text_area(
            "",
            value=st.session_state.raw_response,
            height=400,
            label_visibility="collapsed",
        )
        st.download_button(
            "⬇ Download raw JSON",
            data=json.dumps(r, indent=2),
            file_name=f"job_intel_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
        )

elif not st.session_state.running:
    # ── Empty state ──
    st.markdown("""
<div style="text-align:center;padding:4rem 2rem">
  <div style="font-size:48px;margin-bottom:16px">🎯</div>
  <h3 style="color:#E2E8F0;margin-bottom:8px">Ready to scan</h3>
  <p style="color:#6B7280;font-size:14px;max-width:400px;margin:0 auto">
    Configure your search in the sidebar and click <strong style="color:#A78BFA">Run Intelligence Scan</strong>.
    The agent will search Dice and Indeed, identify high-intent hiring companies,
    and sync them to your HubSpot CRM automatically.
  </p>
</div>
""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;font-size:11px;color:#374151'>"
    "HireGen.co · Job Market Intelligence Agent · "
    "Powered by Dice MCP · Indeed MCP · HubSpot MCP · Claude claude-sonnet-4-6"
    "</p>",
    unsafe_allow_html=True,
)
