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
        model: str = "gemini-2.0-flash",
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> None:
        if not api_key or not api_key.strip():
            raise AIAgentError("A Gemini API key is required. Add it in Settings or .env.")
        self.model_name = self._normalise_model(model)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._resolved = False  # whether we've auto-corrected the model name
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

    @staticmethod
    def _normalise_model(name: str) -> str:
        """Strip an optional ``models/`` prefix from a model name."""
        name = (name or "").strip()
        return name[len("models/"):] if name.startswith("models/") else name

    # Preference order when auto-selecting a working model.
    _PREFERRED = (
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-flash-latest",
        "gemini-2.5-pro",
        "gemini-2.0-pro",
        "gemini-pro-latest",
    )

    def list_available_models(self) -> list[str]:
        """Return models that support ``generateContent`` for this API key."""
        models: list[str] = []
        try:
            for m in self._genai.list_models():
                methods = getattr(m, "supported_generation_methods", []) or []
                if "generateContent" in methods:
                    models.append(self._normalise_model(getattr(m, "name", "")))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not list Gemini models: %s", exc)
        return [m for m in models if m]

    def _resolve_supported_model(self) -> bool:
        """Pick a supported model when the configured one is unavailable.

        Returns True if a different, usable model was selected.
        """
        available = self.list_available_models()
        if not available:
            return False
        available_set = set(available)

        chosen = next((p for p in self._PREFERRED if p in available_set), None)
        if chosen is None:
            # Otherwise prefer any "flash" model, else the first available.
            chosen = next((m for m in available if "flash" in m.lower()), available[0])

        if chosen and chosen != self.model_name:
            logger.warning(
                "Model '%s' unavailable; falling back to '%s'.", self.model_name, chosen
            )
            self.model_name = chosen
            self._model = self._genai.GenerativeModel(chosen)
            self._resolved = True
            return True
        return False

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
        if model is not None:
            normalised = self._normalise_model(model)
            if normalised and normalised != self.model_name:
                self.model_name = normalised
                self._model = self._genai.GenerativeModel(normalised)
                self._resolved = False

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
        """Generate a completion for ``prompt`` and return the text.

        Handles three failure modes distinctly: genuine rate limits (retried),
        an unavailable/deprecated model (auto-falls back to a supported one and
        retries once), and other errors.
        """
        generation_config = {
            "temperature": self.temperature if temperature is None else temperature,
            "max_output_tokens": self.max_tokens if max_tokens is None else max_tokens,
        }
        try:
            return self._generate(prompt, generation_config)
        except AIAgentError as exc:
            # If the model is unavailable, try once to resolve a supported one.
            if self._is_model_not_found(exc.detail or "") and not self._resolved:
                if self._resolve_supported_model():
                    return self._generate(prompt, generation_config)
            raise

    def _generate(self, prompt: str, generation_config: dict) -> LLMResponse:
        """Single generation attempt with error classification."""
        try:
            response = self._model.generate_content(
                prompt, generation_config=generation_config
            )
            text = self._extract_text(response)
            if not text:
                raise AIAgentError("The AI returned an empty response.")
            return LLMResponse(text=text, raw=response)
        except AIAgentError:
            raise
        except Exception as exc:  # noqa: BLE001
            message = str(exc).lower()
            if self._is_model_not_found(message):
                raise AIAgentError(
                    f"The model '{self.model_name}' is not available for your API key. "
                    "Pick a supported model in Settings (e.g. gemini-2.0-flash).",
                    detail=str(exc),
                ) from exc
            if "rate" in message or "quota" in message or "429" in message or "exhausted" in message:
                raise RateLimitError(detail=str(exc)) from exc
            raise AIAgentError("The AI request failed.", detail=str(exc)) from exc

    @staticmethod
    def _is_model_not_found(message: str) -> bool:
        m = message.lower()
        return (
            "404" in m
            or "not found" in m
            or "is not supported" in m
            or "not supported for generatecontent" in m
        )

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
