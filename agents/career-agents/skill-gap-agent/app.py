"""
app.py — AI Skill Gap Agent
============================
Production-ready Streamlit application for career skill gap analysis.
Run: streamlit run app.py
"""

from __future__ import annotations
import os
import json
from datetime import datetime
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from dotenv import load_dotenv

load_dotenv()

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="AI Skill Gap Agent",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Module imports ────────────────────────────────────────────────────────────
from modules import parser, database, agent, exporter

# ── DB bootstrap ──────────────────────────────────────────────────────────────
database.init_db()

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ─────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    background: #0F0F1A !important;
    color: #E2E8F0;
}
[data-testid="stSidebar"] {
    background: #13132B !important;
    border-right: 1px solid #2D2D5E;
}

/* ── Metric cards ─────────────────────────── */
.metric-card {
    background: linear-gradient(135deg, #1A1A3E 0%, #16213E 100%);
    border: 1px solid #2D2D5E;
    border-radius: 16px;
    padding: 20px 24px;
    text-align: center;
    transition: transform 0.2s, border-color 0.2s;
}
.metric-card:hover { transform: translateY(-2px); border-color: #7C3AED; }
.metric-value { font-size: 2.4rem; font-weight: 800; color: #7C3AED; line-height: 1; }
.metric-label { font-size: 0.8rem; color: #94A3B8; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em; }
.metric-sub { font-size: 0.9rem; color: #C4B5FD; margin-top: 2px; }

/* ── Section headers ──────────────────────── */
.section-header {
    font-size: 1.3rem;
    font-weight: 700;
    color: #E2E8F0;
    margin: 24px 0 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(to right, #7C3AED33, transparent);
    margin-left: 12px;
}

/* ── Score badge ──────────────────────────── */
.score-badge {
    display: inline-block;
    background: linear-gradient(135deg, #7C3AED, #4F46E5);
    color: white;
    font-size: 3.5rem;
    font-weight: 900;
    padding: 16px 32px;
    border-radius: 20px;
    text-align: center;
    box-shadow: 0 0 40px #7C3AED44;
    letter-spacing: -1px;
}
.score-grade { font-size: 1.2rem; font-weight: 600; margin-top: 4px; color: #C4B5FD; }

/* ── Skill pills ──────────────────────────── */
.skill-pill {
    display: inline-block;
    background: #1E1E40;
    border: 1px solid #3D3D7A;
    color: #C4B5FD;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    margin: 3px;
}
.skill-pill.matched { border-color: #10B981; color: #6EE7B7; background: #064E3B22; }
.skill-pill.missing { border-color: #EF4444; color: #FCA5A5; background: #7F1D1D22; }
.skill-pill.critical { border-color: #F59E0B; color: #FCD34D; background: #78350F22; }

/* ── Gap cards ────────────────────────────── */
.gap-card {
    background: #1A1A3E;
    border: 1px solid #2D2D5E;
    border-left: 4px solid #7C3AED;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 10px;
}
.gap-card.critical { border-left-color: #EF4444; }
.gap-card.high { border-left-color: #F59E0B; }
.gap-card.medium { border-left-color: #3B82F6; }
.gap-card.low { border-left-color: #10B981; }

/* ── Month cards ──────────────────────────── */
.month-card {
    background: linear-gradient(135deg, #1A1A3E 0%, #16213E 100%);
    border: 1px solid #2D2D5E;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 12px;
}
.month-number {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #7C3AED;
    margin-bottom: 4px;
}
.month-theme {
    font-size: 1.1rem;
    font-weight: 700;
    color: #E2E8F0;
    margin-bottom: 8px;
}

/* ── Course card ──────────────────────────── */
.course-card {
    background: #1A1A3E;
    border: 1px solid #2D2D5E;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 8px;
}
.course-platform {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #7C3AED;
}
.course-title { font-size: 0.95rem; font-weight: 600; color: #E2E8F0; margin: 4px 0; }
.course-meta { font-size: 0.78rem; color: #64748B; }

/* ── Progress bar ─────────────────────────── */
.progress-track {
    background: #1E1E40;
    border-radius: 8px;
    height: 8px;
    overflow: hidden;
    margin: 6px 0;
}
.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #7C3AED, #4F46E5);
    border-radius: 8px;
    transition: width 0.4s ease;
}

/* ── Buttons ──────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #7C3AED, #4F46E5) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* ── Tabs ─────────────────────────────────── */
[data-testid="stTabs"] [role="tab"] {
    color: #94A3B8 !important;
    font-weight: 500;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #C4B5FD !important;
    border-bottom: 2px solid #7C3AED !important;
}

/* ── Expander ─────────────────────────────── */
[data-testid="stExpander"] {
    background: #1A1A3E !important;
    border: 1px solid #2D2D5E !important;
    border-radius: 12px !important;
}

/* ── Inputs ───────────────────────────────── */
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] select {
    background: #1A1A3E !important;
    border: 1px solid #2D2D5E !important;
    color: #E2E8F0 !important;
    border-radius: 8px !important;
}

/* ── Sidebar nav ──────────────────────────── */
.nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    border-radius: 10px;
    cursor: pointer;
    color: #94A3B8;
    font-size: 0.9rem;
    margin: 2px 0;
    transition: all 0.15s;
}
.nav-item:hover { background: #2D2D5E; color: #E2E8F0; }
.nav-item.active { background: linear-gradient(135deg, #7C3AED22, #4F46E522); color: #C4B5FD; border: 1px solid #7C3AED44; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _score_color(score: int) -> str:
    if score >= 90: return "#10B981"
    if score >= 75: return "#3B82F6"
    if score >= 60: return "#F59E0B"
    if score >= 45: return "#EF4444"
    return "#DC2626"


def _priority_emoji(priority: str) -> str:
    return {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(priority.lower(), "⚪")


def metric_card(value, label, sub=""):
    """Render a metric card directly inside a column."""
    sub_html = f'<p style="font-size:0.88rem;color:#C4B5FD;margin:2px 0 0;">{sub}</p>' if sub else ""
    st.markdown(f"""
<div style="background:linear-gradient(135deg,#1A1A3E 0%,#16213E 100%);
            border:1px solid #2D2D5E;border-radius:16px;padding:20px 24px;
            text-align:center;">
  <div style="font-size:2.4rem;font-weight:800;color:#7C3AED;line-height:1;">{value}</div>
  <div style="font-size:0.78rem;color:#94A3B8;margin-top:4px;text-transform:uppercase;
              letter-spacing:0.05em;">{label}</div>
  {sub_html}
</div>
""", unsafe_allow_html=True)


def skill_pills(skills: list, style: str = "") -> str:
    css = f" {style}" if style else ""
    return "".join(f'<span class="skill-pill{css}">{s}</span>' for s in skills)


# ═══════════════════════════════════════════════════════════════════════════════
#  Sidebar Navigation
# ═══════════════════════════════════════════════════════════════════════════════

PAGES = {
    "🏠 Dashboard": "dashboard",
    "📄 New Analysis": "new_analysis",
    "📊 Skill Map": "skill_map",
    "🗺️ Learning Roadmap": "roadmap",
    "📚 Courses": "courses",
    "🏗️ Projects": "projects",
    "💬 Interview Prep": "interview",
    "📈 Progress Tracker": "progress",
    "📁 History": "history",
    "⚙️ Settings": "settings",
}

with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 16px 0 8px;'>
        <div style='font-size:2.2rem;'>🎯</div>
        <div style='font-size:1.1rem; font-weight:800; color:#C4B5FD;'>Skill Gap Agent</div>
        <div style='font-size:0.7rem; color:#4B5563; margin-top:2px;'>AI-Powered Career Intelligence</div>
    </div>
    <hr style='border-color:#2D2D5E; margin:8px 0 16px;'>
    """, unsafe_allow_html=True)

    if "page" not in st.session_state:
        st.session_state.page = "dashboard"

    for label, key in PAGES.items():
        active = "active" if st.session_state.page == key else ""
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.rerun()

    st.markdown("<hr style='border-color:#2D2D5E; margin:16px 0;'>", unsafe_allow_html=True)

    # API Key input
    api_key = st.text_input("🔑 OpenAI API Key", type="password",
                            value=os.environ.get("OPENAI_API_KEY", ""),
                            placeholder="sk-...")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    stats = database.get_stats()
    st.markdown(f"""
    <div style='font-size:0.72rem; color:#4B5563; text-align:center; margin-top:12px;'>
        {stats['profiles']} profiles · {stats['analyses']} analyses · avg {stats['avg_score']}% ready
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  Page Router
# ═══════════════════════════════════════════════════════════════════════════════

page = st.session_state.page


# ╔═══════════════════════════════════════════════════════════════════════════╗
#  DASHBOARD
# ╚═══════════════════════════════════════════════════════════════════════════╝
if page == "dashboard":
    st.markdown("# 🎯 AI Skill Gap Agent")
    st.markdown("<p style='color:#64748B; margin-top:-12px;'>Your personal AI-powered career intelligence platform</p>", unsafe_allow_html=True)

    stats = database.get_stats()
    analyses = database.get_analyses()

    col1, col2, col3, col4 = st.columns(4)
    with col1: metric_card(stats["profiles"], "Profiles Analyzed")
    with col2: metric_card(stats["analyses"], "Gap Analyses Run")
    with col3: metric_card(f"{stats['avg_score']}%", "Average Readiness")
    with col4:
        active = len([a for a in analyses if a["readiness_score"] >= 75])
        metric_card(active, "Ready Candidates", "score ≥ 75%")

    st.markdown("")

    if analyses:
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.markdown('<div class="section-header">📈 Readiness Score History</div>', unsafe_allow_html=True)
            df = pd.DataFrame([{
                "date": a["created_at"][:10],
                "score": a["readiness_score"],
                "id": a["id"],
            } for a in analyses[-20:]])
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["date"], y=df["score"],
                mode="lines+markers",
                fill="tozeroy",
                line=dict(color="#7C3AED", width=2.5),
                fillcolor="rgba(124,58,237,0.12)",
                marker=dict(size=8, color="#7C3AED"),
            ))
            fig.add_hline(y=75, line_dash="dash", line_color="#10B981", annotation_text="Ready (75)", annotation_position="right")
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#E2E8F0", height=280,
                xaxis=dict(showgrid=False, color="#4B5563"),
                yaxis=dict(showgrid=True, gridcolor="#1E2D3D", range=[0, 105], color="#4B5563"),
                margin=dict(l=0, r=10, t=10, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.markdown('<div class="section-header">🕐 Recent Analyses</div>', unsafe_allow_html=True)
            for a in analyses[:5]:
                profile = database.get_profile(a["profile_id"])
                role = profile["target_role"] if profile else "Unknown Role"
                score = a["readiness_score"]
                color = _score_color(score)
                st.markdown(f"""
                <div class="gap-card" style="border-left-color:{color};">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-weight:600; color:#E2E8F0; font-size:0.9rem;">{role}</div>
                            <div style="font-size:0.75rem; color:#64748B;">{a['created_at'][:10]}</div>
                        </div>
                        <div style="font-size:1.4rem; font-weight:800; color:{color};">{score}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Score distribution
        st.markdown('<div class="section-header">📊 Score Distribution</div>', unsafe_allow_html=True)
        scores = [a["readiness_score"] for a in analyses]
        fig2 = go.Figure(go.Histogram(
            x=scores, nbinsx=10,
            marker_color="#7C3AED", opacity=0.8,
        ))
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#E2E8F0", height=200,
            xaxis=dict(title="Readiness Score", showgrid=False, color="#4B5563"),
            yaxis=dict(title="Count", showgrid=True, gridcolor="#1E2D3D", color="#4B5563"),
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.info("👋 Welcome! Start by running a **New Analysis** from the sidebar.")
        st.markdown("""
        <div style='display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:16px;'>
            <div class='gap-card'>
                <div style='font-size:1.5rem;'>📄</div>
                <div style='font-weight:700; color:#E2E8F0; margin:8px 0 4px;'>Upload Resume</div>
                <div style='font-size:0.83rem; color:#64748B;'>PDF or DOCX — GPT-4o extracts your complete skill profile automatically</div>
            </div>
            <div class='gap-card'>
                <div style='font-size:1.5rem;'>🔍</div>
                <div style='font-weight:700; color:#E2E8F0; margin:8px 0 4px;'>AI Gap Analysis</div>
                <div style='font-size:0.83rem; color:#64748B;'>Compare your skills against what top employers need for your target role</div>
            </div>
            <div class='gap-card'>
                <div style='font-size:1.5rem;'>🗺️</div>
                <div style='font-weight:700; color:#E2E8F0; margin:8px 0 4px;'>6-Month Roadmap</div>
                <div style='font-size:0.83rem; color:#64748B;'>Week-by-week learning plan with courses, projects, and milestones</div>
            </div>
            <div class='gap-card'>
                <div style='font-size:1.5rem;'>🎯</div>
                <div style='font-weight:700; color:#E2E8F0; margin:8px 0 4px;'>Readiness Score</div>
                <div style='font-size:0.83rem; color:#64748B;'>Know exactly where you stand and what to fix first</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ╔═══════════════════════════════════════════════════════════════════════════╗
#  NEW ANALYSIS
# ╚═══════════════════════════════════════════════════════════════════════════╝
if page == "new_analysis":
    st.markdown("# 📄 New Skill Gap Analysis")
    st.markdown("<p style='color:#64748B; margin-top:-12px;'>Upload your profile and let AI map your path to your target role</p>", unsafe_allow_html=True)

    with st.form("analysis_form"):
        col1, col2 = st.columns(2)
        with col1:
            target_role = st.text_input("🎯 Target Role *", placeholder="e.g. Senior Machine Learning Engineer")
        with col2:
            industry = st.selectbox("🏭 Industry *", [
                "Technology", "Finance / FinTech", "Healthcare / MedTech",
                "E-Commerce / Retail", "Consulting", "Media / Entertainment",
                "Education / EdTech", "Government / Public Sector", "Manufacturing",
                "Startup / Venture", "Other"
            ])

        st.markdown("---")
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("**📄 Resume** (PDF, DOCX, or TXT)")
            resume_file = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"], label_visibility="collapsed")
        with col4:
            st.markdown("**🔗 LinkedIn Profile** (paste text or URL)")
            linkedin_text = st.text_area("LinkedIn", placeholder="Paste your LinkedIn profile text or 'About' section here...", height=120, label_visibility="collapsed")

        submitted = st.form_submit_button("🚀 Run AI Analysis", use_container_width=True)

    if submitted:
        if not target_role:
            st.error("Please enter a target role.")
            st.stop()
        if not resume_file and not linkedin_text.strip():
            st.error("Please provide a resume or LinkedIn text.")
            st.stop()
        if not os.environ.get("OPENAI_API_KEY"):
            st.error("Please enter your OpenAI API key in the sidebar.")
            st.stop()

        # ── Step 1: Parse input ──
        resume_text = ""
        if resume_file:
            with st.spinner("📄 Parsing resume..."):
                try:
                    resume_text = parser.extract_text(resume_file)
                    st.success(f"Resume parsed: {len(resume_text):,} characters")
                except Exception as e:
                    st.error(f"Resume parsing failed: {e}")
                    st.stop()

        # ── Step 2: AI Profile Extraction ──
        progress_bar = st.progress(0)
        status = st.empty()

        status.markdown("🧠 **Step 1/6** — Extracting your profile with GPT-4o...")
        progress_bar.progress(10)
        try:
            profile = agent.parse_profile(resume_text, linkedin_text, target_role, industry)
        except Exception as e:
            st.error(f"Profile extraction failed: {e}")
            st.stop()

        # ── Step 3: Gap Analysis ──
        status.markdown("🔍 **Step 2/6** — Analyzing skill gaps...")
        progress_bar.progress(25)
        try:
            gap_analysis = agent.analyze_skill_gap(profile, target_role, industry)
        except Exception as e:
            st.error(f"Gap analysis failed: {e}")
            st.stop()

        # ── Step 4: Readiness Score ──
        status.markdown("📊 **Step 3/6** — Calculating readiness score...")
        progress_bar.progress(42)
        try:
            readiness = agent.calculate_readiness(gap_analysis, profile)
        except Exception as e:
            st.error(f"Readiness scoring failed: {e}")
            st.stop()

        # ── Step 5: Roadmap ──
        status.markdown("🗺️ **Step 4/6** — Building your 6-month roadmap...")
        progress_bar.progress(58)
        try:
            roadmap = agent.generate_roadmap(gap_analysis, target_role, industry, readiness)
        except Exception as e:
            st.error(f"Roadmap generation failed: {e}")
            st.stop()

        # ── Step 6: Courses ──
        status.markdown("📚 **Step 5/6** — Curating course recommendations...")
        progress_bar.progress(72)
        try:
            courses = agent.recommend_courses(gap_analysis.get("missing_skills", []), target_role, industry)
        except Exception as e:
            st.error(f"Course recommendations failed: {e}")
            st.stop()

        # ── Step 7: Interview Prep ──
        status.markdown("💬 **Step 6/6** — Preparing interview plan...")
        progress_bar.progress(88)
        try:
            interview = agent.generate_interview_prep(profile, gap_analysis, target_role, industry)
        except Exception as e:
            st.error(f"Interview prep failed: {e}")
            st.stop()

        progress_bar.progress(100)
        status.empty()

        # ── Save to DB ──
        profile_id = database.save_profile(
            target_role=target_role, industry=industry,
            parsed_data=profile, resume_text=resume_text,
            linkedin_text=linkedin_text, name=profile.get("name", ""),
        )
        analysis_id = database.save_analysis(
            profile_id=profile_id,
            readiness_score=readiness.get("overall_score", 0),
            skill_data={"profile": profile},
            gap_data=gap_analysis,
            roadmap_data=roadmap,
            courses_data=courses,
            interview_data=interview,
        )

        # Save progress tasks
        tasks = []
        for month in roadmap.get("monthly_plan", []):
            m = month.get("month", 1)
            start_week = (m - 1) * 4 + 1
            for i, goal in enumerate(month.get("goals", [])[:2]):
                tasks.append({"week": start_week + i, "label": goal})
        if tasks:
            database.save_progress_tasks(analysis_id, tasks)

        # Store in session
        st.session_state.current_analysis_id = analysis_id
        st.session_state.current_profile_id = profile_id

        st.success(f"✅ Analysis complete! Profile saved as #{profile_id}")
        st.balloons()

        # ── Quick summary ──
        score = readiness.get("overall_score", 0)
        grade = readiness.get("grade", "?")
        color = _score_color(score)

        col1, col2, col3 = st.columns([1, 2, 2])
        with col1:
            st.markdown(f"""
            <div style='text-align:center; padding:20px;'>
                <div class='score-badge' style='background:linear-gradient(135deg,{color}99,{color}66);'>
                    {score}<span style='font-size:1.5rem;'>%</span>
                    <div class='score-grade'>{grade} · {readiness.get('grade_label','')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("**✅ Your Strengths**")
            for s in gap_analysis.get("strengths", [])[:4]:
                st.markdown(f"- {s}")

        with col3:
            st.markdown("**🚨 Critical Gaps**")
            for g in gap_analysis.get("critical_gaps", [])[:4]:
                st.markdown(f"- {g}")

        st.info(f"⏱️ **Timeline to ready:** {readiness.get('timeline_to_ready', 'N/A')} · Navigate to other pages to explore your full roadmap!")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("🗺️ View Roadmap", use_container_width=True):
                st.session_state.page = "roadmap"
                st.rerun()
        with col_b:
            if st.button("📊 Skill Map", use_container_width=True):
                st.session_state.page = "skill_map"
                st.rerun()
        with col_c:
            if st.button("💬 Interview Prep", use_container_width=True):
                st.session_state.page = "interview"
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  Helper to load current analysis
# ═══════════════════════════════════════════════════════════════════════════════

def _load_current() -> tuple[dict | None, dict | None]:
    """Load current analysis and profile from session or latest DB record."""
    analysis_id = st.session_state.get("current_analysis_id")
    profile_id = st.session_state.get("current_profile_id")

    if not analysis_id:
        analyses = database.get_analyses()
        if analyses:
            analysis_id = analyses[0]["id"]
            profile_id = analyses[0]["profile_id"]
            st.session_state.current_analysis_id = analysis_id
            st.session_state.current_profile_id = profile_id

    if not analysis_id:
        return None, None

    return database.get_analysis(analysis_id), database.get_profile(profile_id)


def _analysis_selector() -> tuple[dict | None, dict | None]:
    """Show a selector if multiple analyses exist."""
    analyses = database.get_analyses()
    if not analyses:
        st.warning("No analyses found. Run a **New Analysis** first.")
        return None, None

    options = {
        f"#{a['id']} — {database.get_profile(a['profile_id'])['target_role'] if database.get_profile(a['profile_id']) else 'Unknown'} ({a['created_at'][:10]})": a["id"]
        for a in analyses
    }
    chosen_label = st.selectbox("📂 Select Analysis", list(options.keys()), index=0)
    chosen_id = options[chosen_label]
    chosen = database.get_analysis(chosen_id)
    profile = database.get_profile(chosen["profile_id"]) if chosen else None
    return chosen, profile


# ╔═══════════════════════════════════════════════════════════════════════════╗
#  SKILL MAP
# ╚═══════════════════════════════════════════════════════════════════════════╝
if page == "skill_map":
    st.markdown("# 📊 Skill Map & Gap Analysis")

    analysis, profile = _analysis_selector()
    if not analysis:
        st.stop()

    gap = analysis["gap_data"]
    readiness = analysis.get("skill_data", {})
    target_role = profile["target_role"]

    # Readiness Breakdown Radar
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown('<div class="section-header">🕸️ Readiness Radar</div>', unsafe_allow_html=True)
        breakdown = gap.get("readiness_breakdown", {})
        if breakdown:
            cats = list(breakdown.keys())
            vals = list(breakdown.values())
            fig = go.Figure(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=[c.replace("_", " ").title() for c in cats] + [cats[0].replace("_", " ").title()],
                fill="toself",
                fillcolor="rgba(124,58,237,0.2)",
                line=dict(color="#7C3AED", width=2),
                marker=dict(size=6, color="#C4B5FD"),
            ))
            fig.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(range=[0, 100], showticklabels=True, tickfont=dict(color="#64748B"), gridcolor="#2D2D5E"),
                    angularaxis=dict(tickfont=dict(color="#C4B5FD"), gridcolor="#2D2D5E"),
                ),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#E2E8F0", height=360,
                margin=dict(l=60, r=60, t=20, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">📈 Dimension Scores</div>', unsafe_allow_html=True)
        for cat, val in breakdown.items():
            color = _score_color(val)
            st.markdown(f"""
            <div style='margin-bottom:12px;'>
                <div style='display:flex;justify-content:space-between;margin-bottom:4px;'>
                    <span style='font-size:0.85rem;color:#E2E8F0;'>{cat.replace('_',' ').title()}</span>
                    <span style='font-weight:700;color:{color};'>{val}%</span>
                </div>
                <div class='progress-track'>
                    <div class='progress-fill' style='width:{val}%;background:linear-gradient(90deg,{color}88,{color});'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Matched vs Missing skills
    st.markdown('<div class="section-header">✅ Matched Skills</div>', unsafe_allow_html=True)
    matched = gap.get("matched_skills", [])
    if matched:
        pills = "".join(
            f'<span class="skill-pill matched">{s["skill"]} ({s.get("candidate_level",0)}%)</span>'
            for s in matched
        )
        st.markdown(f'<div style="line-height:2;">{pills}</div>', unsafe_allow_html=True)

        # Bar chart for matched skills
        fig3 = go.Figure()
        skills_sorted = sorted(matched, key=lambda x: x.get("candidate_level", 0), reverse=True)[:12]
        fig3.add_trace(go.Bar(
            name="Your Level",
            x=[s["skill"] for s in skills_sorted],
            y=[s.get("candidate_level", 0) for s in skills_sorted],
            marker_color="#7C3AED",
        ))
        fig3.add_trace(go.Bar(
            name="Required Level",
            x=[s["skill"] for s in skills_sorted],
            y=[s.get("required_level", 100) for s in skills_sorted],
            marker_color="#2D2D5E",
        ))
        fig3.update_layout(
            barmode="group",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#E2E8F0", height=260,
            xaxis=dict(showgrid=False, tickangle=-30, color="#64748B"),
            yaxis=dict(showgrid=True, gridcolor="#1E2D3D", range=[0, 110], color="#64748B"),
            legend=dict(font=dict(color="#94A3B8")),
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Missing skills
    st.markdown('<div class="section-header">🚨 Skill Gaps (Prioritized)</div>', unsafe_allow_html=True)
    missing = gap.get("missing_skills", [])
    if missing:
        for s in missing:
            p = s.get("priority", "medium").lower()
            emoji = _priority_emoji(p)
            weeks = s.get("weeks_to_learn", "?")
            difficulty = s.get("difficulty", "medium")
            st.markdown(f"""
            <div class='gap-card {p}'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div>
                        <span style='font-size:0.85rem;font-weight:700;color:#E2E8F0;'>{emoji} {s['skill']}</span>
                        <span style='font-size:0.72rem;color:#64748B;margin-left:8px;'>Difficulty: {difficulty} · ~{weeks} weeks</span>
                    </div>
                    <span class='skill-pill missing'>{p.upper()}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Transferable skills
    transferable = gap.get("transferable_skills", [])
    if transferable:
        st.markdown('<div class="section-header">🔄 Transferable Skills</div>', unsafe_allow_html=True)
        st.markdown(skill_pills(transferable), unsafe_allow_html=True)


# ╔═══════════════════════════════════════════════════════════════════════════╗
#  LEARNING ROADMAP
# ╚═══════════════════════════════════════════════════════════════════════════╝
if page == "roadmap":
    st.markdown("# 🗺️ 6-Month Learning Roadmap")

    analysis, profile = _analysis_selector()
    if not analysis:
        st.stop()

    roadmap = analysis["roadmap_data"]
    monthly = roadmap.get("monthly_plan", [])

    st.markdown(f"""
    <div class='gap-card' style='border-left-color:#7C3AED; margin-bottom:20px;'>
        <div style='font-size:1.1rem;font-weight:700;color:#C4B5FD;'>{roadmap.get('roadmap_title','Your Learning Path')}</div>
        <div style='font-size:0.85rem;color:#64748B;margin-top:4px;'>
            {roadmap.get('total_weeks',26)} weeks · Target: {profile['target_role'] if profile else 'N/A'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Monthly cards
    st.markdown('<div class="section-header">📅 Monthly Plan</div>', unsafe_allow_html=True)

    for i, month in enumerate(monthly):
        m = month.get("month", i + 1)
        with st.expander(f"Month {m}: {month.get('theme', '')}", expanded=(m == 1)):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**⏰ Hours/week:** {month.get('hours_per_week', '?')}")
            with col2:
                st.markdown(f"**📌 Focus areas:** {', '.join(month.get('focus_areas', []))}")
            with col3:
                st.markdown(f"**🏆 Milestone:** {month.get('milestone', '')[:80]}")

            st.markdown("**🎯 Goals this month:**")
            for g in month.get("goals", []):
                st.markdown(f"- {g}")

            if month.get("skills_to_learn"):
                st.markdown("**🔧 Skills to learn:**")
                st.markdown(skill_pills(month["skills_to_learn"]), unsafe_allow_html=True)

    # Weekly schedule
    st.markdown('<div class="section-header">📆 Weekly Schedule Template</div>', unsafe_allow_html=True)
    weekly = roadmap.get("weekly_schedule", {})
    if weekly:
        cols = st.columns(len(weekly))
        day_colors = {"monday": "#7C3AED", "tuesday": "#4F46E5", "wednesday": "#3B82F6",
                      "thursday": "#06B6D4", "friday": "#10B981", "saturday": "#F59E0B", "weekend": "#F59E0B"}
        for i, (day, task) in enumerate(weekly.items()):
            with cols[i % len(cols)]:
                color = day_colors.get(day.lower(), "#7C3AED")
                st.markdown(f"""
                <div style='background:#1A1A3E;border:1px solid {color}44;border-top:3px solid {color};
                            border-radius:10px;padding:12px;text-align:center;height:100%;'>
                    <div style='font-size:0.7rem;font-weight:700;text-transform:uppercase;
                                letter-spacing:0.08em;color:{color};margin-bottom:6px;'>{day}</div>
                    <div style='font-size:0.8rem;color:#CBD5E1;'>{task}</div>
                </div>
                """, unsafe_allow_html=True)

    # Projects in roadmap
    projects = roadmap.get("key_projects", [])
    if projects:
        st.markdown('<div class="section-header">🏗️ Projects Timeline</div>', unsafe_allow_html=True)
        for p in projects:
            month_n = p.get("month", 1)
            diff = p.get("difficulty", "beginner")
            diff_color = {"beginner": "#10B981", "intermediate": "#F59E0B", "advanced": "#EF4444"}.get(diff, "#7C3AED")
            st.markdown(f"""
            <div class='month-card' style='border-left:4px solid {diff_color};'>
                <div style='display:flex;justify-content:space-between;'>
                    <div>
                        <div class='month-number'>Month {month_n} · {diff.upper()} · ~{p.get('estimated_hours','?')} hrs</div>
                        <div class='month-theme'>{p.get('project','')}</div>
                        <div style='font-size:0.83rem;color:#94A3B8;'>{p.get('description','')}</div>
                    </div>
                </div>
                <div style='margin-top:8px;'>
                    {skill_pills(p.get('skills_demonstrated',[]))}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Checkpoints
    checkpoints = roadmap.get("checkpoints", [])
    if checkpoints:
        st.markdown('<div class="section-header">✅ Assessment Checkpoints</div>', unsafe_allow_html=True)
        for c in checkpoints:
            st.markdown(f"""
            <div class='gap-card' style='border-left-color:#3B82F6;'>
                <div style='font-weight:700;color:#93C5FD;'>Week {c.get('week','?')} — {c.get('assessment','')}</div>
                <div style='font-size:0.83rem;color:#64748B;margin-top:4px;'>✔ {c.get('success_criteria','')}</div>
            </div>
            """, unsafe_allow_html=True)


# ╔═══════════════════════════════════════════════════════════════════════════╗
#  COURSES
# ╚═══════════════════════════════════════════════════════════════════════════╝
if page == "courses":
    st.markdown("# 📚 Course Recommendations")

    analysis, profile = _analysis_selector()
    if not analysis:
        st.stop()

    courses = analysis["courses_data"]

    col1, col2, col3 = st.columns(3)
    with col1: metric_card(courses.get("total_resources", 0), "Total Resources")
    with col2: metric_card(len(courses.get("certifications_to_pursue", [])), "Certifications")
    with col3: metric_card(len(courses.get("books_to_read", [])), "Books")

    st.markdown("")

    # Skill courses
    skill_courses = courses.get("skill_courses", [])
    if skill_courses:
        st.markdown('<div class="section-header">🎓 Learning Resources by Skill</div>', unsafe_allow_html=True)
        for sc in skill_courses:
            emoji = _priority_emoji(sc.get("priority", "medium"))
            with st.expander(f"{emoji} {sc['skill']} — {sc.get('priority','').upper()} PRIORITY"):
                for r in sc.get("resources", []):
                    cost = r.get("cost", "")
                    cost_badge = f'<span style="color:#10B981;font-size:0.72rem;">{cost}</span>' if "free" in cost.lower() else f'<span style="color:#F59E0B;font-size:0.72rem;">{cost}</span>'
                    st.markdown(f"""
                    <div class='course-card'>
                        <div class='course-platform'>{r.get('platform','')} · {r.get('type','').upper()} · {r.get('level','')}</div>
                        <div class='course-title'>{r.get('title','')}</div>
                        <div class='course-meta'>
                            ⏱ {r.get('duration','')} &nbsp;|&nbsp; {cost_badge} &nbsp;|&nbsp;
                            <span style='color:#64748B;'>Search: "{r.get('url_hint','')}"</span>
                        </div>
                        <div style='font-size:0.8rem;color:#94A3B8;margin-top:6px;'>💡 {r.get('why_recommended','')}</div>
                    </div>
                    """, unsafe_allow_html=True)

    # Free resources
    free = courses.get("free_resources", [])
    if free:
        st.markdown('<div class="section-header">🆓 Free Resources</div>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, r in enumerate(free):
            with cols[i % 2]:
                st.markdown(f"""
                <div class='course-card'>
                    <div class='course-platform'>{r.get('platform','')} · {r.get('type','').upper()}</div>
                    <div class='course-title'>{r.get('title','')}</div>
                    <div class='course-meta'>Skill: {r.get('skill','')}</div>
                </div>
                """, unsafe_allow_html=True)

    # Certifications
    certs = courses.get("certifications_to_pursue", [])
    if certs:
        st.markdown('<div class="section-header">🏅 Certifications to Pursue</div>', unsafe_allow_html=True)
        for c in certs:
            st.markdown(f"""
            <div class='gap-card' style='border-left-color:#F59E0B;'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div>
                        <div style='font-weight:700;color:#FCD34D;font-size:0.95rem;'>{c.get('name','')}</div>
                        <div style='font-size:0.8rem;color:#64748B;'>by {c.get('provider','')} · Prep: {c.get('prep_time','')} · Est. {c.get('cost_estimate','')}</div>
                        <div style='font-size:0.83rem;color:#94A3B8;margin-top:4px;'>{c.get('relevance','')}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Books
    books = courses.get("books_to_read", [])
    if books:
        st.markdown('<div class="section-header">📖 Books to Read</div>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, b in enumerate(books):
            with cols[i % 2]:
                st.markdown(f"""
                <div class='course-card'>
                    <div class='course-platform'>📚 BOOK</div>
                    <div class='course-title'>{b.get('title','')}</div>
                    <div class='course-meta'>by {b.get('author','')}</div>
                    <div style='font-size:0.8rem;color:#94A3B8;margin-top:4px;'>💡 {b.get('why','')}</div>
                </div>
                """, unsafe_allow_html=True)

    # Communities
    communities = courses.get("communities_to_join", [])
    if communities:
        st.markdown('<div class="section-header">🤝 Communities to Join</div>', unsafe_allow_html=True)
        st.markdown(skill_pills(communities), unsafe_allow_html=True)


# ╔═══════════════════════════════════════════════════════════════════════════╗
#  PROJECTS
# ╚═══════════════════════════════════════════════════════════════════════════╝
if page == "projects":
    st.markdown("# 🏗️ Portfolio Project Suggestions")

    analysis, profile = _analysis_selector()
    if not analysis:
        st.stop()

    if "portfolio_projects" not in analysis.get("roadmap_data", {}):
        # Generate project suggestions if not already stored
        st.info("Generating project suggestions... (this takes ~10 seconds)")
        if os.environ.get("OPENAI_API_KEY"):
            with st.spinner("🤖 AI is crafting project ideas..."):
                try:
                    projects_data = agent.suggest_portfolio_projects(
                        analysis["skill_data"].get("profile", {}),
                        analysis["gap_data"],
                        profile["target_role"],
                        profile["industry"],
                    )
                    st.session_state.projects_data = projects_data
                except Exception as e:
                    st.error(f"Failed to generate projects: {e}")
                    st.stop()
        else:
            st.warning("Enter your OpenAI API key to generate project suggestions.")
            st.stop()
    else:
        projects_data = st.session_state.get("projects_data", {})

    if not projects_data:
        st.warning("Click the button to generate project suggestions.")
        if st.button("🚀 Generate Project Suggestions"):
            st.rerun()
        st.stop()

    st.markdown(f"""
    <div class='gap-card' style='border-left-color:#7C3AED;margin-bottom:16px;'>
        <div style='font-weight:600;color:#C4B5FD;'>📋 Strategy</div>
        <div style='color:#94A3B8;font-size:0.9rem;margin-top:4px;'>{projects_data.get('portfolio_strategy','')}</div>
    </div>
    """, unsafe_allow_html=True)

    # Main projects
    projects = projects_data.get("projects", [])
    if projects:
        st.markdown('<div class="section-header">🏆 Main Portfolio Projects</div>', unsafe_allow_html=True)
        for p in projects:
            diff = p.get("difficulty", "intermediate")
            diff_color = {"beginner": "#10B981", "intermediate": "#F59E0B", "advanced": "#EF4444"}.get(diff, "#7C3AED")
            with st.expander(f"{'🔴' if diff=='advanced' else '🟡' if diff=='intermediate' else '🟢'} {p.get('title','')} — Month {p.get('month_to_build','?')}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Description:** {p.get('description','')}")
                    st.markdown(f"**Wow Factor:** ⭐ {p.get('wow_factor','')}")
                    st.markdown(f"**Deployment:** 🚀 {p.get('deployment','')}")
                    st.markdown(f"**GitHub Structure:** 📁 {p.get('github_structure','')}")
                with col2:
                    st.markdown(f"**Difficulty:** `{diff}`")
                    st.markdown(f"**Hours:** ~{p.get('estimated_hours','?')}")
                    st.markdown(f"**Month:** #{p.get('month_to_build','?')}")

                st.markdown("**Tech Stack:**")
                st.markdown(skill_pills(p.get("tech_stack", [])), unsafe_allow_html=True)
                st.markdown("**Skills Demonstrated:**")
                st.markdown(skill_pills(p.get("skills_demonstrated", []), "matched"), unsafe_allow_html=True)

    # Quick wins
    quick = projects_data.get("quick_wins", [])
    if quick:
        st.markdown('<div class="section-header">⚡ Quick Wins (Start Today)</div>', unsafe_allow_html=True)
        cols = st.columns(min(len(quick), 3))
        for i, qw in enumerate(quick):
            with cols[i % len(cols)]:
                st.markdown(f"""
                <div class='month-card'>
                    <div class='month-number'>⚡ {qw.get('hours','?')} HOURS</div>
                    <div class='month-theme'>{qw.get('title','')}</div>
                    <div style='font-size:0.83rem;color:#94A3B8;'>{qw.get('description','')}</div>
                    <div style='margin-top:8px;'>{skill_pills(qw.get('skills',[]))}</div>
                </div>
                """, unsafe_allow_html=True)

    # Open source
    oss = projects_data.get("open_source_contributions", [])
    if oss:
        st.markdown('<div class="section-header">🌐 Open Source Contributions</div>', unsafe_allow_html=True)
        for o in oss:
            st.markdown(f"""
            <div class='gap-card' style='border-left-color:#10B981;'>
                <div style='font-weight:600;color:#6EE7B7;'>{o.get('project','')}</div>
                <div style='font-size:0.83rem;color:#94A3B8;margin-top:4px;'>{o.get('how_to_contribute','')}</div>
                <div style='font-size:0.78rem;color:#64748B;margin-top:2px;'>Skill gained: {o.get('skill_gained','')}</div>
            </div>
            """, unsafe_allow_html=True)

    # Tips
    tips = projects_data.get("portfolio_presentation_tips", [])
    if tips:
        st.markdown('<div class="section-header">💡 Portfolio Presentation Tips</div>', unsafe_allow_html=True)
        for t in tips:
            st.markdown(f"- {t}")


# ╔═══════════════════════════════════════════════════════════════════════════╗
#  INTERVIEW PREP
# ╚═══════════════════════════════════════════════════════════════════════════╝
if page == "interview":
    st.markdown("# 💬 Interview Preparation Plan")

    analysis, profile = _analysis_selector()
    if not analysis:
        st.stop()

    interview = analysis["interview_data"]
    target_role = profile["target_role"] if profile else "Target Role"

    st.markdown(f"""
    <div class='gap-card' style='border-left-color:#7C3AED;margin-bottom:16px;'>
        <div style='font-weight:600;color:#C4B5FD;'>🎯 Strategy for {target_role}</div>
        <div style='color:#94A3B8;font-size:0.9rem;margin-top:4px;'>{interview.get('prep_overview','')}</div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💻 Technical", "⭐ Behavioral", "❓ Ask Them", "💰 Salary", "📅 7-Day Plan"])

    with tab1:
        tech_qs = interview.get("technical_questions", [])
        for q in tech_qs:
            diff_color = {"easy": "#10B981", "medium": "#F59E0B", "hard": "#EF4444"}.get(q.get("difficulty","medium"), "#7C3AED")
            with st.expander(f"[{q.get('difficulty','?').upper()}] {q.get('question','')}"):
                st.markdown(f"**Category:** `{q.get('category','')}`")
                st.markdown(f"**How to approach:** {q.get('answer_framework','')}")
                if q.get("key_points"):
                    st.markdown("**Key points to cover:**")
                    for kp in q["key_points"]:
                        st.markdown(f"  • {kp}")

    with tab2:
        beh_qs = interview.get("behavioral_questions", [])
        for q in beh_qs:
            with st.expander(f"⭐ {q.get('question','')}"):
                star = q.get("star_framework", {})
                if star:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**S — Situation:** {star.get('situation','')}")
                        st.markdown(f"**T — Task:** {star.get('task','')}")
                    with col2:
                        st.markdown(f"**A — Action:** {star.get('action','')}")
                        st.markdown(f"**R — Result:** {star.get('result','')}")
                if q.get("draw_from"):
                    st.info(f"💡 Draw from: {q['draw_from']}")

    with tab3:
        q_to_ask = interview.get("questions_to_ask", [])
        st.markdown("**Questions to ask your interviewer:**")
        for q in q_to_ask:
            st.markdown(f"""
            <div class='gap-card' style='border-left-color:#3B82F6;'>
                <span style='color:#93C5FD;'>❓ {q}</span>
            </div>
            """, unsafe_allow_html=True)

        red_flags = interview.get("red_flags_to_avoid", [])
        if red_flags:
            st.markdown("**🚩 Red flags to avoid:**")
            for r in red_flags:
                st.markdown(f"- ❌ {r}")

    with tab4:
        salary = interview.get("salary_negotiation", {})
        if salary:
            st.markdown(f"""
            <div class='gap-card' style='border-left-color:#10B981;'>
                <div style='font-size:1.1rem;font-weight:700;color:#6EE7B7;'>💰 Market Range: {salary.get('market_range','Research needed')}</div>
            </div>
            """, unsafe_allow_html=True)
            anchor = salary.get("anchor_statement", "")
            if anchor:
                st.markdown("**Anchor statement template:**")
                st.code(anchor, language=None)
            tips = salary.get("negotiation_tips", [])
            if tips:
                st.markdown("**Negotiation tips:**")
                for t in tips:
                    st.markdown(f"- {t}")

    with tab5:
        week_plan = interview.get("week_prep_plan", [])
        if week_plan:
            for day in week_plan:
                st.markdown(f"""
                <div class='month-card'>
                    <div class='month-number'>DAY {day.get('day','?')}</div>
                    <div class='month-theme'>{day.get('focus','')}</div>
                    {''.join(f'<div style="font-size:0.82rem;color:#94A3B8;margin-top:4px;">• {t}</div>' for t in day.get('tasks',[]))}
                </div>
                """, unsafe_allow_html=True)

    boosters = interview.get("confidence_boosters", [])
    if boosters:
        st.markdown('<div class="section-header">🚀 Your Competitive Advantages</div>', unsafe_allow_html=True)
        for b in boosters:
            st.markdown(f"""
            <div class='gap-card' style='border-left-color:#10B981;'>
                <span style='color:#6EE7B7;'>✨ {b}</span>
            </div>
            """, unsafe_allow_html=True)


# ╔═══════════════════════════════════════════════════════════════════════════╗
#  PROGRESS TRACKER
# ╚═══════════════════════════════════════════════════════════════════════════╝
if page == "progress":
    st.markdown("# 📈 Progress Tracker")

    analysis, profile = _analysis_selector()
    if not analysis:
        st.stop()

    tasks = database.get_progress(analysis["id"])

    if not tasks:
        st.info("No progress tasks found. Run a new analysis to generate your weekly task list.")
        st.stop()

    total = len(tasks)
    done = sum(1 for t in tasks if t["completed"])
    pct = int(done / total * 100) if total else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1: metric_card(total, "Total Tasks")
    with col2: metric_card(done, "Completed")
    with col3: metric_card(f"{pct}%", "Progress")
    with col4: metric_card(total - done, "Remaining")

    st.markdown("")
    st.markdown(f"""
    <div class='progress-track' style='height:16px;border-radius:8px;'>
        <div class='progress-fill' style='width:{pct}%;height:16px;'></div>
    </div>
    <div style='font-size:0.8rem;color:#64748B;margin-top:4px;'>{pct}% complete — {total-done} tasks remaining</div>
    """, unsafe_allow_html=True)

    # Group by week
    by_week: dict[int, list] = {}
    for t in tasks:
        w = t["week_number"]
        by_week.setdefault(w, []).append(t)

    for week, week_tasks in sorted(by_week.items()):
        week_done = sum(1 for t in week_tasks if t["completed"])
        week_pct = int(week_done / len(week_tasks) * 100)
        color = "#10B981" if week_pct == 100 else "#7C3AED" if week_pct > 0 else "#2D2D5E"
        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:12px;margin:16px 0 8px;'>
            <div style='font-size:0.85rem;font-weight:700;color:{color};'>Week {week}</div>
            <div style='font-size:0.75rem;color:#64748B;'>{week_done}/{len(week_tasks)} done</div>
        </div>
        """, unsafe_allow_html=True)

        for t in week_tasks:
            col_check, col_label = st.columns([1, 12])
            with col_check:
                checked = st.checkbox("", value=bool(t["completed"]), key=f"task_{t['id']}")
                if checked != bool(t["completed"]):
                    database.toggle_task(t["id"], checked)
                    st.rerun()
            with col_label:
                style = "text-decoration:line-through;color:#4B5563;" if t["completed"] else "color:#E2E8F0;"
                st.markdown(f"<span style='{style}'>{t['task_label']}</span>", unsafe_allow_html=True)

    # Progress chart over weeks
    if by_week:
        st.markdown('<div class="section-header">📊 Completion by Week</div>', unsafe_allow_html=True)
        week_data = []
        for w, wt in sorted(by_week.items()):
            week_data.append({"Week": f"W{w}", "Completed": sum(1 for t in wt if t["completed"]), "Total": len(wt)})
        df_w = pd.DataFrame(week_data)
        fig = px.bar(df_w, x="Week", y=["Completed", "Total"],
                     barmode="overlay",
                     color_discrete_map={"Completed": "#7C3AED", "Total": "#1E1E40"})
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#E2E8F0", height=220,
            xaxis=dict(showgrid=False, color="#4B5563"),
            yaxis=dict(showgrid=True, gridcolor="#1E2D3D", color="#4B5563"),
            legend=dict(font=dict(color="#94A3B8")),
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)


# ╔═══════════════════════════════════════════════════════════════════════════╗
#  HISTORY
# ╚═══════════════════════════════════════════════════════════════════════════╝
if page == "history":
    st.markdown("# 📁 Analysis History")

    analyses = database.get_analyses()

    if not analyses:
        st.info("No analyses saved yet. Run your first analysis!")
        st.stop()

    for a in analyses:
        profile = database.get_profile(a["profile_id"])
        score = a["readiness_score"]
        color = _score_color(score)
        target = profile["target_role"] if profile else "Unknown"
        industry = profile["industry"] if profile else "Unknown"
        name = profile.get("name", "Candidate") if profile else "Candidate"

        col1, col2, col3 = st.columns([5, 2, 2])
        with col1:
            st.markdown(f"""
            <div class='gap-card' style='border-left-color:{color};'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div>
                        <div style='font-weight:700;color:#E2E8F0;'>{name} → {target}</div>
                        <div style='font-size:0.78rem;color:#64748B;'>{industry} · {a['created_at'][:10]} · ID #{a['id']}</div>
                        <div style='margin-top:6px;'>
                            {skill_pills(a['gap_data'].get('critical_gaps',[])[:3], 'missing')}
                        </div>
                    </div>
                    <div style='font-size:2rem;font-weight:800;color:{color};margin-left:16px;'>{score}%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if st.button("📂 Load", key=f"load_{a['id']}", use_container_width=True):
                st.session_state.current_analysis_id = a["id"]
                st.session_state.current_profile_id = a["profile_id"]
                st.session_state.page = "skill_map"
                st.rerun()

        with col3:
            if profile and st.button("📄 Export PDF", key=f"pdf_{a['id']}", use_container_width=True):
                with st.spinner("Generating PDF..."):
                    try:
                        readiness_data = agent.calculate_readiness(a["gap_data"], profile["parsed_data"])
                        pdf_bytes = exporter.export_full_report(
                            profile=profile["parsed_data"],
                            readiness=readiness_data,
                            gap_analysis=a["gap_data"],
                            roadmap=a["roadmap_data"],
                            courses=a["courses_data"],
                            target_role=profile["target_role"],
                            industry=profile["industry"],
                        )
                        st.download_button(
                            "⬇️ Download PDF",
                            data=pdf_bytes,
                            file_name=f"skill_gap_report_{a['id']}.pdf",
                            mime="application/pdf",
                            key=f"dl_{a['id']}",
                        )
                    except Exception as e:
                        st.error(f"PDF export failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#  Footer
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<hr style='border-color:#1E1E40;margin-top:40px;'>
<div style='text-align:center;font-size:0.72rem;color:#374151;padding-bottom:16px;'>
    🎯 AI Skill Gap Agent · Powered by GPT-4o · Built with Streamlit
</div>
""", unsafe_allow_html=True)

# ╔═══════════════════════════════════════════════════════════════════════════╗
#  SETTINGS PAGE (appended)
# ╚═══════════════════════════════════════════════════════════════════════════╝

if page == "settings":
    st.markdown("# ⚙️ Settings")
    st.markdown("<p style='color:#64748B;margin-top:-12px;'>Configure your AI Skill Gap Agent</p>", unsafe_allow_html=True)

    # ── API Configuration ──────────────────────────────────────────────────
    st.markdown("""
<div style="background:linear-gradient(135deg,#1A1A3E,#16213E);border:1px solid #2D2D5E;
            border-radius:16px;padding:24px;margin-bottom:20px;">
  <div style="font-size:1.1rem;font-weight:700;color:#C4B5FD;margin-bottom:4px;">🔑 API Configuration</div>
  <div style="font-size:0.82rem;color:#64748B;">Your API key is used only for on-demand AI calls and never stored in the database.</div>
</div>
""", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        new_key = st.text_input(
            "OpenAI API Key",
            value=os.environ.get("OPENAI_API_KEY", ""),
            type="password",
            placeholder="sk-proj-...",
            help="Get your key at platform.openai.com/api-keys",
        )
    with col2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("💾 Save Key", use_container_width=True):
            if new_key.startswith("sk-"):
                os.environ["OPENAI_API_KEY"] = new_key
                st.session_state.api_key_saved = True
                st.success("✅ API key saved for this session!")
            else:
                st.error("Key must start with sk-")

    if os.environ.get("OPENAI_API_KEY"):
        key = os.environ["OPENAI_API_KEY"]
        masked = key[:8] + "..." + key[-4:]
        st.markdown(f"""
<div style="background:#064E3B22;border:1px solid #10B98144;border-radius:10px;
            padding:10px 16px;font-size:0.83rem;color:#6EE7B7;margin-top:8px;">
  ✅ Active key: <code style="color:#A7F3D0;">{masked}</code>
</div>
""", unsafe_allow_html=True)

        # Test API key
        if st.button("🧪 Test API Connection"):
            with st.spinner("Testing connection..."):
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
                    client.models.list()
                    st.success("✅ Connection successful! GPT-4o is ready.")
                except Exception as e:
                    st.error(f"❌ Connection failed: {e}")

    st.markdown("---")

    # ── Model Settings ─────────────────────────────────────────────────────
    st.markdown("""
<div style="font-size:1.05rem;font-weight:700;color:#E2E8F0;margin:20px 0 12px;">
  🤖 Model Settings
</div>
""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        model = st.selectbox(
            "AI Model",
            ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            index=0,
            help="gpt-4o gives best results. gpt-4o-mini is faster and cheaper.",
        )
        if "ai_model" not in st.session_state:
            st.session_state.ai_model = "gpt-4o"
        if model != st.session_state.ai_model:
            st.session_state.ai_model = model

    with col2:
        temperature = st.slider(
            "Response Creativity",
            min_value=0.0, max_value=1.0, value=0.3, step=0.05,
            help="Lower = more consistent/structured. Higher = more creative recommendations.",
        )
        st.session_state.ai_temperature = temperature

    cost_map = {"gpt-4o": "$0.05–0.08", "gpt-4o-mini": "$0.005–0.01", "gpt-4-turbo": "$0.06–0.10"}
    st.markdown(f"""
<div style="background:#1A1A3E;border:1px solid #2D2D5E;border-radius:10px;
            padding:12px 16px;font-size:0.82rem;color:#94A3B8;margin-top:8px;">
  💰 Estimated cost per full analysis with <strong style="color:#C4B5FD;">{model}</strong>: 
  <strong style="color:#7C3AED;">{cost_map.get(model, "~$0.05")}</strong>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Analysis Defaults ──────────────────────────────────────────────────
    st.markdown("""
<div style="font-size:1.05rem;font-weight:700;color:#E2E8F0;margin:20px 0 12px;">
  📋 Analysis Defaults
</div>
""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        default_industry = st.selectbox(
            "Default Industry",
            ["Technology", "Finance / FinTech", "Healthcare / MedTech",
             "E-Commerce / Retail", "Consulting", "Media / Entertainment",
             "Education / EdTech", "Government / Public Sector", "Manufacturing",
             "Startup / Venture", "Other"],
            index=0,
        )
        st.session_state.default_industry = default_industry

    with col2:
        roadmap_months = st.selectbox(
            "Roadmap Duration",
            ["3 months", "6 months", "9 months", "12 months"],
            index=1,
            help="Length of the learning roadmap generated by AI.",
        )
        st.session_state.roadmap_months = roadmap_months

    st.markdown("---")

    # ── Database Management ────────────────────────────────────────────────
    st.markdown("""
<div style="font-size:1.05rem;font-weight:700;color:#E2E8F0;margin:20px 0 12px;">
  🗄️ Database Management
</div>
""", unsafe_allow_html=True)

    stats = database.get_stats()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card(stats["profiles"], "Profiles")
    with col2:
        metric_card(stats["analyses"], "Analyses")
    with col3:
        metric_card(f"{stats['avg_score']}%", "Avg Score")
    with col4:
        from pathlib import Path
        db_path = Path("data/skill_gap.db")
        db_size = f"{db_path.stat().st_size / 1024:.1f} KB" if db_path.exists() else "0 KB"
        metric_card(db_size, "DB Size")

    st.markdown("")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📤 Export All Data (JSON)", use_container_width=True):
            import json as json_mod
            all_data = {
                "profiles": database.get_profiles(),
                "analyses": database.get_analyses(),
                "exported_at": datetime.now().isoformat(),
            }
            st.download_button(
                "⬇️ Download backup.json",
                data=json_mod.dumps(all_data, indent=2, default=str),
                file_name="skill_gap_backup.json",
                mime="application/json",
            )
    with col_b:
        with st.expander("⚠️ Danger Zone — Clear Database"):
            st.warning("This will permanently delete ALL profiles, analyses, and progress data.")
            confirm = st.text_input("Type DELETE to confirm", key="delete_confirm")
            if st.button("🗑️ Clear All Data", type="primary", key="clear_db"):
                if confirm == "DELETE":
                    import sqlite3
                    conn = sqlite3.connect("data/skill_gap.db")
                    conn.executescript("DELETE FROM progress; DELETE FROM analyses; DELETE FROM profiles;")
                    conn.commit()
                    conn.close()
                    st.success("✅ Database cleared.")
                    st.rerun()
                else:
                    st.error("Type DELETE to confirm.")

    st.markdown("---")

    # ── About ──────────────────────────────────────────────────────────────
    st.markdown("""
<div style="font-size:1.05rem;font-weight:700;color:#E2E8F0;margin:20px 0 12px;">
  ℹ️ About
</div>
<div style="background:linear-gradient(135deg,#1A1A3E,#16213E);border:1px solid #2D2D5E;
            border-radius:16px;padding:24px;display:grid;grid-template-columns:1fr 1fr;gap:16px;">
  <div>
    <div style="font-size:0.78rem;color:#7C3AED;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">Application</div>
    <div style="color:#E2E8F0;font-weight:600;margin-top:4px;">AI Skill Gap Agent</div>
    <div style="color:#64748B;font-size:0.82rem;">v1.0.0</div>
  </div>
  <div>
    <div style="font-size:0.78rem;color:#7C3AED;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">AI Engine</div>
    <div style="color:#E2E8F0;font-weight:600;margin-top:4px;">OpenAI GPT-4o</div>
    <div style="color:#64748B;font-size:0.82rem;">7 specialized prompts</div>
  </div>
  <div>
    <div style="font-size:0.78rem;color:#7C3AED;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">Frontend</div>
    <div style="color:#E2E8F0;font-weight:600;margin-top:4px;">Streamlit + Plotly</div>
    <div style="color:#64748B;font-size:0.82rem;">9 interactive pages</div>
  </div>
  <div>
    <div style="font-size:0.78rem;color:#7C3AED;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">Storage</div>
    <div style="color:#E2E8F0;font-weight:600;margin-top:4px;">SQLite (local)</div>
    <div style="color:#64748B;font-size:0.82rem;">3 tables, zero config</div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div style="margin-top:16px;padding:14px 18px;background:#1A1A3E;border:1px solid #2D2D5E;
            border-radius:12px;font-size:0.82rem;color:#64748B;">
  💡 <strong style="color:#C4B5FD;">Tip:</strong> Set your OpenAI API key as an environment variable 
  <code>OPENAI_API_KEY=sk-...</code> or in <code>.streamlit/secrets.toml</code> to avoid re-entering it each session.
</div>
""", unsafe_allow_html=True)
