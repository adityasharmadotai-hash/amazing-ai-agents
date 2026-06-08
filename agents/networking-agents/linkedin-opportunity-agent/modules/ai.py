"""
ai.py — Thin Claude (Anthropic) wrapper used across the app.

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
    import anthropic
except Exception:  # anthropic not installed yet
    anthropic = None


def is_configured() -> bool:
    return ai_enabled() and anthropic is not None


def _sync_client():
    return anthropic.Anthropic(api_key=get_api_key())


def _async_client():
    return anthropic.AsyncAnthropic(api_key=get_api_key())


# ── JSON helpers ─────────────────────────────────────────────────────────────────
def parse_json(text: str):
    """Strip markdown fences / prose and parse the first JSON object or array."""
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    # Grab the outermost {...} or [...] if the model wrapped it in prose.
    match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1)
    return json.loads(cleaned)


def _extract_text(resp) -> str:
    return "".join(b.text for b in resp.content if b.type == "text").strip()


# ── Completions ──────────────────────────────────────────────────────────────────
def complete(system: str, user: str, max_tokens: int = 1400) -> str:
    """Plain text completion (sync). Raises on failure — callers handle fallback.

    No temperature/top_p are passed: those parameters are rejected by the newest
    Claude models and unnecessary here, so omitting them keeps the call valid
    across every model in the catalogue.
    """
    resp = _sync_client().messages.create(
        model=get_model(),
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return _extract_text(resp)


def complete_json(system: str, user: str, max_tokens: int = 1400):
    return parse_json(complete(system, user, max_tokens=max_tokens))


async def complete_async(system: str, user: str, max_tokens: int = 1200) -> str:
    """Async text completion — used to analyse many posts concurrently."""
    resp = await _async_client().messages.create(
        model=get_model(),
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return _extract_text(resp)
