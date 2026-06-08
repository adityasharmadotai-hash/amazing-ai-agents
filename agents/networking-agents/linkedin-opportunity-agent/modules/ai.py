"""
ai.py — Thin OpenAI wrapper used across the app.

Every AI feature degrades gracefully: when no API key is configured the calling
modules fall back to deterministic, rule-based output so the dashboard is fully
usable out of the box. Sync and async clients are both provided — the async
client powers concurrent scanning of many posts at once.
"""

from __future__ import annotations

import json
import re

from .config import ai_enabled, get_api_key, get_model

try:
    from openai import AsyncOpenAI, OpenAI
except Exception:  # openai not installed yet
    OpenAI = None
    AsyncOpenAI = None


def is_configured() -> bool:
    return ai_enabled() and OpenAI is not None


def _sync_client():
    return OpenAI(api_key=get_api_key())


def _async_client():
    return AsyncOpenAI(api_key=get_api_key())


# ── JSON helpers ─────────────────────────────────────────────────────────────────
def parse_json(text: str):
    """Strip markdown fences / prose and parse the first JSON object or array."""
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1)
    return json.loads(cleaned)


def _messages(system: str, user: str):
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ── Completions ──────────────────────────────────────────────────────────────────
def complete(system: str, user: str, max_tokens: int = 1400, json_mode: bool = False) -> str:
    """Plain text completion (sync). Raises on failure — callers handle fallback."""
    kwargs: dict = {
        "model": get_model(),
        "max_tokens": max_tokens,
        "messages": _messages(system, user),
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = _sync_client().chat.completions.create(**kwargs)
    return (resp.choices[0].message.content or "").strip()


def complete_json(system: str, user: str, max_tokens: int = 1400):
    return parse_json(complete(system, user, max_tokens=max_tokens, json_mode=True))


async def complete_async(
    system: str, user: str, max_tokens: int = 1200, json_mode: bool = False
) -> str:
    """Async text completion — used to analyse many posts concurrently."""
    kwargs: dict = {
        "model": get_model(),
        "max_tokens": max_tokens,
        "messages": _messages(system, user),
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = await _async_client().chat.completions.create(**kwargs)
    return (resp.choices[0].message.content or "").strip()
