"""
modules/agent.py
----------------
All AI-powered features via OpenAI GPT-4o.
Each function has a carefully engineered prompt and returns a typed dict.
"""

from __future__ import annotations
import json
import os
import re

from openai import OpenAI


# ── Client ────────────────────────────────────────────────────────────────────

def get_client() -> OpenAI:
    """Return an OpenAI client, reading the key from env or Streamlit secrets."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            pass
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Set it in .env or .streamlit/secrets.toml"
        )
    return OpenAI(api_key=api_key)


def _call_gpt(system: str, user: str, max_tokens: int = 3000) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=max_tokens,
        temperature=0.3,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content


def _safe_json(text: str) -> dict:
    """Strip markdown fences and parse JSON safely."""
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Attempt to extract first JSON object
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise


# ── 1. Resume + LinkedIn Parsing ──────────────────────────────────────────────

def parse_profile(
    resume_text: str = "",
    linkedin_text: str = "",
    target_role: str = "",
    industry: str = "",
) -> dict:
    """
    Extract structured candidate data from resume and/or LinkedIn text.
    Returns skills, experience, education, projects, and a candidate summary.
    """
    system = """You are an expert career analyst and talent profiler.
Extract a comprehensive structured profile from the provided resume and/or LinkedIn text.
Return ONLY valid JSON (no markdown, no extra text) with these exact keys:
{
  "name": "candidate full name or 'Unknown'",
  "current_title": "current or most recent job title",
  "years_experience": 3,
  "summary": "2-3 sentence professional summary",
  "technical_skills": ["skill1", "skill2"],
  "soft_skills": ["skill1", "skill2"],
  "tools_technologies": ["tool1", "tool2"],
  "education": [{"degree": "...", "field": "...", "institution": "...", "year": "..."}],
  "experience": [{"title": "...", "company": "...", "duration": "...", "highlights": ["..."]}],
  "certifications": ["cert1", "cert2"],
  "projects": [{"name": "...", "description": "...", "technologies": ["..."]}],
  "languages": ["English"],
  "notable_achievements": ["achievement1", "achievement2"]
}
Be thorough. Infer skills from context if not explicitly listed."""

    user = f"""Target Role: {target_role}
Industry: {industry}

RESUME:
{resume_text or '(not provided)'}

LINKEDIN:
{linkedin_text or '(not provided)'}"""

    raw = _call_gpt(system, user, max_tokens=2000)
    return _safe_json(raw)


# ── 2. Skill Gap Analysis ─────────────────────────────────────────────────────

def analyze_skill_gap(
    profile: dict,
    target_role: str,
    industry: str,
) -> dict:
    """
    Compare candidate's current skills against target role requirements.
    Returns matched skills, missing skills, and priority gaps.
    """
    system = """You are a senior talent acquisition specialist and career strategist.
Analyze the candidate's profile against the target role and industry standards.
Return ONLY valid JSON with these exact keys:
{
  "target_role_requirements": {
    "must_have_skills": ["skill1", "skill2"],
    "nice_to_have_skills": ["skill1", "skill2"],
    "experience_level": "mid-level",
    "key_competencies": ["competency1", "competency2"]
  },
  "matched_skills": [
    {"skill": "Python", "candidate_level": 80, "required_level": 90, "gap": 10}
  ],
  "missing_skills": [
    {"skill": "Kubernetes", "priority": "critical", "difficulty": "medium", "weeks_to_learn": 8}
  ],
  "transferable_skills": ["skill1", "skill2"],
  "strengths": ["strength1", "strength2"],
  "critical_gaps": ["gap1", "gap2"],
  "overall_fit_percentage": 65,
  "readiness_breakdown": {
    "technical": 70,
    "experience": 60,
    "soft_skills": 80,
    "education": 75,
    "certifications": 50
  }
}
Priority must be one of: critical, high, medium, low.
Difficulty must be one of: easy, medium, hard."""

    user = f"""Target Role: {target_role}
Industry: {industry}

Candidate Profile:
{json.dumps(profile, indent=2)}"""

    raw = _call_gpt(system, user, max_tokens=2500)
    return _safe_json(raw)


# ── 3. Career Readiness Score ─────────────────────────────────────────────────

def calculate_readiness(gap_analysis: dict, profile: dict) -> dict:
    """
    Generate a holistic career readiness score with detailed breakdown.
    """
    system = """You are a career development expert.
Based on the gap analysis and profile, calculate a comprehensive readiness score.
Return ONLY valid JSON with these exact keys:
{
  "overall_score": 72,
  "grade": "B",
  "grade_label": "Strong Candidate",
  "score_breakdown": {
    "technical_skills": {"score": 70, "weight": 0.35, "weighted": 24.5},
    "work_experience": {"score": 75, "weight": 0.25, "weighted": 18.75},
    "soft_skills": {"score": 80, "weight": 0.15, "weighted": 12},
    "education": {"score": 65, "weight": 0.10, "weighted": 6.5},
    "certifications": {"score": 50, "weight": 0.10, "weighted": 5},
    "portfolio_projects": {"score": 60, "weight": 0.05, "weighted": 3}
  },
  "timeline_to_ready": "4-6 months",
  "key_bottlenecks": ["bottleneck1", "bottleneck2"],
  "quick_wins": ["win1", "win2"],
  "competitive_advantage": "What makes this candidate stand out",
  "market_positioning": "How they compare to typical applicants"
}
Grade scale: A (90-100, Ready Now), B (75-89, Almost Ready), C (60-74, Needs Work), D (45-59, Significant Gaps), F (<45, Major Rebuild)"""

    user = f"""Gap Analysis:
{json.dumps(gap_analysis, indent=2)}

Candidate Profile Summary:
Name: {profile.get('name')}
Current Title: {profile.get('current_title')}
Years Experience: {profile.get('years_experience')}
Technical Skills: {profile.get('technical_skills', [])}"""

    raw = _call_gpt(system, user, max_tokens=1500)
    return _safe_json(raw)


# ── 4. Learning Roadmap ───────────────────────────────────────────────────────

def generate_roadmap(
    gap_analysis: dict,
    target_role: str,
    industry: str,
    readiness: dict,
) -> dict:
    """
    Generate a detailed 6-month learning roadmap with monthly milestones.
    """
    system = """You are a curriculum designer and career coach specializing in tech roles.
Create a detailed, actionable 6-month learning roadmap.
Return ONLY valid JSON with these exact keys:
{
  "roadmap_title": "Your Path to [Role]",
  "total_weeks": 26,
  "monthly_plan": [
    {
      "month": 1,
      "theme": "Foundation Building",
      "focus_areas": ["area1", "area2"],
      "goals": ["goal1", "goal2"],
      "skills_to_learn": ["skill1", "skill2"],
      "hours_per_week": 10,
      "milestone": "Description of what should be achieved"
    }
  ],
  "weekly_schedule": {
    "monday": "Concept study (1-2 hrs)",
    "tuesday": "Hands-on practice (1-2 hrs)",
    "wednesday": "Project work (1-2 hrs)",
    "thursday": "Review & exercises (1 hr)",
    "friday": "Community/networking (30 min)",
    "weekend": "Project building (2-3 hrs)"
  },
  "key_projects": [
    {
      "month": 1,
      "project": "Project name",
      "description": "What to build",
      "skills_demonstrated": ["skill1"],
      "difficulty": "beginner",
      "estimated_hours": 20
    }
  ],
  "checkpoints": [
    {"week": 4, "assessment": "What to measure", "success_criteria": "How to know you passed"}
  ]
}
Make it realistic, specific, and tailored to the exact gaps identified."""

    user = f"""Target Role: {target_role}
Industry: {industry}
Timeline to Ready: {readiness.get('timeline_to_ready', '6 months')}
Overall Score: {readiness.get('overall_score', 60)}

Critical Gaps:
{json.dumps(gap_analysis.get('missing_skills', []), indent=2)}

Current Strengths:
{json.dumps(gap_analysis.get('strengths', []), indent=2)}"""

    raw = _call_gpt(system, user, max_tokens=3000)
    return _safe_json(raw)


# ── 5. Course Recommendations ─────────────────────────────────────────────────

def recommend_courses(
    missing_skills: list,
    target_role: str,
    industry: str,
) -> dict:
    """
    Recommend specific courses, books, and resources for each skill gap.
    """
    system = """You are an e-learning expert and career development advisor.
Recommend the best learning resources for the identified skill gaps.
Return ONLY valid JSON with these exact keys:
{
  "total_resources": 15,
  "skill_courses": [
    {
      "skill": "Skill name",
      "priority": "critical",
      "resources": [
        {
          "title": "Course/Book title",
          "platform": "Coursera/Udemy/YouTube/Book",
          "type": "course",
          "duration": "20 hours",
          "cost": "Free/$49",
          "level": "beginner",
          "url_hint": "search term to find it",
          "why_recommended": "Brief reason"
        }
      ]
    }
  ],
  "free_resources": [
    {"title": "Resource", "type": "documentation/youtube/blog", "platform": "...", "skill": "..."}
  ],
  "certifications_to_pursue": [
    {
      "name": "Certification name",
      "provider": "AWS/Google/Microsoft",
      "relevance": "Why it matters for this role",
      "prep_time": "3 months",
      "cost_estimate": "$300"
    }
  ],
  "communities_to_join": ["community1", "community2"],
  "books_to_read": [
    {"title": "Book title", "author": "Author", "why": "Why this book"}
  ]
}"""

    user = f"""Target Role: {target_role}
Industry: {industry}

Skills to Learn (prioritized):
{json.dumps(missing_skills, indent=2)}"""

    raw = _call_gpt(system, user, max_tokens=2500)
    return _safe_json(raw)


# ── 6. Interview Preparation Plan ────────────────────────────────────────────

def generate_interview_prep(
    profile: dict,
    gap_analysis: dict,
    target_role: str,
    industry: str,
) -> dict:
    """
    Generate a tailored interview preparation plan with questions and strategies.
    """
    system = """You are an expert interview coach who has helped thousands of candidates land their dream jobs.
Create a comprehensive interview preparation plan.
Return ONLY valid JSON with these exact keys:
{
  "prep_overview": "High-level interview strategy for this role",
  "technical_questions": [
    {
      "question": "Question text",
      "difficulty": "medium",
      "category": "algorithms/system_design/etc",
      "answer_framework": "How to approach this question",
      "key_points": ["point1", "point2"]
    }
  ],
  "behavioral_questions": [
    {
      "question": "Question text",
      "star_framework": {
        "situation": "Describe the context",
        "task": "Your responsibility",
        "action": "What you did",
        "result": "Measurable outcome"
      },
      "draw_from": "Which experience to reference"
    }
  ],
  "questions_to_ask": ["Question for interviewer 1", "Question 2"],
  "red_flags_to_avoid": ["red flag 1", "red flag 2"],
  "salary_negotiation": {
    "market_range": "$X - $Y",
    "negotiation_tips": ["tip1", "tip2"],
    "anchor_statement": "Template statement to use"
  },
  "week_prep_plan": [
    {"day": 1, "focus": "Research the company", "tasks": ["task1", "task2"]},
    {"day": 2, "focus": "Technical review", "tasks": ["task1"]}
  ],
  "confidence_boosters": ["Your strength 1 to highlight", "strength 2"]
}"""

    user = f"""Target Role: {target_role}
Industry: {industry}

Candidate Strengths: {json.dumps(profile.get('notable_achievements', []))}
Technical Skills: {json.dumps(profile.get('technical_skills', []))}
Missing Skills: {json.dumps([s['skill'] for s in gap_analysis.get('missing_skills', [])])}
Overall Fit: {gap_analysis.get('overall_fit_percentage', 65)}%"""

    raw = _call_gpt(system, user, max_tokens=2500)
    return _safe_json(raw)


# ── 7. Project Suggestions ────────────────────────────────────────────────────

def suggest_portfolio_projects(
    profile: dict,
    gap_analysis: dict,
    target_role: str,
    industry: str,
) -> dict:
    """
    Suggest portfolio projects to bridge skill gaps and impress recruiters.
    """
    system = """You are a senior engineering mentor and portfolio coach.
Suggest portfolio projects that will maximally impress recruiters for this role.
Return ONLY valid JSON with these exact keys:
{
  "portfolio_strategy": "Overall strategy for the portfolio",
  "projects": [
    {
      "title": "Project name",
      "description": "What it does and why it matters",
      "skills_demonstrated": ["skill1", "skill2"],
      "difficulty": "intermediate",
      "estimated_hours": 40,
      "month_to_build": 2,
      "tech_stack": ["tech1", "tech2"],
      "wow_factor": "What makes this impressive",
      "github_structure": "How to organize the repo",
      "deployment": "How/where to deploy it"
    }
  ],
  "quick_wins": [
    {
      "title": "Quick project",
      "description": "Simple but impressive",
      "hours": 8,
      "skills": ["skill"]
    }
  ],
  "open_source_contributions": [
    {"project": "Project name", "how_to_contribute": "...", "skill_gained": "..."}
  ],
  "portfolio_presentation_tips": ["tip1", "tip2"]
}
Suggest 4-6 main projects and 3 quick wins."""

    user = f"""Target Role: {target_role}
Industry: {industry}

Current Skills: {json.dumps(profile.get('technical_skills', []) + profile.get('tools_technologies', []))}
Skills to Demonstrate: {json.dumps([s['skill'] for s in gap_analysis.get('missing_skills', [])][:6])}
Existing Projects: {json.dumps([p.get('name') for p in profile.get('projects', [])])}"""

    raw = _call_gpt(system, user, max_tokens=2000)
    return _safe_json(raw)
