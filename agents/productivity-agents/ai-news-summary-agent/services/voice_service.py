"""Voice service — speech-to-text (Whisper) and text-to-speech (OpenAI TTS)."""
from __future__ import annotations

import io
from typing import Optional

from openai import OpenAI

from config.settings import get_settings
from utils.helpers import retry
from utils.logging_config import get_logger

logger = get_logger(__name__)


class VoiceServiceError(Exception):
    pass


class VoiceService:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.has_openai:
            raise VoiceServiceError("OPENAI_API_KEY is not configured.")
        self._client = OpenAI(api_key=self.settings.openai_api_key)

    @retry(attempts=2, base_delay=1.5)
    def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """Transcribe spoken audio to text via Whisper."""
        if not audio_bytes:
            return ""
        buffer = io.BytesIO(audio_bytes)
        buffer.name = filename
        try:
            resp = self._client.audio.transcriptions.create(
                model=self.settings.openai_transcribe_model,
                file=buffer,
            )
            return (resp.text or "").strip()
        except Exception as exc:  # noqa: BLE001
            raise VoiceServiceError(f"Transcription failed: {exc}") from exc

    @retry(attempts=2, base_delay=1.5)
    def synthesize(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
        """Convert text to spoken audio (MP3 bytes). Returns None on failure."""
        if not text:
            return None
        try:
            resp = self._client.audio.speech.create(
                model=self.settings.openai_tts_model,
                voice=voice or self.settings.openai_tts_voice,
                input=text[:4000],
            )
            return resp.read()
        except Exception as exc:  # noqa: BLE001
            logger.warning("TTS failed: %s", exc)
            return None
