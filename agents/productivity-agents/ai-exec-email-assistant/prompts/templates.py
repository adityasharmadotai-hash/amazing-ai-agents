"""Centralised prompt templates for the AI layer.

Keeping prompts in one module makes them easy to tune and version.
Each template is a plain string with `{placeholders}` filled by `.format`.
"""
from __future__ import annotations

SYSTEM_ASSISTANT = (
    "You are an elite executive email assistant. You are concise, precise, and "
    "action-oriented. You never invent facts that are not present in the provided "
    "email content. When unsure, you say so. You write in clear business English."
)

SYSTEM_DRAFTER = (
    "You are an expert email writer for a busy executive. You produce polished, "
    "ready-to-send emails. You match the requested tone exactly, keep the message "
    "focused, and avoid filler. Return only the email body unless a subject is asked for."
)

# --- Summarisation ---
INBOX_SUMMARY = """Summarise the following {count} emails for a busy executive.

For the overall inbox, produce:
1. A 2-3 sentence high-level summary.
2. The 3-5 most important items (with sender + one-line reason).
3. Anything time-sensitive.

Emails:
{emails}

Respond in clear Markdown."""

DAILY_DIGEST = """Create a daily email digest from these emails.

Group into: "Needs Action", "FYI / Informational", "Can Ignore".
Under each, list sender — subject — one-line summary.
Keep it scannable. Use Markdown.

Emails:
{emails}"""

WEEKLY_SUMMARY = """Create a weekly email summary from these emails.

Include:
- Key themes of the week
- Important threads and their status
- Outstanding items carried into next week
- A short "executive takeaway" paragraph

Emails:
{emails}

Use Markdown with headings."""

# --- Classification (returns strict JSON) ---
CLASSIFY_EMAIL = """Analyse this single email and return STRICT JSON only, no prose.

Schema:
{{
  "priority_score": <float 0-1, how urgent/important for an executive>,
  "is_important": <bool>,
  "needs_followup": <bool>,
  "reason": "<short reason, max 12 words>",
  "category": "<one of: action, decision, fyi, scheduling, sales, personal, spam>"
}}

Email:
From: {sender}
Subject: {subject}
Body:
{body}"""

# --- Follow-up ---
SUGGEST_FOLLOWUP = """The executive needs to follow up on this email thread.
Draft a brief, polite follow-up email body. Reference context appropriately,
be {tone} in tone, and include a clear next step or question.

Original email:
From: {sender}
Subject: {subject}
Body:
{body}

Return only the follow-up email body."""

# --- Drafting ---
GENERATE_DRAFT = """Write an email for the following request.
Tone: {tone}
Context / instructions: {instructions}

Return JSON only:
{{"subject": "<subject line>", "body": "<email body>"}}"""

REPLY_WITH_CONTEXT = """Write a reply to the most recent email in this thread.
Use the prior conversation for context. Match the executive's voice.
Tone: {tone}
Additional instructions: {instructions}

Thread (oldest to newest):
{thread}

Return only the reply body. Do not include quoted history."""

REWRITE_TONE = """Rewrite the following email in a {tone} tone.
Preserve all facts and intent. Do not add new commitments.

Original:
{original}

Return only the rewritten email body."""

TONE_GUIDE = {
    "professional": "formal, courteous, business-appropriate",
    "friendly": "warm, approachable, lightly personable but still professional",
    "executive": "crisp, confident, decisive, minimal words, leadership voice",
    "short": "extremely concise, 1-3 sentences, no pleasantries beyond a greeting",
}

# --- Daily executive briefing ---
EXECUTIVE_BRIEFING = """You are preparing the morning executive briefing for {owner}.
Today is {today}.

INPUTS
Important emails:
{important_emails}

Emails needing follow-up:
{followup_emails}

Produce a polished Markdown briefing with these sections:
# Executive Briefing — {today}
## 🔴 Top Priorities (ranked, max 5)
## 📧 Important Emails
## ↩️ Follow-ups Needed
## ✅ Suggested Focus for the Day

Be specific and actionable. No fluff."""

# --- Voice intent routing (returns strict JSON) ---
VOICE_INTENT = """You route a spoken command to one assistant action.
Return STRICT JSON only.

Available intents:
- read_inbox
- read_unread
- search_emails (params: {{"query": "<gmail search query>"}})
- summarize_inbox
- followups
- draft_reply (params: {{"target": "<who/what>"}})
- daily_briefing
- unknown

Schema:
{{"intent": "<one of above>", "params": {{}}, "spoken_response": "<one short sentence to say back to the user>"}}

User said: "{transcript}"
"""
