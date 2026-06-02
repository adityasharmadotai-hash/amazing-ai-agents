"""
Central configuration for the AI Executive Email Assistant.

All tunables are read from environment variables (loaded from a local
`.env` file in development). Nothing secret is hard-coded.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env exactly once, from the project root, regardless of CWD.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _get_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (TypeError, ValueError):
        return default


# Google API scopes. Keep read/modify for Gmail (draft creation) + calendar read.
GOOGLE_SCOPES: List[str] = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/calendar.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings snapshot."""

    # --- OpenAI ---
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_reasoning_model: str = os.getenv("OPENAI_REASONING_MODEL", "gpt-4o")
    openai_transcribe_model: str = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")
    openai_tts_model: str = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
    openai_tts_voice: str = os.getenv("OPENAI_TTS_VOICE", "alloy")
    openai_max_tokens: int = _get_int("OPENAI_MAX_TOKENS", 1500)
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))

    # --- Google OAuth ---
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8501"
    )
    # Path to a downloaded OAuth client_secret.json (alternative to id/secret).
    google_client_secrets_file: str = os.getenv("GOOGLE_CLIENT_SECRETS_FILE", "")
    scopes: List[str] = field(default_factory=lambda: list(GOOGLE_SCOPES))

    # --- Storage ---
    db_path: str = os.getenv("DB_PATH", str(PROJECT_ROOT / "database" / "assistant.db"))
    token_dir: str = os.getenv("TOKEN_DIR", str(PROJECT_ROOT / ".tokens"))

    # --- App behaviour ---
    app_title: str = os.getenv("APP_TITLE", "AI Executive Email Assistant")
    owner_name: str = os.getenv("OWNER_NAME", "")
    timezone: str = os.getenv("TIMEZONE", "Asia/Kolkata")
    max_emails_fetch: int = _get_int("MAX_EMAILS_FETCH", 50)
    cache_ttl_minutes: int = _get_int("CACHE_TTL_MINUTES", 10)
    enable_voice: bool = _get_bool("ENABLE_VOICE", True)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_google_credentials(self) -> bool:
        return bool(
            (self.google_client_id and self.google_client_secret)
            or (self.google_client_secrets_file and Path(self.google_client_secrets_file).exists())
        )

    def client_config(self) -> dict:
        """Build a google-auth `client_config` dict from env vars."""
        return {
            "web": {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.google_redirect_uri],
            }
        }

    def ensure_dirs(self) -> None:
        Path(self.token_dir).mkdir(parents=True, exist_ok=True)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)


# Singleton-style accessor so the dataclass is built once.
_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_dirs()
    return _settings
