"""
LLM client wrapper around the OpenAI Chat Completions API.

Design goals
------------
* Single place that knows how to talk to OpenAI.
* Graceful degradation: if no API key is configured the agent still runs in
  a deterministic "demo / offline" mode so the UI is fully explorable.
* Robust JSON extraction so structured generation never crashes the app.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from config import OPENAI_MODEL, OPENAI_MAX_TOKENS, OPENAI_TEMPERATURE


class LLMClient:
    """Thin convenience wrapper. Lazily constructs the OpenAI SDK client."""

    def __init__(self, api_key: str | None = None, model: str = OPENAI_MODEL):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self._client = None

    # ----------------------------------------------------------------- #
    @property
    def available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI  # imported lazily so app loads without the dep

            self._client = OpenAI(api_key=self.api_key)
        return self._client

    # ----------------------------------------------------------------- #
    def complete(
        self,
        system: str,
        user: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
    ) -> str:
        """Return a plain-text completion. Raises on hard API errors."""
        if not self.available:
            raise RuntimeError("No OpenAI API key configured.")
        client = self._get_client()
        resp = client.chat.completions.create(
            model=model or self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=OPENAI_TEMPERATURE if temperature is None else temperature,
            max_tokens=max_tokens or OPENAI_MAX_TOKENS,
        )
        return (resp.choices[0].message.content or "").strip()

    def complete_json(
        self,
        system: str,
        user: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Any:
        """Completion constrained to JSON, parsed and returned as a Python object."""
        system_json = system + (
            "\n\nReturn ONLY valid JSON with no markdown fences, no commentary, "
            "no preamble. The entire response must be parseable by json.loads()."
        )
        raw = self.complete(system_json, user, temperature=temperature, max_tokens=max_tokens)
        return extract_json(raw)


# --------------------------------------------------------------------------- #
# JSON extraction helpers
# --------------------------------------------------------------------------- #
def extract_json(text: str) -> Any:
    """Best-effort parse of a model response into JSON.

    Handles ```json fences, leading/trailing prose, and falls back to locating
    the outermost {...} or [...] block.
    """
    if not text:
        raise ValueError("Empty response")

    cleaned = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Find first { or [ and matching last } or ]
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = cleaned.find(open_ch)
        end = cleaned.rfind(close_ch)
        if start != -1 and end != -1 and end > start:
            snippet = cleaned[start : end + 1]
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Could not parse JSON from model response: {text[:200]}")
