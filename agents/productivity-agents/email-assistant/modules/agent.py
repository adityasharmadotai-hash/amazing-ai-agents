"""
modules/agent.py
----------------
All AI-powered email intelligence features via OpenAI GPT-4o.
Each function is prompt-engineered for a specific email task.
"""
from __future__ import annotations
import hashlib
import json
import os
import re

from openai import OpenAI


def get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            pass
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set.")
    return OpenAI(api_key=api_key)


def _call(system: str, user: str, max_tokens: int = 1000, temperature: float = 0.3) -> str:
    client = get_client()
    resp = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content.strip()


def _safe_json(text: str) -> dict | list:
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        m = re.search(r"[\[{].*[\]}]", cleaned, re.DOTALL)
        if m:
            return json.loads(m.group())
        return {}


def _cache_key(prefix: str, content: str) -> str:
    return f"{prefix}:{hashlib.md5(content.encode()).hexdigest()[:12]}"


# ── 1. Email Summarization ────────────────────────────────────────────────────

def summarize_email(subject: str, sender: str, body: str, use_cache: bool = True) -> str:
    """Generate a 2–3 sentence summary of an email."""
    from modules import database
    key = _cache_key("summary", subject + body[:200])
    if use_cache:
        cached = database.get_cached(key)
        if cached:
            return cached

    system = """You are an expert email summarizer. 
Read the email and return a clear 2-3 sentence summary.
Focus on: what is being asked/said, any action required, and deadline if mentioned.
Be concise and use plain language. No bullet points."""

    user = f"From: {sender}\nSubject: {subject}\n\nBody:\n{body[:2000]}"
    result = _call(system, user, max_tokens=200)
    database.set_cache(key, result)
    return result


# ── 2. Smart Reply Suggestions ────────────────────────────────────────────────

def suggest_replies(subject: str, sender: str, body: str, context: str = "") -> list[dict]:
    """
    Generate 3 smart reply options with different tones.
    Returns list of {tone, subject, body}.
    """
    system = """You are an expert email assistant.
Generate exactly 3 reply options for the given email.
Return ONLY valid JSON array (no markdown) with this structure:
[
  {"tone": "Professional", "subject": "Re: ...", "body": "Full reply text here"},
  {"tone": "Friendly", "subject": "Re: ...", "body": "Full reply text here"},
  {"tone": "Brief", "subject": "Re: ...", "body": "One or two sentence reply"}
]
Make each reply natural, complete, and ready to send."""

    user = f"""Original email:
From: {sender}
Subject: {subject}
Body: {body[:1500]}
{f'Context: {context}' if context else ''}"""

    raw = _call(system, user, max_tokens=800)
    result = _safe_json(raw)
    if isinstance(result, list):
        return result
    return [{"tone": "Professional", "subject": f"Re: {subject}", "body": raw}]


# ── 3. Priority Classification ────────────────────────────────────────────────

def classify_priority(subject: str, sender: str, snippet: str) -> dict:
    """
    Classify email priority and detect if it needs a response.
    Returns {priority, needs_reply, reason, urgency_score}.
    """
    system = """You are an email priority classifier.
Analyze the email and return ONLY valid JSON with:
{
  "priority": "critical|high|medium|low",
  "needs_reply": true/false,
  "reason": "one sentence explanation",
  "urgency_score": 1-10,
  "category": "meeting|task|info|social|marketing|support|other",
  "suggested_action": "reply|forward|archive|schedule|follow-up|none"
}
Critical = immediate action needed (deadline today, urgent request from boss/client).
High = needs reply within 24h. Medium = this week. Low = informational or can wait."""

    user = f"From: {sender}\nSubject: {subject}\nSnippet: {snippet}"
    raw = _call(system, user, max_tokens=200, temperature=0.1)
    result = _safe_json(raw)
    if not isinstance(result, dict):
        return {"priority": "medium", "needs_reply": False, "reason": "Could not classify",
                "urgency_score": 5, "category": "other", "suggested_action": "none"}
    return result


# ── 4. Detect Unanswered Important Emails ────────────────────────────────────

def detect_unanswered(emails: list[dict]) -> list[dict]:
    """
    From a list of emails, identify which ones need a response and haven't been replied to.
    Returns the emails with priority data added.
    """
    flagged = []
    for email in emails[:30]:  # Process up to 30 at once
        if not email.get("is_unread"):
            continue
        classification = classify_priority(
            email.get("subject", ""),
            email.get("sender", email.get("from", "")),
            email.get("snippet", ""),
        )
        if classification.get("needs_reply") and classification.get("urgency_score", 0) >= 6:
            email["_priority_data"] = classification
            flagged.append(email)
    # Sort by urgency
    flagged.sort(key=lambda x: x.get("_priority_data", {}).get("urgency_score", 0), reverse=True)
    return flagged


# ── 5. Meeting Preparation Summary ───────────────────────────────────────────

def prepare_meeting_brief(
    event_title: str,
    attendees: list[str],
    event_description: str,
    related_emails: list[dict],
) -> dict:
    """
    Generate a meeting prep brief with context, talking points, and background.
    """
    email_context = "\n\n".join([
        f"Email from {e.get('sender', e.get('from', ''))} ({e.get('date_str', e.get('date', ''))}):\n"
        f"Subject: {e.get('subject', '')}\n{e.get('snippet', '')}"
        for e in related_emails[:5]
    ])

    system = """You are an executive assistant preparing a meeting brief.
Return ONLY valid JSON with:
{
  "executive_summary": "2-3 sentences on what this meeting is about and why it matters",
  "key_context": ["context point 1", "context point 2"],
  "talking_points": ["talking point 1", "talking point 2", "talking point 3"],
  "open_items": ["open question/item 1", "open question/item 2"],
  "attendee_notes": [{"person": "email", "role": "inferred role", "note": "relationship/context"}],
  "suggested_outcomes": ["what to achieve 1", "what to achieve 2"],
  "prep_checklist": ["prep task 1", "prep task 2"]
}"""

    user = f"""Meeting: {event_title}
Attendees: {', '.join(attendees)}
Description: {event_description or 'None provided'}

Related emails:
{email_context or 'No related emails found'}"""

    raw = _call(system, user, max_tokens=1000, temperature=0.4)
    result = _safe_json(raw)
    if not isinstance(result, dict):
        return {"executive_summary": raw, "talking_points": [], "key_context": []}
    return result


# ── 6. Conversation Context ───────────────────────────────────────────────────

def generate_conversation_context(thread: list[dict]) -> dict:
    """
    Analyze a full email thread and generate context summary.
    """
    thread_text = "\n\n---\n\n".join([
        f"From: {m.get('sender', m.get('from', ''))}\nDate: {m.get('date_str', m.get('date', ''))}\n"
        f"Subject: {m.get('subject', '')}\n{m.get('body', m.get('snippet', ''))[:500]}"
        for m in thread[:10]
    ])

    system = """You are an email context analyzer.
Analyze the email thread and return ONLY valid JSON with:
{
  "thread_summary": "What this conversation is about (2-3 sentences)",
  "current_status": "Where things stand right now",
  "key_decisions": ["decision 1", "decision 2"],
  "action_items": [{"who": "person", "what": "task", "when": "deadline or 'unspecified'"}],
  "tone": "collaborative|tense|formal|casual|urgent",
  "relationship": "manager|colleague|client|vendor|unknown",
  "next_step": "What should happen next"
}"""

    raw = _call(system, thread_text, max_tokens=600, temperature=0.2)
    result = _safe_json(raw)
    if not isinstance(result, dict):
        return {"thread_summary": raw, "action_items": [], "current_status": "Unknown"}
    return result


# ── 7. Contact Summary ────────────────────────────────────────────────────────

def summarize_contact(email_addr: str, name: str, emails: list[dict]) -> str:
    """Generate an AI summary of a contact based on email history."""
    sample_emails = "\n\n".join([
        f"Subject: {e.get('subject','')}\n{e.get('snippet','')}"
        for e in emails[:8]
    ])

    system = """You are analyzing email history to build a contact profile.
Write a concise 3-4 sentence professional summary of this person based on their emails.
Include: their apparent role/relationship, topics they discuss, communication style, and any key context.
Be factual and professional."""

    user = f"Contact: {name} <{email_addr}>\n\nEmail history:\n{sample_emails}"
    return _call(system, user, max_tokens=200, temperature=0.3)


# ── 8. AI Email Drafting ──────────────────────────────────────────────────────

def draft_email(
    to: str,
    purpose: str,
    tone: str = "professional",
    context: str = "",
    original_email: str = "",
) -> dict:
    """
    Draft a complete email based on purpose and tone.
    Returns {subject, body}.
    """
    system = f"""You are an expert email writer. 
Write a {tone} email based on the purpose provided.
Return ONLY valid JSON with:
{{"subject": "Email subject line", "body": "Complete email body"}}
The email should be complete, natural, and ready to send.
Tone guidelines:
- professional: formal, clear, respectful
- friendly: warm, personable, approachable
- assertive: direct, confident, clear about expectations
- brief: concise, bullet points OK, under 100 words"""

    user = f"""To: {to}
Purpose: {purpose}
Tone: {tone}
{f'Context/Background: {context}' if context else ''}
{f'Replying to: {original_email[:500]}' if original_email else ''}"""

    raw = _call(system, user, max_tokens=600, temperature=0.5)
    result = _safe_json(raw)
    if not isinstance(result, dict) or "body" not in result:
        return {"subject": f"Re: {purpose[:50]}", "body": raw}
    return result


# ── 9. Tone Rewriting ─────────────────────────────────────────────────────────

def rewrite_tone(original: str, target_tone: str) -> str:
    """Rewrite an email body in a different tone."""
    tones = {
        "professional": "formal, polished, business-appropriate",
        "friendly": "warm, approachable, personable",
        "assertive": "confident, direct, clear expectations",
        "diplomatic": "tactful, considerate, constructive",
        "brief": "very concise, under 80 words, to the point",
        "formal": "highly formal, deferential, structured",
    }
    desc = tones.get(target_tone, target_tone)

    system = f"""Rewrite the email body in a {target_tone} tone ({desc}).
Keep the same meaning and key information.
Return only the rewritten email body text, no subject line, no extra explanation."""

    return _call(system, f"Original:\n{original}", max_tokens=500, temperature=0.4)


# ── 10. Priority Inbox Ranking ────────────────────────────────────────────────

def rank_priority_inbox(emails: list[dict]) -> list[dict]:
    """
    Batch-rank up to 20 emails and return them sorted by priority.
    """
    if not emails:
        return []

    email_list = "\n".join([
        f"{i+1}. From: {e.get('sender', e.get('from', ''))} | "
        f"Subject: {e.get('subject', '')} | "
        f"Snippet: {e.get('snippet', '')[:100]}"
        for i, e in enumerate(emails[:20])
    ])

    system = """You are an email priority ranker.
Rank these emails by importance. Return ONLY a JSON array of objects:
[{"index": 1, "priority": "critical|high|medium|low", "urgency": 1-10, "category": "meeting|task|info|social|marketing|other"}]
Index matches the numbered list. Be accurate about urgency."""

    raw = _call(system, email_list, max_tokens=800, temperature=0.1)
    rankings = _safe_json(raw)

    if not isinstance(rankings, list):
        return emails

    rank_map = {r["index"]: r for r in rankings}
    result = []
    for i, email in enumerate(emails[:20], 1):
        rank = rank_map.get(i, {})
        email["_ai_priority"] = rank.get("priority", "medium")
        email["_ai_urgency"] = rank.get("urgency", 5)
        email["_ai_category"] = rank.get("category", "other")
        result.append(email)

    result.sort(key=lambda x: x.get("_ai_urgency", 0), reverse=True)
    return result


# ── 11. Follow-up Detection ───────────────────────────────────────────────────

def detect_follow_up_needed(emails: list[dict]) -> list[dict]:
    """Identify sent emails that likely need a follow-up."""
    candidates = []
    for email in emails:
        snippet = email.get("snippet", "").lower()
        subject = email.get("subject", "").lower()
        # Heuristic: emails with action words that haven't been replied to
        action_words = ["please", "can you", "could you", "let me know", "waiting",
                        "following up", "as discussed", "per our conversation"]
        if any(w in snippet or w in subject for w in action_words):
            candidates.append(email)
    return candidates[:10]


# ── 12. Inbox Analytics Summary ──────────────────────────────────────────────

def generate_inbox_insight(stats: dict, top_senders: list, email_samples: list) -> str:
    """Generate a natural language inbox health summary."""
    system = """You are a personal productivity coach analyzing someone's inbox.
Write a concise 3-4 sentence insight about their email patterns and a key recommendation.
Be specific, actionable, and encouraging."""

    user = f"""Inbox stats:
- Total emails cached: {stats.get('total', 0)}
- Unread: {stats.get('unread', 0)}
- Important: {stats.get('important', 0)}
- Pending follow-ups: {stats.get('follow_ups', 0)}
- Active reminders: {stats.get('reminders', 0)}

Top senders: {', '.join(top_senders[:5])}

Sample recent subjects: {', '.join([e.get('subject','') for e in email_samples[:5]])}"""

    return _call(system, user, max_tokens=200, temperature=0.5)
