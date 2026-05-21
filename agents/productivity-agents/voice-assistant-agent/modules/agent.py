"""
agent.py — Conversational AI with intent detection and task execution.
Uses GPT-4o with a system prompt that enables smart routing to tools.
"""

import json
import os
import re
from datetime import datetime

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


# ─────────────────────────────────────────────
# System prompt
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are ARIA — an Advanced Real-time Intelligent Assistant — a helpful, 
warm, and highly capable AI voice assistant built by Aditya Sharma.

PERSONALITY:
- Warm, conversational, and concise
- Smart and proactive — anticipate what the user needs
- Adapt tone: friendly for casual chat, professional for tasks
- Keep responses clear and spoken-word friendly (no markdown tables or complex formatting)

CAPABILITIES:
- Answer questions on any topic
- Help draft notes, emails, messages, and documents
- Create, list, update, and manage tasks/reminders
- Perform calendar lookups and event suggestions
- Summarise information clearly
- Provide smart suggestions and follow-ups

INTENT DETECTION:
At the START of every response, output a JSON intent block on its own line:
[INTENT: {"type": "INTENT_TYPE", "data": {...}}]

INTENT TYPES:
- CHAT — general conversation or questions
- CREATE_NOTE — user wants to create/save a note → data: {"title": "...", "content": "..."}
- CREATE_TASK — user wants to add a task → data: {"task": "...", "deadline": "...", "priority": "Medium"}
- CREATE_REMINDER — user wants a reminder → data: {"reminder": "...", "time": "..."}
- SEARCH_WEB — user wants info that needs searching → data: {"query": "..."}
- CALENDAR_EVENT — user wants to schedule something → data: {"title": "...", "date": "...", "time": "..."}
- UPDATE_TASK — user is updating/completing a task → data: {"task_ref": "...", "status": "done/pending"}
- SUMMARISE — user wants a summary → data: {"topic": "..."}

After the intent line, write your spoken response naturally.
Keep responses under 150 words unless detail is explicitly requested.
Today's date is: """ + datetime.now().strftime("%A, %B %d, %Y") + """."""


def _safe_json(text: str):
    try:
        cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
        return json.loads(cleaned)
    except Exception:
        return {}


def _parse_intent(text: str) -> tuple[dict, str]:
    """Extract intent JSON from response and return (intent, clean_text)."""
    pattern = r"\[INTENT:\s*(\{.*?\})\s*\]"
    match = re.search(pattern, text, re.DOTALL)
    intent = {}
    clean = text
    if match:
        try:
            intent = json.loads(match.group(1))
        except Exception:
            intent = {"type": "CHAT"}
        clean = text[:match.start()].strip() + text[match.end():].strip()
    return intent, clean.strip()


# ─────────────────────────────────────────────
# Main chat function
# ─────────────────────────────────────────────

def chat(
    user_message: str,
    conversation_history: list,
    context: str = "",
) -> dict:
    """
    Send a message and get a response with intent detection.
    Returns: {
        "response": "text",
        "intent": {"type": "CHAT", "data": {...}},
        "raw": "full response"
    }
    """
    client = get_client()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if context:
        messages.append({
            "role": "system",
            "content": f"ADDITIONAL CONTEXT:\n{context}"
        })

    # Include last 10 turns of history
    for msg in conversation_history[-10:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"],
        })

    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=600,
            temperature=0.75,
        )
        raw = response.choices[0].message.content.strip()
        intent, clean = _parse_intent(raw)

        if not intent:
            intent = {"type": "CHAT", "data": {}}

        return {
            "response": clean,
            "intent": intent,
            "raw": raw,
        }

    except Exception as e:
        err = str(e)
        if "authentication" in err.lower():
            return {"response": "I can't respond right now — the API key seems invalid. Please check Settings.", "intent": {"type": "CHAT"}, "raw": ""}
        if "rate_limit" in err.lower():
            return {"response": "I'm being rate limited. Please wait a moment and try again.", "intent": {"type": "CHAT"}, "raw": ""}
        return {"response": f"Something went wrong: {err}", "intent": {"type": "CHAT"}, "raw": ""}


# ─────────────────────────────────────────────
# Quick note generator
# ─────────────────────────────────────────────

def generate_note_from_text(text: str, style: str = "bullet") -> str:
    """Generate a structured note from raw text."""
    client = get_client()
    styles = {
        "bullet": "bullet point list with clear headings",
        "summary": "concise paragraph summary",
        "action": "action items and next steps",
        "formal": "formal document format",
    }
    fmt = styles.get(style, "bullet point list")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=500,
            messages=[
                {"role": "system", "content": f"You create clean, well-structured notes in {fmt} format. No markdown headers with #."},
                {"role": "user", "content": f"Create a note from this text:\n\n{text}"},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Could not generate note: {e}"


def web_search_answer(query: str) -> str:
    """
    Use GPT-4o's knowledge to answer a search-type query.
    (For live web search, integrate Serper/Tavily API.)
    """
    client = get_client()
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=400,
            messages=[
                {"role": "system", "content": "Answer the user's question clearly and concisely using your knowledge. If you're unsure, say so. Keep it under 150 words."},
                {"role": "user", "content": query},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Search failed: {e}"
