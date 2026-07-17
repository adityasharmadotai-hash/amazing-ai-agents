"""Shared Gemini helper.

Both the news and LinkedIn extractors call `complete_json()` here, so there is
exactly one place that talks to the LLM.

IMPORTANT: `google.generativeai` is imported LAZILY (inside functions), not at
module top. It pulls in grpcio/protobuf (C extensions) whose import at Streamlit
app startup was segfaulting the Cloud health check. Deferring the import until
the first actual Gemini call keeps startup light and crash-free — nothing here
runs until the user triggers a scan.
"""
from __future__ import annotations

import json
import logging

from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

from . import config

log = logging.getLogger(__name__)

_genai = None          # cached google.generativeai module (lazy)
_configured = False


def _get_genai():
    """Import google.generativeai on first use (see module docstring)."""
    global _genai
    if _genai is None:
        import google.generativeai as genai  # noqa: PLC0415 — intentional lazy import
        _genai = genai
    return _genai


def _ensure_configured() -> None:
    global _configured
    if _configured:
        return
    if not config.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it on the Settings page (get one at "
            "https://aistudio.google.com) — both News and LinkedIn extraction "
            "depend on it."
        )
    _get_genai().configure(api_key=config.GEMINI_API_KEY)
    _configured = True


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        # remove leading ```json / ``` and trailing ```
        text = text.split("\n", 1)[-1] if "\n" in text else text
        if text.endswith("```"):
            text = text[: -3]
    return text.strip()


# Only retry when the MODEL returned non-JSON (transient). API errors like
# InvalidArgument (bad key/model/request) are NOT retried — retrying wastes calls
# and hides the real message; we reraise the original error immediately so the
# caller can show exactly what Gemini said.
@retry(retry=retry_if_exception_type(json.JSONDecodeError),
       stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10),
       reraise=True)
def complete_json(system: str, user: str) -> dict | list:
    """Send a prompt and parse the model's reply as JSON.

    Retries up to 3x only on non-JSON replies; API errors propagate immediately.
    """
    _ensure_configured()
    genai = _get_genai()
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
