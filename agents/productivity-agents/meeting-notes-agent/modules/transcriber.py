"""
transcriber.py — Audio/video transcription using OpenAI Whisper API.
Supports MP3, WAV, MP4 uploads.
"""

import io
import os
import tempfile
from pathlib import Path

import streamlit as st
from openai import OpenAI


def get_client() -> OpenAI:
    try:
        key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    except Exception:
        key = os.environ.get("OPENAI_API_KEY", "")
    return OpenAI(api_key=key)


SUPPORTED_FORMATS = [".mp3", ".wav", ".mp4", ".m4a", ".webm", ".ogg"]
MAX_FILE_SIZE_MB = 25  # Whisper API limit


def get_file_size_mb(file_bytes: bytes) -> float:
    return len(file_bytes) / (1024 * 1024)


def transcribe_audio(uploaded_file) -> dict:
    """
    Transcribe an uploaded audio/video file using OpenAI Whisper.
    Returns dict with: text, duration_estimate, language, segments (if available)
    On error returns: {"error": "message"}
    """
    file_bytes = uploaded_file.read()
    filename = uploaded_file.name
    ext = Path(filename).suffix.lower()

    if ext not in SUPPORTED_FORMATS:
        return {"error": f"Unsupported format: {ext}. Use MP3, WAV, MP4, M4A, WebM, or OGG."}

    size_mb = get_file_size_mb(file_bytes)
    if size_mb > MAX_FILE_SIZE_MB:
        return {"error": f"File too large ({size_mb:.1f} MB). Maximum is {MAX_FILE_SIZE_MB} MB for Whisper API."}

    client = get_client()

    try:
        # Write to temp file — Whisper API needs a file-like object with a name
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )

            # Extract data from response
            transcript_text = response.text.strip()
            duration = getattr(response, "duration", None)
            language = getattr(response, "language", "unknown")
            segments = getattr(response, "segments", [])

            # Convert segments to plain dicts
            seg_list = []
            for seg in (segments or []):
                if hasattr(seg, "__dict__"):
                    seg_list.append({
                        "start": round(getattr(seg, "start", 0), 1),
                        "end": round(getattr(seg, "end", 0), 1),
                        "text": getattr(seg, "text", "").strip(),
                    })
                elif isinstance(seg, dict):
                    seg_list.append({
                        "start": round(seg.get("start", 0), 1),
                        "end": round(seg.get("end", 0), 1),
                        "text": seg.get("text", "").strip(),
                    })

            return {
                "text": transcript_text,
                "language": language,
                "duration_seconds": round(duration, 1) if duration else estimate_duration(size_mb, ext),
                "segments": seg_list,
                "word_count": len(transcript_text.split()),
                "file_size_mb": round(size_mb, 2),
                "filename": filename,
            }

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        err = str(e)
        if "audio_too_short" in err.lower() or "too short" in err.lower():
            return {"error": "Audio is too short to transcribe. Minimum ~1 second required."}
        if "invalid_file" in err.lower() or "could not process" in err.lower():
            return {"error": "Could not process this audio file. Ensure it contains valid audio."}
        if "rate_limit" in err.lower():
            return {"error": "Rate limit exceeded. Wait a moment and try again."}
        if "authentication" in err.lower():
            return {"error": "Invalid API key. Check your OPENAI_API_KEY in secrets."}
        return {"error": f"Transcription failed: {err}"}


def estimate_duration(size_mb: float, ext: str) -> float:
    """Rough duration estimate based on file size when API doesn't return duration."""
    # Average bitrates: MP3 ~128kbps, WAV ~1411kbps, MP4 ~256kbps
    bitrate_map = {".mp3": 128, ".wav": 1411, ".mp4": 256, ".m4a": 256, ".webm": 96, ".ogg": 96}
    kbps = bitrate_map.get(ext, 128)
    return round((size_mb * 8 * 1024) / kbps, 1)


def format_duration(seconds: float) -> str:
    """Format seconds to MM:SS or HH:MM:SS."""
    seconds = int(seconds)
    if seconds >= 3600:
        h, r = divmod(seconds, 3600)
        m, s = divmod(r, 60)
        return f"{h}:{m:02d}:{s:02d}"
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"
