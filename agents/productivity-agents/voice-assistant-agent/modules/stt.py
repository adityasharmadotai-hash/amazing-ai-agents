"""
stt.py — Speech-to-Text via OpenAI Whisper API.
Handles microphone recordings (WAV bytes) and uploaded audio files.
"""

import io
import os
import tempfile
from pathlib import Path

import streamlit as st
from openai import OpenAI

SUPPORTED = [".mp3", ".wav", ".m4a", ".ogg", ".webm", ".mp4", ".flac"]


def get_client() -> OpenAI:
    try:
        key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    except Exception:
        key = os.environ.get("OPENAI_API_KEY", "")
    return OpenAI(api_key=key)


def transcribe_bytes(audio_bytes: bytes, ext: str = ".wav", language: str = "en") -> dict:
    """
    Transcribe raw audio bytes using OpenAI Whisper.
    Returns: {"text": "...", "language": "en", "duration": 12.3}
    On error: {"error": "message"}
    """
    if not audio_bytes or len(audio_bytes) < 100:
        return {"error": "Audio too short or empty. Please record at least 1 second."}

    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > 25:
        return {"error": f"Audio too large ({size_mb:.1f} MB). Max is 25 MB."}

    client = get_client()

    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as f:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="verbose_json",
                    language=language if language != "auto" else None,
                )
            text = (response.text or "").strip()
            duration = round(getattr(response, "duration", 0) or 0, 1)
            lang = getattr(response, "language", language) or language
            return {"text": text, "language": lang, "duration": duration}
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        err = str(e)
        if "authentication" in err.lower():
            return {"error": "Invalid API key."}
        if "rate_limit" in err.lower():
            return {"error": "Rate limit. Please wait and try again."}
        return {"error": f"Transcription failed: {err}"}


def transcribe_uploaded(uploaded_file) -> dict:
    """Transcribe a Streamlit UploadedFile object."""
    ext = Path(uploaded_file.name).suffix.lower()
    if ext not in SUPPORTED:
        return {"error": f"Unsupported format: {ext}. Use MP3, WAV, M4A, OGG, WebM, MP4, FLAC."}
    return transcribe_bytes(uploaded_file.read(), ext)
