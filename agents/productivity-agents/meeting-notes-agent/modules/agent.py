"""
agent.py — OpenAI GPT-4o calls for meeting analysis.
All functions return structured data from transcript text.
"""

import json
import os
import re

import streamlit as st
from openai import OpenAI


def get_client() -> OpenAI:
    try:
        key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    except Exception:
        key = os.environ.get("OPENAI_API_KEY", "")
    return OpenAI(api_key=key)


def is_configured() -> bool:
    try:
        key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    except Exception:
        key = os.environ.get("OPENAI_API_KEY", "")
    return bool(key)


def _call_gpt(system: str, user: str, max_tokens: int = 2000) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content.strip()


def _safe_json(text: str) -> dict | list:
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    return json.loads(cleaned)


def _truncate(transcript: str, max_chars: int = 14000) -> str:
    if len(transcript) <= max_chars:
        return transcript
    half = max_chars // 2
    return transcript[:half] + "\n\n[...middle section omitted for length...]\n\n" + transcript[-half:]


# ─────────────────────────────────────────────
# 1. Full Analysis (all sections at once)
# ─────────────────────────────────────────────

def analyze_meeting(transcript: str, meeting_title: str = "", attendees: str = "") -> dict:
    """
    Run full meeting analysis in one GPT-4o call.
    Returns structured dict with all sections.
    """
    system = """You are an expert meeting analyst and executive assistant. 
Analyze meeting transcripts and extract structured, actionable information.
Return ONLY valid JSON — no markdown fences, no preamble."""

    user = f"""Analyze this meeting transcript and return a comprehensive JSON analysis.

MEETING TITLE: {meeting_title or "Untitled Meeting"}
ATTENDEES MENTIONED: {attendees or "Extract from transcript"}

Return this exact JSON structure:
{{
  "title": "Meeting title (concise, descriptive)",
  "date_mentioned": "any date mentioned in transcript, or empty string",
  "attendees": ["Person A", "Person B"],
  "duration_estimate": "estimated meeting length (e.g. 45 minutes)",
  "summary": "3-5 sentence executive summary of what was discussed and decided",
  "key_topics": ["Topic 1", "Topic 2", "Topic 3"],
  "decisions": [
    {{
      "decision": "What was decided",
      "context": "Why this decision was made",
      "owner": "Person responsible (or 'Team')"
    }}
  ],
  "action_items": [
    {{
      "task": "Specific task description",
      "owner": "Person responsible",
      "deadline": "Deadline mentioned or 'TBD'",
      "priority": "High / Medium / Low"
    }}
  ],
  "tasks_by_person": {{
    "Person A": ["task 1", "task 2"],
    "Person B": ["task 1"]
  }},
  "follow_up_questions": ["Question 1", "Question 2"],
  "risks_blockers": ["Risk or blocker 1", "Risk or blocker 2"],
  "sentiment": "Positive / Neutral / Mixed / Tense",
  "meeting_effectiveness": "High / Medium / Low",
  "next_meeting_suggested": "any mention of next meeting, or empty string"
}}

TRANSCRIPT:
{_truncate(transcript)}

Return ONLY the JSON object."""

    try:
        raw = _call_gpt(system, user, max_tokens=3000)
        return _safe_json(raw)
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────
# 2. Follow-up Email
# ─────────────────────────────────────────────

def generate_follow_up_email(analysis: dict, transcript: str) -> str:
    """Generate a professional follow-up email from the meeting analysis."""
    system = """You are an expert business communicator who writes clear, 
professional follow-up emails after meetings."""

    attendees = ", ".join(analysis.get("attendees", ["Team"]))
    action_items = analysis.get("action_items", [])
    decisions = analysis.get("decisions", [])

    ai_text = "\n".join(
        f"- {ai['task']} (Owner: {ai['owner']}, Due: {ai['deadline']})"
        for ai in action_items
    ) or "None recorded"

    dec_text = "\n".join(
        f"- {d['decision']}" for d in decisions
    ) or "None recorded"

    user = f"""Write a professional follow-up email for this meeting.

MEETING: {analysis.get('title', 'Meeting')}
ATTENDEES: {attendees}
SUMMARY: {analysis.get('summary', '')}

ACTION ITEMS:
{ai_text}

DECISIONS:
{dec_text}

Write a clean, professional email that:
1. Thanks attendees
2. Recaps key decisions (2-3 bullet points max)
3. Lists action items with owners and deadlines
4. States next steps
5. Has a warm but professional sign-off

Use plain text only — no markdown headers or formatting symbols.
Format it as a real email with Subject line, greeting, body, and sign-off."""

    try:
        return _call_gpt(system, user, max_tokens=1000)
    except Exception as e:
        return f"Error generating email: {e}"


# ─────────────────────────────────────────────
# 3. Search / Q&A on transcript
# ─────────────────────────────────────────────

def ask_about_meeting(transcript: str, question: str, analysis: dict) -> str:
    """Answer a specific question about the meeting."""
    system = """You are a helpful meeting assistant. Answer questions about 
meeting transcripts accurately and concisely. If the answer isn't in the 
transcript, say so clearly."""

    user = f"""MEETING: {analysis.get('title', 'Meeting')}
SUMMARY: {analysis.get('summary', '')}

FULL TRANSCRIPT:
{_truncate(transcript, 12000)}

QUESTION: {question}

Answer clearly and concisely. Quote the transcript directly when relevant."""

    try:
        return _call_gpt(system, user, max_tokens=800)
    except Exception as e:
        return f"Error: {e}"


# ─────────────────────────────────────────────
# 4. Quick title extraction
# ─────────────────────────────────────────────

def extract_meeting_title(transcript: str) -> str:
    """Extract a concise meeting title from the transcript."""
    system = "You extract concise meeting titles from transcripts. Return only the title, nothing else."
    user = f"Extract a concise meeting title (max 8 words) from:\n\n{transcript[:2000]}"
    try:
        return _call_gpt(system, user, max_tokens=50)
    except Exception:
        words = transcript.split()
        return " ".join(words[:5]) + "..."
