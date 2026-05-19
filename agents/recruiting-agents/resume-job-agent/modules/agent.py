"""
agent.py — All OpenAI API calls for resume analysis
"""

import json
import os
import re

import streamlit as st
from openai import OpenAI


def get_client():
    """Return an OpenAI client using the key from secrets or env."""
    api_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    return OpenAI(api_key=api_key)


def _call_openai(system: str, user: str, max_tokens: int = 2000) -> str:
    """Low-level OpenAI call — returns text content."""
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content


def _safe_json(text: str) -> dict | list:
    """Strip markdown fences and parse JSON safely."""
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    return json.loads(cleaned)


# ─────────────────────────────────────────────
# 1. Resume Parsing
# ─────────────────────────────────────────────

def parse_resume(resume_text: str) -> dict:
    """
    Parse a resume and return structured data:
    name, email, phone, skills, experience, education, projects, summary
    """
    system = """You are an expert resume parser. Extract structured information
from the resume text provided.

Return ONLY valid JSON (no markdown, no extra text) with these exact keys:
{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "phone number or empty string",
  "location": "City, State or empty string",
  "summary": "2-3 sentence professional summary",
  "skills": ["skill1", "skill2", ...],
  "experience": [
    {
      "title": "Job Title",
      "company": "Company Name",
      "duration": "Jan 2022 - Present",
      "years": 2.5,
      "highlights": ["achievement 1", "achievement 2"]
    }
  ],
  "education": [
    {
      "degree": "B.S. Computer Science",
      "institution": "University Name",
      "year": "2020",
      "gpa": "3.8 or empty string"
    }
  ],
  "projects": [
    {
      "name": "Project Name",
      "description": "What it does",
      "technologies": ["tech1", "tech2"]
    }
  ],
  "certifications": ["cert1", "cert2"],
  "total_experience_years": 5.0
}"""

    user = f"Parse this resume:\n\n{resume_text}"
    try:
        raw = _call_openai(system, user, max_tokens=2500)
        return _safe_json(raw)
    except Exception as e:
        return {"error": str(e), "raw": resume_text[:500]}


# ─────────────────────────────────────────────
# 2. Job Matching
# ─────────────────────────────────────────────

def match_job(resume_data: dict, job_description: str) -> dict:
    """
    Compare resume against a job description.
    Returns match score, missing skills, strengths, and recommendations.
    """
    system = """You are an expert HR consultant and talent acquisition specialist.
Analyze the candidate's resume against the job description and provide a detailed match analysis.

Return ONLY valid JSON with these exact keys:
{
  "match_score": 78,
  "grade": "B+",
  "summary": "2-3 sentence overall assessment",
  "matching_skills": ["skill1", "skill2"],
  "missing_skills": ["skill1", "skill2"],
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "gaps": ["gap 1", "gap 2"],
  "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"],
  "experience_match": "Strong / Moderate / Weak",
  "education_match": "Strong / Moderate / Weak",
  "cultural_fit_notes": "Brief notes on cultural/soft skill fit"
}"""

    user = f"""
RESUME DATA:
{json.dumps(resume_data, indent=2)}

JOB DESCRIPTION:
{job_description}

Analyze the match comprehensively.
"""
    try:
        raw = _call_openai(system, user, max_tokens=2000)
        return _safe_json(raw)
    except Exception as e:
        return {"error": str(e), "match_score": 0}


# ─────────────────────────────────────────────
# 3. ATS Checker
# ─────────────────────────────────────────────

def check_ats(resume_text: str, job_description: str = "") -> dict:
    """
    Analyze resume for ATS compatibility.
    Returns score, keyword analysis, formatting issues, and optimizations.
    """
    system = """You are an ATS (Applicant Tracking System) expert. 
Analyze the resume for ATS compatibility and keyword optimization.

Return ONLY valid JSON with these exact keys:
{
  "ats_score": 72,
  "grade": "C+",
  "summary": "Overall ATS compatibility summary",
  "formatting_issues": ["issue 1", "issue 2"],
  "keyword_density": {
    "found_keywords": ["keyword1", "keyword2"],
    "missing_keywords": ["keyword1", "keyword2"],
    "keyword_score": 65
  },
  "section_analysis": {
    "contact_info": {"score": 90, "notes": "Good"},
    "work_experience": {"score": 75, "notes": "Needs quantified achievements"},
    "skills_section": {"score": 80, "notes": "Well formatted"},
    "education": {"score": 85, "notes": "Clear and complete"}
  },
  "optimization_suggestions": [
    {"priority": "High", "suggestion": "Add a dedicated Skills section"},
    {"priority": "Medium", "suggestion": "Use standard section headers"},
    {"priority": "Low", "suggestion": "Remove tables and graphics"}
  ],
  "readability_score": 78,
  "length_assessment": "Appropriate / Too Long / Too Short"
}"""

    user = f"""
RESUME TEXT:
{resume_text}

JOB DESCRIPTION (for keyword matching):
{job_description if job_description else "Not provided — do general ATS analysis"}
"""
    try:
        raw = _call_openai(system, user, max_tokens=2000)
        return _safe_json(raw)
    except Exception as e:
        return {"error": str(e), "ats_score": 0}


# ─────────────────────────────────────────────
# 4. Cover Letter Generator
# ─────────────────────────────────────────────

def generate_cover_letter(resume_data: dict, job_description: str, company_name: str = "", tone: str = "Professional") -> str:
    """Generate a tailored cover letter."""
    system = f"""You are an expert career coach and professional writer.
Write a compelling, personalized cover letter in a {tone} tone.
The letter should be 3-4 paragraphs, around 300-400 words.
Do NOT use placeholder brackets like [Your Name] — use the actual data provided.
Format it as a proper business letter."""

    user = f"""
CANDIDATE INFORMATION:
{json.dumps(resume_data, indent=2)}

JOB DESCRIPTION:
{job_description}

COMPANY NAME: {company_name if company_name else "the company"}

Write a tailored cover letter that:
1. Opens with a strong hook referencing the specific role
2. Highlights 2-3 most relevant experiences/achievements
3. Shows genuine interest in the company
4. Closes with a clear call to action
"""
    return _call_openai(system, user, max_tokens=1000)


# ─────────────────────────────────────────────
# 5. Interview Question Generator
# ─────────────────────────────────────────────

def generate_interview_questions(resume_data: dict, job_description: str, num_questions: int = 10) -> dict:
    """Generate likely interview questions with suggested answers."""
    system = """You are an expert interviewer and career coach.
Generate realistic interview questions based on the candidate's background and the job requirements.

Return ONLY valid JSON with this structure:
{
  "behavioral": [
    {
      "question": "Tell me about a time when...",
      "why_asked": "Tests leadership and problem-solving",
      "suggested_answer_framework": "Use STAR method: Situation - [hint], Task - [hint], Action - [hint], Result - [hint]"
    }
  ],
  "technical": [
    {
      "question": "How would you approach...",
      "why_asked": "Tests technical knowledge of X",
      "key_points_to_cover": ["point 1", "point 2"]
    }
  ],
  "situational": [
    {
      "question": "If you were faced with...",
      "why_asked": "Tests decision making",
      "ideal_response_direction": "Brief guidance"
    }
  ],
  "culture_fit": [
    {
      "question": "Why do you want to work here?",
      "why_asked": "Tests motivation and research",
      "tips": "Brief tip"
    }
  ]
}"""

    user = f"""
CANDIDATE RESUME:
{json.dumps(resume_data, indent=2)}

JOB DESCRIPTION:
{job_description}

Generate {num_questions} total interview questions spread across the categories (behavioral, technical, situational, culture_fit).
Make them specific to this candidate's background and this role.
"""
    try:
        raw = _call_openai(system, user, max_tokens=3000)
        return _safe_json(raw)
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────
# 6. Resume Improvement Suggestions
# ─────────────────────────────────────────────

def get_resume_improvements(resume_data: dict, resume_text: str) -> dict:
    """Get AI-powered suggestions to improve the resume."""
    system = """You are a professional resume coach with 15+ years of experience.
Provide specific, actionable improvements for this resume.

Return ONLY valid JSON:
{
  "overall_score": 72,
  "impact_level": "Medium",
  "quick_wins": ["Quick improvement 1", "Quick improvement 2", "Quick improvement 3"],
  "section_improvements": {
    "summary": "Specific suggestion for summary section",
    "experience": "Specific suggestion for experience section",
    "skills": "Specific suggestion for skills section",
    "education": "Specific suggestion for education section"
  },
  "bullet_point_rewrites": [
    {
      "original": "Managed team projects",
      "improved": "Led cross-functional team of 8 engineers to deliver 3 projects 15% ahead of schedule"
    }
  ],
  "missing_sections": ["Certifications", "Projects"],
  "power_words_to_add": ["Spearheaded", "Orchestrated", "Accelerated"],
  "achievement_gaps": "Bullets lack quantified results — add numbers, percentages, dollar amounts"
}"""

    user = f"""
RESUME DATA:
{json.dumps(resume_data, indent=2)}

ORIGINAL TEXT:
{resume_text[:3000]}

Provide detailed improvement suggestions.
"""
    try:
        raw = _call_openai(system, user, max_tokens=2000)
        return _safe_json(raw)
    except Exception as e:
        return {"error": str(e), "overall_score": 0}
