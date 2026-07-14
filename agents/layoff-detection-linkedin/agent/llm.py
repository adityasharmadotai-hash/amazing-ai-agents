"""Shared Gemini helper.

Both the news and LinkedIn extractors call `complete_json()` here, so there is
exactly one place that talks to the LLM. This is the module that replaced the
silent OpenAI no-op (missing OPENAI_API_KEY) with a working Gemini call.
"""
from __future__ import annotations

import json
import logging

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from . import config

log = logging.getLogger(__name__)

_configured = False


def _ensure_configured() -> None:
    global _configured
    if _configured:
        return
    if not config.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to .env (get one at "
            "https://aistudio.google.com) — both News and LinkedIn extraction "
            "depend on it."
        )
    genai.configure(api_key=config.GEMINI_API_KEY)
    _configured = True


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        # remove leading ```json / ``` and trailing ```
        text = text.split("\n", 1)[-1] if "\n" in text else text
        if text.endswith("```"):
            text = text[: -3]
    return text.strip()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
def complete_json(system: str, user: str) -> dict | list:
    """Send a prompt and parse the model's reply as JSON.

    Raises on repeated failure (tenacity retries transient errors 3x).
    """
    _ensure_configured()
    model = genai.GenerativeModel(
        config.GEMINI_MODEL,
        system_instruction=system,
        generation_config={"response_mime_type": "application/json"},
    )
    resp = model.generate_content(user)
    raw = _strip_code_fence(resp.text or "")
    # record usage (rough token estimate: ~4 chars/token)
    from . import usage
    usage.add("gemini_calls", 1)
    usage.add("gemini_in_tokens", (len(system) + len(user)) // 4)
    usage.add("gemini_out_tokens", len(raw) // 4)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.warning("LLM returned non-JSON, retrying. First 200 chars: %s", raw[:200])
        raise
