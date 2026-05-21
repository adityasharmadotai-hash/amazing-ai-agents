"""
tts.py — Text-to-Speech via OpenAI TTS API.
Generates audio bytes from text for in-browser playback.
"""

import base64
import os

import streamlit as st
from openai import OpenAI

VOICES = {
    "Alloy": "alloy",       # Neutral
    "Echo": "echo",         # Male
    "Fable": "fable",       # British
    "Onyx": "onyx",         # Deep male
    "Nova": "nova",         # Female
    "Shimmer": "shimmer",   # Soft female
}

VOICE_DESCRIPTIONS = {
    "alloy": "Neutral, balanced",
    "echo": "Clear, male",
    "fable": "Warm, British",
    "onyx": "Deep, authoritative",
    "nova": "Bright, female",
    "shimmer": "Soft, friendly",
}


def get_client() -> OpenAI:
    try:
        key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    except Exception:
        key = os.environ.get("OPENAI_API_KEY", "")
    return OpenAI(api_key=key)


def synthesize(text: str, voice: str = "nova", speed: float = 1.0) -> bytes | None:
    """
    Convert text to speech. Returns MP3 bytes or None on error.
    voice: one of alloy, echo, fable, onyx, nova, shimmer
    speed: 0.25 to 4.0
    """
    if not text or not text.strip():
        return None

    # Trim very long text
    text = text[:4000] if len(text) > 4000 else text

    client = get_client()
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            speed=max(0.25, min(4.0, speed)),
        )
        return response.content
    except Exception:
        return None


def audio_to_html(audio_bytes: bytes, autoplay: bool = True) -> str:
    """Convert audio bytes to an HTML audio tag for Streamlit rendering."""
    b64 = base64.b64encode(audio_bytes).decode()
    autoplay_attr = "autoplay" if autoplay else ""
    return f"""
    <audio controls {autoplay_attr} style="width:100%;border-radius:8px;margin-top:8px;">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
