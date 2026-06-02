"""
Central configuration for the AI Executive Email Assistant.

Settings are read from environment variables (loaded from a local `.env`
file in development). On top of that there is a small **runtime overrides**
layer: values entered in the in-app Settings page are persisted to a JSON
file and re-applied to the environment on startup, so the app can be
configured entirely through the UI without editing secrets/`.env`.

Precedence on a fresh boot: real environment variables / Streamlit secrets
win; saved UI overrides only fill in keys that aren't already set. When the
user saves in the Settings page, those values are applied immediately for the
running process (overwriting) and persisted for next boot.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env exactly once, from the project root, regardless of CWD.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

_DEFAULT_DB = str(PROJECT_ROOT / "database" / "assistant.db")
_DEFAULT_TOKENS = str(PROJECT_ROOT / ".tokens")

# Where UI-entered settings are persisted. Override with CONFIG_DIR if the
# project root is read-only.
_CONFIG_DIR = Path(os.getenv("CONFIG_DIR", str(PROJECT_ROOT / ".config")))
_OVERRIDES_PATH = _CONFIG_DIR / "runtime_settings.json"


# Google API scopes. Keep read/modify for Gmail (draft creation) + calendar read.
GOOGLE_SCOPES: List[str] = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/calendar.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

# Environment-variable keys the in-app Settings page is allowed to manage.
# (Used by pages/9_Settings.py to render fields and by the overrides layer.)
RUNTIME_KEYS: tuple[str, ...] = (
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "OPENAI_REASONING_MODEL",
    "OPENAI_TRANSCRIBE_MODEL",
    "OPENAI_TTS_MODEL",
    "OPENAI_TTS_VOICE",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REDIRECT_URI",
    "OWNER_NAME",
    "TIMEZONE",
    "MAX_EMAILS_FETCH",
    "ENABLE_VOICE",
)

# Keys that hold secrets (rendered as password fields, masked in status views).
SECRET_KEYS: frozenset[str] = frozenset(
    {"OPENAI_API_KEY", "GOOGLE_CLIENT_SECRET"}
)


def _get_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Runtime overrides persistence
# ---------------------------------------------------------------------------
def load_overrides() -> Dict[str, str]:
    """Return persisted UI settings (may be empty)."""
    try:
        if _OVERRIDES_PATH.exists():
            data = json.loads(_OVERRIDES_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
    except Exception:  # noqa: BLE001 - never let bad config crash startup
        pass
    return {}


def apply_saved_overrides_to_env() -> None:
    """Fill in env vars from saved overrides WITHOUT clobbering real env/secrets."""
    for key, value in load_overrides().items():
        if value != "" and not os.environ.get(key):
            os.environ[key] = value


def save_overrides(values: Dict[str, str]) -> None:
    """Persist UI settings, apply them to the live process, and rebuild settings.

    Empty-string values are treated as "clear this override".
    """
    current = load_overrides()
    for key, value in values.items():
        if key not in RUNTIME_KEYS:
            continue
        value = (value or "").strip()
        if value == "":
            current.pop(key, None)
            os.environ.pop(key, None)
        else:
            current[key] = value
            os.environ[key] = value  # win for the running process
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _OVERRIDES_PATH.write_text(json.dumps(current, indent=2), encoding="utf-8")
    try:
        _OVERRIDES_PATH.chmod(0o600)  # best-effort: restrict to owner
    except OSError:
        pass
    reset_settings()


def clear_overrides() -> None:
    """Remove all persisted UI settings and unset them from the environment."""
    for key in list(load_overrides().keys()):
        os.environ.pop(key, None)
    try:
        if _OVERRIDES_PATH.exists():
            _OVERRIDES_PATH.unlink()
    except OSError:
        pass
    reset_settings()


def overrides_path() -> Path:
    return _OVERRIDES_PATH


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings snapshot. Build via `Settings.from_env()`."""

    # --- OpenAI ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_reasoning_model: str = "gpt-4o"
    openai_transcribe_model: str = "whisper-1"
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "alloy"
    openai_max_tokens: int = 1500
    openai_temperature: float = 0.3

    # --- Google OAuth ---
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8501"
    google_client_secrets_file: str = ""
    scopes: List[str] = field(default_factory=lambda: list(GOOGLE_SCOPES))

    # --- Storage ---
    db_path: str = _DEFAULT_DB
    token_dir: str = _DEFAULT_TOKENS

    # --- App behaviour ---
    app_title: str = "AI Executive Email Assistant"
    owner_name: str = ""
    timezone: str = "Asia/Kolkata"
    max_emails_fetch: int = 50
    cache_ttl_minutes: int = 10
    enable_voice: bool = True
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        """Read every value from the environment at call time."""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            openai_reasoning_model=os.getenv("OPENAI_REASONING_MODEL", "gpt-4o"),
            openai_transcribe_model=os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1"),
            openai_tts_model=os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
            openai_tts_voice=os.getenv("OPENAI_TTS_VOICE", "alloy"),
            openai_max_tokens=_get_int("OPENAI_MAX_TOKENS", 1500),
            openai_temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.3")),
            google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            google_redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501"),
            google_client_secrets_file=os.getenv("GOOGLE_CLIENT_SECRETS_FILE", ""),
            db_path=os.getenv("DB_PATH", _DEFAULT_DB),
            token_dir=os.getenv("TOKEN_DIR", _DEFAULT_TOKENS),
            app_title=os.getenv("APP_TITLE", "AI Executive Email Assistant"),
            owner_name=os.getenv("OWNER_NAME", ""),
            timezone=os.getenv("TIMEZONE", "Asia/Kolkata"),
            max_emails_fetch=_get_int("MAX_EMAILS_FETCH", 50),
            cache_ttl_minutes=_get_int("CACHE_TTL_MINUTES", 10),
            enable_voice=_get_bool("ENABLE_VOICE", True),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

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


# Singleton-style accessor so the dataclass is built once per config change.
_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        apply_saved_overrides_to_env()
        _settings = Settings.from_env()
        _settings.ensure_dirs()
    return _settings


def reset_settings() -> None:
    """Drop the cached Settings so the next get_settings() rebuilds from env."""
    global _settings
    _settings = None
