"""
app.py — AI Resume & Job Match Agent
Main Streamlit application entry point
"""

import json
import sys
import os

import streamlit as st

# ── Bootstrap path so `modules` is importable ───────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from modules.database import init_db

# ── Page config — MUST be first Streamlit call ──────────────────────────────
st.set_page_config(
    page_title="AI Resume & Job Match Agent",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Fonts & Base ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e3a5f 100%);
    color: white;
}
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] span {
    color: white !important;
}
[data-testid="stSidebar"] .stRadio > div {
    gap: 8px;
}
[data-testid="stSidebar"] .stRadio label {
    background: rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 10px 14px;
    transition: background 0.2s;
    cursor: pointer;
    display: block;
    font-weight: 500;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.18);
}

/* ── Metric Cards ── */
.metric-card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04);
    border-left: 4px solid #3b82f6;
    margin-bottom: 16px;
}
.metric-card h3 { margin: 0 0 4px 0; font-size: 13px; color: #6b7280; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
.metric-card .value { font-size: 36px; font-weight: 700; color: #0f172a; line-height: 1; }
.metric-card .sub { font-size: 12px; color: #9ca3af; margin-top: 4px; }

/* ── Score Badge ── */
.score-badge {
    display: inline-flex; align-items: center; justify-content: center;
    width: 80px; height: 80px; border-radius: 50%;
    font-size: 22px; font-weight: 700; color: white;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.score-high   { background: linear-gradient(135deg, #22c55e, #16a34a); }
.score-medium { background: linear-gradient(135deg, #f59e0b, #d97706); }
.score-low    { background: linear-gradient(135deg, #ef4444, #dc2626); }

/* ── Section headers ── */
.section-header {
    background: linear-gradient(90deg, #1e3a5f, #3b82f6);
    color: white; border-radius: 12px; padding: 14px 20px;
    margin: 20px 0 16px 0; font-size: 16px; font-weight: 600;
}

/* ── Skill pills ── */
.pill-container { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0; }
.pill {
    background: #eff6ff; color: #1d4ed8;
    border: 1px solid #bfdbfe; border-radius: 20px;
    padding: 4px 12px; font-size: 13px; font-weight: 500;
}
.pill-red   { background: #fef2f2; color: #dc2626; border-color: #fecaca; }
.pill-green { background: #f0fdf4; color: #16a34a; border-color: #bbf7d0; }
.pill-gray  { background: #f9fafb; color: #6b7280; border-color: #e5e7eb; }

/* ── Cards ── */
.info-card {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 16px; margin: 8px 0;
}

/* ── Buttons ── */
.stButton button {
    border-radius: 8px; font-weight: 500; transition: all 0.2s;
}
.stButton button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.12); }

/* ── Upload area ── */
[data-testid="stFileUploader"] {
    border: 2px dashed #93c5fd; border-radius: 12px;
    background: #eff6ff; padding: 8px;
}

/* ── Progress bars ── */
.stProgress > div > div { border-radius: 8px; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab"] {
    font-weight: 500; font-size: 14px;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: #f1f5f9; padding: 4px; border-radius: 10px;
}
.stTabs [aria-selected="true"] {
    background: white !important; border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* ── Interview question cards ── */
.q-card {
    background: white; border-radius: 12px;
    border-left: 4px solid #3b82f6;
    padding: 16px 20px; margin: 10px 0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.q-card.behavioral { border-color: #8b5cf6; }
.q-card.technical  { border-color: #0ea5e9; }
.q-card.situational{ border-color: #f59e0b; }
.q-card.culture    { border-color: #10b981; }

/* ── Cover letter box ── */
.cover-letter-box {
    background: white; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 32px; line-height: 1.8; font-size: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    white-space: pre-wrap;
}

/* ── Hide Streamlit branding ── */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Initialise DB & check credentials ────────────────────────────────────────
init_db()


def _show_setup_banner():
    """Show a helpful setup message when credentials are missing."""
    missing = []
    try:
        ok_openai = bool(st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY"))
    except Exception:
        ok_openai = bool(os.environ.get("OPENAI_API_KEY"))
    try:
        ok_supabase = bool(
            (st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")) and
            (st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY"))
        )
    except Exception:
        ok_supabase = bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY"))

    if not ok_openai:
        missing.append("OPENAI_API_KEY")
    if not ok_supabase:
        missing.append("SUPABASE_URL and SUPABASE_KEY")

    if missing:
        st.markdown("""
        <div style="background:#fef2f2;border:2px solid #fecaca;border-radius:16px;padding:32px;max-width:640px;margin:40px auto;">
            <div style="font-size:32px;margin-bottom:12px;">🔑</div>
            <h2 style="color:#dc2626;margin:0 0 8px 0;">Setup Required</h2>
            <p style="color:#7f1d1d;margin:0 0 16px 0;">The following credentials are missing:</p>
        """, unsafe_allow_html=True)
        for m in missing:
            st.markdown(f"- **`{m}`**")
        st.markdown("""
        <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;padding:16px;margin-top:16px;">
            <strong>📋 Add these to Streamlit Cloud → App → Settings → Secrets:</strong>
        </div>
        """, unsafe_allow_html=True)
        st.code(
            'OPENAI_API_KEY  = "sk-your-openai-key-here"\n'
            'SUPABASE_URL    = "https://your-project.supabase.co"\n'
            'SUPABASE_KEY    = "your-supabase-anon-key-here"',
            language="toml"
        )
        st.markdown("""
        <div style="margin-top:12px;font-size:13px;color:#6b7280;">
            <strong>Local dev?</strong> Copy <code>.env.example</code> to <code>.env</code> and fill in your keys.<br>
            Get OpenAI key: <a href="https://platform.openai.com/api-keys" target="_blank">platform.openai.com/api-keys</a><br>
            Get Supabase keys: <a href="https://supabase.com/dashboard" target="_blank">supabase.com</a> → Project Settings → API
        </div>
        """, unsafe_allow_html=True)
        st.stop()

_show_setup_banner()

# ── Session state helpers ────────────────────────────────────────────────────
def _ss(key, default=None):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]

_ss("active_resume_id", None)
_ss("active_resume_data", None)
_ss("active_job_analysis_id", None)
_ss("active_match", None)
_ss("active_ats", None)
_ss("active_cover_letter", None)
_ss("active_interview_qs", None)
_ss("page", "🏠 Dashboard")

# ── Sidebar Navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 20px 0 10px 0;'>
        <div style='font-size:40px;'>🎯</div>
        <div style='font-size:18px; font-weight:700; color:white;'>Resume AI Agent</div>
        <div style='font-size:12px; color:#94a3b8; margin-top:4px;'>Powered by OpenAI</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "📄 Upload Resume",
            "🔍 Job Matching",
            "🤖 ATS Checker",
            "✉️ Cover Letter",
            "💬 Interview Prep",
            "📊 Analytics",
            "📁 History",
        ],
        label_visibility="collapsed",
    )
    st.session_state.page = page

    # Active resume indicator
    if st.session_state.active_resume_data:
        parsed = st.session_state.active_resume_data.get("parsed_data", {})
        name = parsed.get("name", "Unknown")
        st.markdown("---")
        st.markdown(f"""
        <div style='background:rgba(255,255,255,0.1); border-radius:10px; padding:12px;'>
            <div style='font-size:11px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.05em;'>Active Resume</div>
            <div style='font-size:14px; font-weight:600; color:white; margin-top:4px;'>👤 {name}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style='font-size:11px; color:#64748b; text-align:center;'>
        Built with OpenAI API<br>© 2025 Resume AI Agent
    </div>
    """, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE ROUTING
# ═════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
if page == "🏠 Dashboard":
    from modules.database import get_dashboard_stats
    import plotly.graph_objects as go

    st.markdown("""
    <div style='padding: 8px 0 24px 0;'>
        <h1 style='font-size:32px; font-weight:700; color:#0f172a; margin:0;'>
            🎯 AI Resume & Job Match Agent
        </h1>
        <p style='color:#64748b; font-size:16px; margin-top:6px;'>
            Upload your resume, match against jobs, optimize for ATS, and land your dream role.
        </p>
    </div>
    """, unsafe_allow_html=True)

    try:
        stats = get_dashboard_stats()
    except Exception as e:
        st.error(f"Database error: {e}")
        st.info("Make sure your SUPABASE_URL and SUPABASE_KEY secrets are set correctly, and that you have run supabase_schema.sql in the Supabase SQL Editor.")
        st.stop()

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card" style="border-color:#3b82f6;">
            <h3>📄 Resumes</h3>
            <div class="value">{stats['total_resumes']}</div>
            <div class="sub">Uploaded & parsed</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card" style="border-color:#8b5cf6;">
            <h3>🔍 Analyses</h3>
            <div class="value">{stats['total_analyses']}</div>
            <div class="sub">Job matches run</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card" style="border-color:#10b981;">
            <h3>✉️ Cover Letters</h3>
            <div class="value">{stats['total_cover_letters']}</div>
            <div class="sub">Generated</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card" style="border-color:#f59e0b;">
            <h3>📈 Avg Match</h3>
            <div class="value">{stats['avg_match_score']}%</div>
            <div class="sub">Across all analyses</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<div class="section-header">📈 Match Score History</div>', unsafe_allow_html=True)
        if stats["all_scores"]:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=stats["all_scores"],
                x=list(range(1, len(stats["all_scores"]) + 1)),
                mode="lines+markers",
                line=dict(color="#3b82f6", width=3),
                marker=dict(size=8, color="#1d4ed8"),
                fill="tozeroy",
                fillcolor="rgba(59,130,246,0.1)",
                name="Match Score",
            ))
            fig.update_layout(
                xaxis_title="Analysis #", yaxis_title="Score (%)",
                yaxis=dict(range=[0, 100]),
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=40, r=20, t=20, b=40),
                height=280,
                showlegend=False,
            )
            fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
            fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No analyses yet. Upload a resume and run a job match to see your score history here.")

    with col_right:
        st.markdown('<div class="section-header">🕐 Recent Analyses</div>', unsafe_allow_html=True)
        if stats["recent_analyses"]:
            for item in stats["recent_analyses"]:
                score = item.get("match_result", {}).get("match_score", 0)
                color = "#22c55e" if score >= 75 else "#f59e0b" if score >= 50 else "#ef4444"
                st.markdown(f"""
                <div class="info-card" style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-weight:600; font-size:13px; color:#0f172a;">{item.get('job_title','Unknown Role')}</div>
                        <div style="font-size:12px; color:#6b7280;">{item.get('company_name','Unknown Co')} · {item.get('name','')}</div>
                    </div>
                    <div style="background:{color}; color:white; border-radius:20px; padding:4px 12px; font-weight:700; font-size:14px;">{score}%</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No analyses yet.")

    # Feature overview
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">🚀 How to Get Started</div>', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)
    for col, icon, title, desc in [
        (f1, "📄", "1. Upload Resume", "Upload your PDF or DOCX resume and let AI parse it instantly"),
        (f2, "🔍", "2. Match Jobs", "Paste a job description and get a detailed compatibility score"),
        (f3, "🤖", "3. ATS Check", "Optimize for Applicant Tracking Systems before applying"),
        (f4, "✉️", "4. Generate Assets", "Get a tailored cover letter and interview prep questions"),
    ]:
        with col:
            st.markdown(f"""
            <div class="info-card" style="text-align:center; padding:20px;">
                <div style="font-size:32px;">{icon}</div>
                <div style="font-weight:600; color:#0f172a; margin:8px 0 4px;">{title}</div>
                <div style="font-size:12px; color:#6b7280; line-height:1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# UPLOAD RESUME
# ─────────────────────────────────────────────
elif page == "📄 Upload Resume":
    from modules.parser import extract_resume_text
    from modules.agent import parse_resume
    from modules.database import save_resume, get_all_resumes, get_resume_by_id, delete_resume

    st.markdown('<h1 style="color:#0f172a;">📄 Upload & Parse Resume</h1>', unsafe_allow_html=True)
    st.markdown("Upload a PDF or DOCX resume and GPT-4o will extract all key information automatically.")

    col_upload, col_saved = st.columns([3, 2])

    with col_upload:
        st.markdown('<div class="section-header">📎 Upload New Resume</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Drop your resume here", type=["pdf", "docx"],
                                     help="Supports PDF and DOCX formats")

        if uploaded:
            with st.spinner("🔍 Extracting text from resume..."):
                raw_text = extract_resume_text(uploaded)

            if raw_text.startswith("[Error"):
                st.error(raw_text)
            else:
                st.success(f"✅ Extracted {len(raw_text)} characters from {uploaded.name}")

                with st.expander("📝 View Raw Text", expanded=False):
                    st.text(raw_text[:2000] + ("..." if len(raw_text) > 2000 else ""))

                if st.button("🤖 Parse Resume with GPT-4o", type="primary", use_container_width=True):
                    with st.spinner("🧠 GPT-4o is analyzing your resume..."):
                        parsed = parse_resume(raw_text)

                    if "error" in parsed and "name" not in parsed:
                        st.error(f"Parsing error: {parsed['error']}")
                    else:
                        name = parsed.get("name", uploaded.name.replace(".pdf","").replace(".docx",""))
                        resume_id = save_resume(name, uploaded.name, raw_text, parsed)

                        # Set active
                        st.session_state.active_resume_id = resume_id
                        st.session_state.active_resume_data = {
                            "id": resume_id,
                            "raw_text": raw_text,
                            "parsed_data": parsed,
                        }

                        st.success(f"✅ Resume parsed and saved! ID: {resume_id}")
                        st.rerun()

    with col_saved:
        st.markdown('<div class="section-header">📁 Saved Resumes</div>', unsafe_allow_html=True)
        resumes = get_all_resumes()

        if not resumes:
            st.info("No resumes saved yet. Upload one!")
        else:
            for r in resumes:
                is_active = r["id"] == st.session_state.active_resume_id
                border = "#3b82f6" if is_active else "#e2e8f0"
                bg = "#eff6ff" if is_active else "white"
                st.markdown(f"""
                <div style="background:{bg}; border:2px solid {border}; border-radius:10px;
                            padding:12px 16px; margin:6px 0;">
                    <div style="font-weight:600; color:#0f172a;">{r['name']}</div>
                    <div style="font-size:12px; color:#6b7280;">{r['filename']} · {r['created_at'][:10]}</div>
                    {'<span style="background:#3b82f6;color:white;border-radius:4px;padding:1px 6px;font-size:11px;">Active</span>' if is_active else ''}
                </div>
                """, unsafe_allow_html=True)

                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("Load", key=f"load_{r['id']}", use_container_width=True):
                        full = get_resume_by_id(r["id"])
                        st.session_state.active_resume_id = r["id"]
                        st.session_state.active_resume_data = full
                        st.rerun()
                with btn_col2:
                    if st.button("🗑️", key=f"del_{r['id']}", use_container_width=True):
                        delete_resume(r["id"])
                        if st.session_state.active_resume_id == r["id"]:
                            st.session_state.active_resume_id = None
                            st.session_state.active_resume_data = None
                        st.rerun()

    # Show parsed data if active
    if st.session_state.active_resume_data:
        st.markdown('<div class="section-header">👤 Parsed Resume Data</div>', unsafe_allow_html=True)
        parsed = st.session_state.active_resume_data.get("parsed_data", {})

        tab1, tab2, tab3, tab4 = st.tabs(["👤 Overview", "💼 Experience", "🎓 Education", "🛠️ Skills & Projects"])

        with tab1:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Personal Info**")
                for field, icon in [("name","👤"),("email","📧"),("phone","📞"),("location","📍")]:
                    val = parsed.get(field, "")
                    if val:
                        st.markdown(f"{icon} {val}")
                exp_years = parsed.get("total_experience_years", 0)
                st.markdown(f"⏱️ **{exp_years} years** total experience")
            with c2:
                st.markdown("**Summary**")
                st.markdown(f'<div class="info-card">{parsed.get("summary","No summary extracted.")}</div>',
                            unsafe_allow_html=True)
                if parsed.get("certifications"):
                    st.markdown("**Certifications**")
                    for cert in parsed["certifications"]:
                        st.markdown(f"🏆 {cert}")

        with tab2:
            for exp in parsed.get("experience", []):
                with st.expander(f"**{exp.get('title','')}** at {exp.get('company','')}"):
                    st.markdown(f"📅 {exp.get('duration','')} · {exp.get('years',0)} years")
                    for h in exp.get("highlights", []):
                        st.markdown(f"• {h}")

        with tab3:
            for edu in parsed.get("education", []):
                st.markdown(f"""
                <div class="info-card">
                    <strong>{edu.get('degree','')}</strong><br>
                    🎓 {edu.get('institution','')} · {edu.get('year','')}
                    {f" · GPA: {edu.get('gpa','')}" if edu.get('gpa') else ""}
                </div>
                """, unsafe_allow_html=True)

        with tab4:
            skills = parsed.get("skills", [])
            if skills:
                pills_html = '<div class="pill-container">' + "".join(
                    f'<span class="pill">{s}</span>' for s in skills
                ) + "</div>"
                st.markdown(pills_html, unsafe_allow_html=True)

            for proj in parsed.get("projects", []):
                with st.expander(f"🛠️ {proj.get('name','')}"):
                    st.markdown(proj.get("description",""))
                    techs = proj.get("technologies", [])
                    if techs:
                        st.markdown("**Tech:** " + ", ".join(techs))


# ─────────────────────────────────────────────
# JOB MATCHING
# ─────────────────────────────────────────────
elif page == "🔍 Job Matching":
    from modules.agent import match_job, get_resume_improvements
    from modules.database import save_job_analysis, get_analyses_for_resume
    import plotly.graph_objects as go

    st.markdown('<h1 style="color:#0f172a;">🔍 AI Job Matching</h1>', unsafe_allow_html=True)

    if not st.session_state.active_resume_data:
        st.warning("⚠️ No active resume. Please upload a resume first.")
        st.stop()

    parsed = st.session_state.active_resume_data.get("parsed_data", {})
    st.markdown(f"**Active Resume:** {parsed.get('name','Unknown')}")

    col_input, col_result = st.columns([2, 3])

    with col_input:
        st.markdown('<div class="section-header">📋 Job Details</div>', unsafe_allow_html=True)
        job_title = st.text_input("Job Title", placeholder="e.g. Senior Software Engineer")
        company_name = st.text_input("Company Name", placeholder="e.g. Google")
        job_description = st.text_area("Job Description", height=300,
                                        placeholder="Paste the full job description here...")

        if st.button("🔍 Analyze Match", type="primary", use_container_width=True):
            if not job_description.strip():
                st.error("Please enter a job description.")
            else:
                with st.spinner("🧠 GPT-4o is analyzing the match..."):
                    match = match_job(parsed, job_description)

                if "error" not in match:
                    from modules.agent import check_ats
                    raw_text = st.session_state.active_resume_data.get("raw_text","")
                    with st.spinner("🤖 Running ATS check..."):
                        ats = check_ats(raw_text, job_description)

                    job_id = save_job_analysis(
                        st.session_state.active_resume_id,
                        job_title, company_name, job_description,
                        match, ats
                    )
                    st.session_state.active_job_analysis_id = job_id
                    st.session_state.active_match = match
                    st.session_state.active_ats = ats
                    st.success("✅ Analysis complete!")
                    st.rerun()
                else:
                    st.error(f"Error: {match['error']}")

    with col_result:
        match = st.session_state.active_match
        if match and "match_score" in match:
            score = match["match_score"]
            score_class = "score-high" if score >= 75 else "score-medium" if score >= 50 else "score-low"

            st.markdown('<div class="section-header">📊 Match Results</div>', unsafe_allow_html=True)

            # Score + grade
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                st.markdown(f"""
                <div style="text-align:center; padding:20px;">
                    <div class="score-badge {score_class}">{score}%</div>
                    <div style="font-size:13px; color:#6b7280; margin-top:8px;">Match Score</div>
                </div>
                """, unsafe_allow_html=True)
            with sc2:
                st.markdown(f"""
                <div style="text-align:center; padding:20px;">
                    <div style="font-size:36px; font-weight:700; color:#0f172a;">{match.get('grade','N/A')}</div>
                    <div style="font-size:13px; color:#6b7280; margin-top:8px;">Grade</div>
                </div>
                """, unsafe_allow_html=True)
            with sc3:
                st.markdown(f"""
                <div style="text-align:center; padding:20px; font-size:13px; color:#0f172a;">
                    <div>Experience: <strong>{match.get('experience_match','N/A')}</strong></div>
                    <div style="margin-top:8px;">Education: <strong>{match.get('education_match','N/A')}</strong></div>
                </div>
                """, unsafe_allow_html=True)

            st.progress(score / 100)
            st.markdown(f'<div class="info-card">{match.get("summary","")}</div>', unsafe_allow_html=True)

            t1, t2, t3, t4 = st.tabs(["✅ Strengths", "❌ Missing Skills", "💡 Recommendations", "📈 Radar"])

            with t1:
                for s in match.get("strengths", []):
                    st.markdown(f'<div class="info-card">✅ {s}</div>', unsafe_allow_html=True)

            with t2:
                missing = match.get("missing_skills", [])
                if missing:
                    pills = '<div class="pill-container">' + "".join(
                        f'<span class="pill pill-red">❌ {s}</span>' for s in missing
                    ) + "</div>"
                    st.markdown(pills, unsafe_allow_html=True)
                else:
                    st.success("Great! No critical missing skills found.")

            with t3:
                for r in match.get("recommendations", []):
                    st.markdown(f'<div class="info-card">💡 {r}</div>', unsafe_allow_html=True)

            with t4:
                # Radar chart
                categories = ["Skills Match", "Experience", "Education", "Cultural Fit", "Keywords"]
                exp_map = {"Strong": 90, "Moderate": 60, "Weak": 30}
                values = [
                    len(match.get("matching_skills",[])) / max(len(match.get("matching_skills",[])) + len(match.get("missing_skills",[])), 1) * 100,
                    exp_map.get(match.get("experience_match","Moderate"), 60),
                    exp_map.get(match.get("education_match","Moderate"), 60),
                    score * 0.9,
                    score * 0.85,
                ]
                fig = go.Figure(data=go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill="toself",
                    line_color="#3b82f6",
                    fillcolor="rgba(59,130,246,0.2)",
                ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0,100])),
                    showlegend=False, margin=dict(l=40,r=40,t=20,b=20), height=300,
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Enter a job description and click **Analyze Match** to see results here.")


# ─────────────────────────────────────────────
# ATS CHECKER
# ─────────────────────────────────────────────
elif page == "🤖 ATS Checker":
    from modules.agent import check_ats
    import plotly.graph_objects as go

    st.markdown('<h1 style="color:#0f172a;">🤖 ATS Compatibility Checker</h1>', unsafe_allow_html=True)
    st.markdown("Check how well your resume performs against Applicant Tracking Systems.")

    if not st.session_state.active_resume_data:
        st.warning("⚠️ No active resume. Please upload a resume first.")
        st.stop()

    col_in, col_out = st.columns([2, 3])

    with col_in:
        st.markdown('<div class="section-header">⚙️ ATS Settings</div>', unsafe_allow_html=True)
        job_desc_ats = st.text_area("Job Description (optional)", height=200,
                                     placeholder="Paste a job description for targeted keyword analysis...")

        if st.button("🔍 Run ATS Check", type="primary", use_container_width=True):
            raw_text = st.session_state.active_resume_data.get("raw_text","")
            with st.spinner("🤖 Running ATS analysis..."):
                ats = check_ats(raw_text, job_desc_ats)
            st.session_state.active_ats = ats
            st.rerun()

    with col_out:
        ats = st.session_state.active_ats
        if ats and "ats_score" in ats:
            score = ats["ats_score"]
            score_class = "score-high" if score >= 75 else "score-medium" if score >= 50 else "score-low"

            st.markdown('<div class="section-header">📊 ATS Results</div>', unsafe_allow_html=True)

            sc1, sc2 = st.columns(2)
            with sc1:
                st.markdown(f"""
                <div style="text-align:center; padding:16px;">
                    <div class="score-badge {score_class}">{score}%</div>
                    <div style="font-size:13px; color:#6b7280; margin-top:8px;">ATS Score</div>
                </div>
                """, unsafe_allow_html=True)
            with sc2:
                st.markdown(f"""
                <div style="padding:16px; font-size:13px;">
                    <div><strong>Grade:</strong> {ats.get('grade','N/A')}</div>
                    <div style="margin-top:6px;"><strong>Length:</strong> {ats.get('length_assessment','N/A')}</div>
                    <div style="margin-top:6px;"><strong>Readability:</strong> {ats.get('readability_score',0)}%</div>
                </div>
                """, unsafe_allow_html=True)

            st.progress(score / 100)
            st.markdown(f'<div class="info-card">{ats.get("summary","")}</div>', unsafe_allow_html=True)

            t1, t2, t3, t4 = st.tabs(["⚠️ Issues", "🔑 Keywords", "📋 Sections", "💡 Suggestions"])

            with t1:
                issues = ats.get("formatting_issues", [])
                if issues:
                    for issue in issues:
                        st.markdown(f'<div class="info-card" style="border-left:3px solid #ef4444;">⚠️ {issue}</div>',
                                    unsafe_allow_html=True)
                else:
                    st.success("No major formatting issues found!")

            with t2:
                kw = ats.get("keyword_density", {})
                kw_score = kw.get("keyword_score", 0)
                st.markdown(f"**Keyword Score:** {kw_score}%")
                st.progress(kw_score / 100)

                if kw.get("found_keywords"):
                    st.markdown("**✅ Found Keywords:**")
                    pills = '<div class="pill-container">' + "".join(
                        f'<span class="pill pill-green">{k}</span>' for k in kw["found_keywords"]
                    ) + "</div>"
                    st.markdown(pills, unsafe_allow_html=True)

                if kw.get("missing_keywords"):
                    st.markdown("**❌ Missing Keywords:**")
                    pills = '<div class="pill-container">' + "".join(
                        f'<span class="pill pill-red">{k}</span>' for k in kw["missing_keywords"]
                    ) + "</div>"
                    st.markdown(pills, unsafe_allow_html=True)

            with t3:
                sections = ats.get("section_analysis", {})
                for sec_name, sec_data in sections.items():
                    sec_score = sec_data.get("score", 0) if isinstance(sec_data, dict) else 0
                    sec_notes = sec_data.get("notes","") if isinstance(sec_data, dict) else str(sec_data)
                    color = "#22c55e" if sec_score >= 80 else "#f59e0b" if sec_score >= 60 else "#ef4444"
                    st.markdown(f"""
                    <div class="info-card" style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <strong>{sec_name.replace('_',' ').title()}</strong>
                            <div style="font-size:12px; color:#6b7280;">{sec_notes}</div>
                        </div>
                        <div style="background:{color}; color:white; border-radius:20px; padding:4px 12px; font-weight:700;">{sec_score}%</div>
                    </div>
                    """, unsafe_allow_html=True)

            with t4:
                suggestions = ats.get("optimization_suggestions", [])
                priority_colors = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}
                for s in suggestions:
                    priority = s.get("priority","Low")
                    color = priority_colors.get(priority, "#6b7280")
                    st.markdown(f"""
                    <div class="info-card">
                        <span style="background:{color}; color:white; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:600;">{priority}</span>
                        <span style="margin-left:10px; font-size:13px;">{s.get('suggestion','')}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Click **Run ATS Check** to analyze your resume.")


# ─────────────────────────────────────────────
# COVER LETTER
# ─────────────────────────────────────────────
elif page == "✉️ Cover Letter":
    from modules.agent import generate_cover_letter
    from modules.database import save_cover_letter, get_cover_letters_for_resume
    from modules.exporter import export_cover_letter_pdf

    st.markdown('<h1 style="color:#0f172a;">✉️ AI Cover Letter Generator</h1>', unsafe_allow_html=True)

    if not st.session_state.active_resume_data:
        st.warning("⚠️ No active resume. Please upload a resume first.")
        st.stop()

    parsed = st.session_state.active_resume_data.get("parsed_data", {})

    col_in, col_out = st.columns([2, 3])

    with col_in:
        st.markdown('<div class="section-header">⚙️ Cover Letter Settings</div>', unsafe_allow_html=True)
        cl_company = st.text_input("Company Name", placeholder="e.g. Google")
        cl_job_title = st.text_input("Job Title", placeholder="e.g. Software Engineer")
        cl_tone = st.selectbox("Tone", ["Professional", "Enthusiastic", "Formal", "Conversational", "Creative"])
        cl_jd = st.text_area("Job Description", height=200,
                              placeholder="Paste the job description for a tailored letter...")

        if st.button("✍️ Generate Cover Letter", type="primary", use_container_width=True):
            if not cl_jd.strip():
                st.error("Please enter a job description.")
            else:
                with st.spinner("✍️ GPT-4o is writing your cover letter..."):
                    letter = generate_cover_letter(parsed, cl_jd, cl_company, cl_tone)

                st.session_state.active_cover_letter = letter
                jid = st.session_state.active_job_analysis_id or 0
                save_cover_letter(
                    st.session_state.active_resume_id, jid,
                    cl_company, cl_job_title, letter, cl_tone
                )
                st.success("✅ Cover letter generated!")
                st.rerun()

        # History
        st.markdown('<div class="section-header">📁 Saved Letters</div>', unsafe_allow_html=True)
        saved_letters = get_cover_letters_for_resume(st.session_state.active_resume_id or 0)
        for l in saved_letters:
            if st.button(f"📄 {l['company_name']} — {l['job_title']}", key=f"cl_{l['id']}", use_container_width=True):
                st.session_state.active_cover_letter = l["content"]
                st.rerun()

    with col_out:
        letter = st.session_state.active_cover_letter
        if letter:
            st.markdown('<div class="section-header">📄 Generated Cover Letter</div>', unsafe_allow_html=True)

            # Edit area
            edited = st.text_area("Edit your cover letter:", value=letter, height=500, key="cl_edit")
            st.session_state.active_cover_letter = edited

            # Export
            ec1, ec2 = st.columns(2)
            with ec1:
                st.download_button(
                    "📥 Download as TXT",
                    data=edited,
                    file_name=f"cover_letter_{cl_company or 'company'}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with ec2:
                pdf_bytes = export_cover_letter_pdf(
                    edited,
                    parsed.get("name","Candidate"),
                    cl_company,
                    cl_job_title
                )
                st.download_button(
                    "📥 Download as PDF",
                    data=pdf_bytes,
                    file_name=f"cover_letter_{cl_company or 'company'}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
        else:
            st.info("Fill in the details and click **Generate Cover Letter** to create a tailored letter.")


# ─────────────────────────────────────────────
# INTERVIEW PREP
# ─────────────────────────────────────────────
elif page == "💬 Interview Prep":
    from modules.agent import generate_interview_questions
    from modules.database import save_interview_questions, get_interview_questions_for_resume

    st.markdown('<h1 style="color:#0f172a;">💬 AI Interview Prep</h1>', unsafe_allow_html=True)

    if not st.session_state.active_resume_data:
        st.warning("⚠️ No active resume. Please upload a resume first.")
        st.stop()

    parsed = st.session_state.active_resume_data.get("parsed_data", {})

    col_in, col_out = st.columns([2, 3])

    with col_in:
        st.markdown('<div class="section-header">⚙️ Interview Settings</div>', unsafe_allow_html=True)
        ip_jd = st.text_area("Job Description", height=200,
                              placeholder="Paste the job description for role-specific questions...")
        num_q = st.slider("Number of Questions", 5, 20, 10)

        if st.button("💬 Generate Questions", type="primary", use_container_width=True):
            if not ip_jd.strip():
                st.error("Please enter a job description.")
            else:
                with st.spinner("🧠 GPT-4o is preparing your interview questions..."):
                    qs = generate_interview_questions(parsed, ip_jd, num_q)

                if "error" not in qs:
                    st.session_state.active_interview_qs = qs
                    save_interview_questions(
                        st.session_state.active_resume_id,
                        st.session_state.active_job_analysis_id or 0,
                        qs
                    )
                    st.success("✅ Questions generated!")
                    st.rerun()
                else:
                    st.error(f"Error: {qs['error']}")

    with col_out:
        qs = st.session_state.active_interview_qs
        if qs and not isinstance(qs, str):
            st.markdown('<div class="section-header">💬 Interview Questions</div>', unsafe_allow_html=True)

            categories = [
                ("behavioral", "🎯 Behavioral", "behavioral"),
                ("technical", "💻 Technical", "technical"),
                ("situational", "🤔 Situational", "situational"),
                ("culture_fit", "🌱 Culture Fit", "culture"),
            ]

            for key, label, css_class in categories:
                items = qs.get(key, [])
                if items:
                    with st.expander(f"{label} ({len(items)} questions)", expanded=(key=="behavioral")):
                        for i, q in enumerate(items, 1):
                            question = q.get("question","")
                            why = q.get("why_asked","")
                            framework = q.get("suggested_answer_framework") or q.get("key_points_to_cover") or q.get("ideal_response_direction") or q.get("tips","")

                            if isinstance(framework, list):
                                framework = " · ".join(framework)

                            st.markdown(f"""
                            <div class="q-card {css_class}">
                                <div style="font-weight:600; color:#0f172a; font-size:14px;">Q{i}: {question}</div>
                                <div style="font-size:12px; color:#6b7280; margin-top:6px;">
                                    <em>Why asked: {why}</em>
                                </div>
                                <div style="font-size:12px; color:#0f172a; margin-top:8px; background:#f8fafc; padding:8px; border-radius:6px;">
                                    💡 {framework}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
        else:
            st.info("Click **Generate Questions** to get role-specific interview questions with answer guidance.")


# ─────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────
elif page == "📊 Analytics":
    from modules.database import get_dashboard_stats, get_all_analyses
    import plotly.express as px
    import plotly.graph_objects as go

    st.markdown('<h1 style="color:#0f172a;">📊 Analytics Dashboard</h1>', unsafe_allow_html=True)

    try:
        stats = get_dashboard_stats()
    except Exception as e:
        st.error(f"Database error: {e}")
        st.info("Make sure your SUPABASE_URL and SUPABASE_KEY secrets are set correctly, and that you have run supabase_schema.sql in the Supabase SQL Editor.")
        st.stop()
    analyses = get_all_analyses()

    if not analyses:
        st.info("No data yet. Run some job analyses to see analytics here.")
        st.stop()

    # Score distribution
    scores = [a["match_result"].get("match_score", 0) for a in analyses if a.get("match_result")]
    ats_scores = [a["ats_result"].get("ats_score", 0) for a in analyses if a.get("ats_result")]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">📈 Match Score Distribution</div>', unsafe_allow_html=True)
        fig = go.Figure(data=go.Histogram(
            x=scores, nbinsx=10,
            marker_color="#3b82f6", opacity=0.8,
        ))
        fig.update_layout(
            xaxis_title="Match Score (%)", yaxis_title="Count",
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40,r=20,t=10,b=40), height=280,
        )
        fig.update_xaxes(range=[0,100], showgrid=True, gridcolor="#f1f5f9")
        fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">🤖 ATS Score Distribution</div>', unsafe_allow_html=True)
        fig2 = go.Figure(data=go.Histogram(
            x=ats_scores, nbinsx=10,
            marker_color="#8b5cf6", opacity=0.8,
        ))
        fig2.update_layout(
            xaxis_title="ATS Score (%)", yaxis_title="Count",
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40,r=20,t=10,b=40), height=280,
        )
        fig2.update_xaxes(range=[0,100], showgrid=True, gridcolor="#f1f5f9")
        fig2.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
        st.plotly_chart(fig, use_container_width=True)

    # Scatter: match vs ats
    st.markdown('<div class="section-header">🎯 Match Score vs ATS Score</div>', unsafe_allow_html=True)
    scatter_data = [
        {
            "Match Score": a["match_result"].get("match_score", 0),
            "ATS Score": a["ats_result"].get("ats_score", 0),
            "Job": f"{a.get('job_title','?')} @ {a.get('company_name','?')}",
        }
        for a in analyses
        if a.get("match_result") and a.get("ats_result")
    ]
    if scatter_data:
        import pandas as pd
        df = pd.DataFrame(scatter_data)
        fig3 = px.scatter(
            df, x="Match Score", y="ATS Score", hover_data=["Job"],
            color="Match Score", color_continuous_scale="Blues",
            range_x=[0,100], range_y=[0,100],
        )
        fig3.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40,r=20,t=10,b=40), height=350,
        )
        fig3.add_shape(type="line", x0=0,y0=0,x1=100,y1=100,
                       line=dict(color="#e5e7eb", dash="dot"))
        st.plotly_chart(fig3, use_container_width=True)

    # Table
    st.markdown('<div class="section-header">📋 All Analyses</div>', unsafe_allow_html=True)
    table_data = []
    for a in analyses:
        table_data.append({
            "Candidate": a.get("candidate_name",""),
            "Job Title": a.get("job_title",""),
            "Company": a.get("company_name",""),
            "Match %": a["match_result"].get("match_score",0),
            "ATS %": a["ats_result"].get("ats_score",0),
            "Grade": a["match_result"].get("grade",""),
            "Date": a.get("created_at","")[:10],
        })
    if table_data:
        import pandas as pd
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# HISTORY
# ─────────────────────────────────────────────
elif page == "📁 History":
    from modules.database import get_all_analyses, get_resume_by_id
    from modules.exporter import export_analysis_pdf

    st.markdown('<h1 style="color:#0f172a;">📁 Analysis History</h1>', unsafe_allow_html=True)

    analyses = get_all_analyses()

    if not analyses:
        st.info("No analyses saved yet. Run a job match to see history here.")
        st.stop()

    for a in analyses:
        score = a["match_result"].get("match_score", 0)
        ats_score = a["ats_result"].get("ats_score", 0)
        color = "#22c55e" if score >= 75 else "#f59e0b" if score >= 50 else "#ef4444"

        with st.expander(
            f"{'🟢' if score >= 75 else '🟡' if score >= 50 else '🔴'} "
            f"{a.get('job_title','Unknown')} @ {a.get('company_name','Unknown')} — "
            f"Match: {score}% · ATS: {ats_score}% · {a.get('created_at','')[:10]}"
        ):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Candidate:** {a.get('candidate_name','')}")
                st.markdown(f"**Summary:** {a['match_result'].get('summary','')}")
                if a["match_result"].get("strengths"):
                    st.markdown("**Strengths:**")
                    for s in a["match_result"]["strengths"][:3]:
                        st.markdown(f"• {s}")
            with c2:
                if a["match_result"].get("missing_skills"):
                    st.markdown("**Missing Skills:**")
                    pills = '<div class="pill-container">' + "".join(
                        f'<span class="pill pill-red">{s}</span>'
                        for s in a["match_result"]["missing_skills"][:8]
                    ) + "</div>"
                    st.markdown(pills, unsafe_allow_html=True)
                if a["match_result"].get("recommendations"):
                    st.markdown("**Recommendations:**")
                    for r in a["match_result"]["recommendations"][:2]:
                        st.markdown(f"• {r}")

            # Export PDF
            pdf_bytes = export_analysis_pdf(
                a["match_result"], a["ats_result"],
                a.get("candidate_name","Candidate"),
                a.get("job_title","Role"), a.get("company_name","Company")
            )
            st.download_button(
                "📥 Download Analysis PDF",
                data=pdf_bytes,
                file_name=f"analysis_{a.get('id',0)}.pdf",
                mime="application/pdf",
                key=f"pdf_dl_{a['id']}",
            )
