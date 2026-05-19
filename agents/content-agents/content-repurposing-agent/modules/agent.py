"""
agent.py — OpenAI API calls for content generation.
"""

import os
import streamlit as st
from openai import OpenAI

from modules.prompts import build_prompt, CONTENT_PROMPTS


def get_client() -> OpenAI:
    """Return OpenAI client using secrets or env var."""
    try:
        api_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    except Exception:
        api_key = os.environ.get("OPENAI_API_KEY", "")
    return OpenAI(api_key=api_key)


def is_configured() -> bool:
    """Return True if API key is set."""
    try:
        key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    except Exception:
        key = os.environ.get("OPENAI_API_KEY", "")
    return bool(key)


def generate_content(
    content_type: str,
    transcript: str,
    style: str = "Educational",
    custom_system: str = "",
    custom_user: str = "",
    max_tokens: int = 2000,
) -> str:
    """
    Generate content using OpenAI GPT-4o.
    Returns generated text or an error string starting with 'Error:'.
    """
    client = get_client()

    if custom_system and custom_user:
        system_prompt = custom_system
        user_prompt = custom_user
    else:
        prompt = build_prompt(content_type, transcript, style)
        if not prompt:
            return f"Error: Unknown content type '{content_type}'"
        system_prompt = prompt["system"]
        user_prompt = prompt["user"]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        err = str(e)
        if "authentication" in err.lower() or "api_key" in err.lower():
            return "Error: Invalid API key. Check your OPENAI_API_KEY in secrets."
        if "rate_limit" in err.lower():
            return "Error: Rate limit exceeded. Wait a moment and try again."
        return f"Error: {err}"


def generate_all_content(
    transcript: str,
    style: str = "Educational",
    content_types: list | None = None,
) -> dict:
    """Generate all content types. Returns {content_type: text}."""
    if content_types is None:
        content_types = list(CONTENT_PROMPTS.keys())
    return {ct: generate_content(ct, transcript, style) for ct in content_types}


def generate_title_and_summary(transcript: str) -> dict:
    """Generate a short title and 2-sentence summary for history display."""
    client = get_client()
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=300,
            messages=[
                {"role": "system", "content": "You extract concise titles and summaries from transcripts."},
                {"role": "user", "content": f"""From this transcript extract:
1. A short title (max 8 words)
2. A 2-sentence summary

Return ONLY valid JSON: {{"title": "...", "summary": "..."}}

TRANSCRIPT:
{transcript[:3000]}"""},
            ],
        )
        import json, re
        text = response.choices[0].message.content.strip()
        text = re.sub(r"```(?:json)?|```", "", text).strip()
        return json.loads(text)
    except Exception:
        words = transcript.split()
        return {"title": " ".join(words[:6]) + "...", "summary": " ".join(words[:30]) + "..."}
