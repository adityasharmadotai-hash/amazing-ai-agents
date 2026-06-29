"""Google Gemini client wrapper.

A thin, testable wrapper around ``google-generativeai`` that handles
configuration, generation parameters, retries, JSON extraction and rate-limit
errors. The interface is deliberately OpenAI-compatible in spirit (a single
``complete`` method) so the agent could be pointed at another provider with
minimal change.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.exceptions import AIAgentError, RateLimitError
from core.logging_config import get_logger

logger = get_logger(__name__)

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)
_FENCE = re.compile(r"```(?:json|sql)?\s*(.*?)```", re.DOTALL)


@dataclass
class LLMResponse:
    """A normalised response from the language model."""

    text: str
    raw: Any = None

    def extract_json(self) -> dict[str, Any]:
        """Best-effort extraction of a JSON object from the model output."""
        candidate = self.text.strip()
        fenced = _FENCE.search(candidate)
        if fenced:
            candidate = fenced.group(1).strip()
        match = _JSON_BLOCK.search(candidate)
        if match:
            candidate = match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise AIAgentError(
                "The AI returned a response that could not be parsed as JSON.",
                detail=str(exc),
            ) from exc

    def strip_code_fences(self) -> str:
        fenced = _FENCE.search(self.text)
        if fenced:
            return fenced.group(1).strip()
        return self.text.strip()


class GeminiClient:
    """Wrapper around the Gemini generative model."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> None:
        if not api_key or not api_key.strip():
            raise AIAgentError("A Gemini API key is required. Add it in Settings or .env.")
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._configure(api_key)

    def _configure(self, api_key: str) -> None:
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            self._genai = genai
            self._model = genai.GenerativeModel(self.model_name)
            logger.info("Initialised Gemini model: %s", self.model_name)
        except ImportError as exc:  # pragma: no cover
            raise AIAgentError(
                "google-generativeai is not installed.", detail=str(exc)
            ) from exc

    def update_params(
        self,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> None:
        if temperature is not None:
            self.temperature = temperature
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if model is not None and model != self.model_name:
            self.model_name = model
            self._model = self._genai.GenerativeModel(model)

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def complete(
        self,
        prompt: str,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a completion for ``prompt`` and return the text."""
        generation_config = {
            "temperature": self.temperature if temperature is None else temperature,
            "max_output_tokens": self.max_tokens if max_tokens is None else max_tokens,
        }
        try:
            response = self._model.generate_content(
                prompt, generation_config=generation_config
            )
            text = self._extract_text(response)
            if not text:
                raise AIAgentError("The AI returned an empty response.")
            return LLMResponse(text=text, raw=response)
        except Exception as exc:  # noqa: BLE001
            message = str(exc).lower()
            if "rate" in message or "quota" in message or "429" in message:
                raise RateLimitError(detail=str(exc)) from exc
            if isinstance(exc, AIAgentError):
                raise
            raise AIAgentError("The AI request failed.", detail=str(exc)) from exc

    @staticmethod
    def _extract_text(response: Any) -> str:
        """Pull text out of a Gemini response object robustly."""
        text = getattr(response, "text", None)
        if text:
            return text.strip()
        # Fallback: walk candidates/parts.
        try:
            parts = []
            for candidate in getattr(response, "candidates", []) or []:
                content = getattr(candidate, "content", None)
                for part in getattr(content, "parts", []) or []:
                    if getattr(part, "text", None):
                        parts.append(part.text)
            return "\n".join(parts).strip()
        except (AttributeError, TypeError):
            return ""
