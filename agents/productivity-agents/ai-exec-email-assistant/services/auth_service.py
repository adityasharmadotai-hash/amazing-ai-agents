"""Google OAuth authentication service.

Supports two flows:
  * **Web flow** (default for deployed Streamlit) — redirect-based, uses
    `st.query_params` to capture the `?code=` returned by Google.
  * **Installed-app / local flow** — convenient for local development when a
    `client_secret.json` is available; opens a browser and runs a local server.

Credentials are cached to disk (per Google account email) so users don't have
to re-auth every session, and mirrored into `st.session_state`.
"""
from __future__ import annotations

import json
import secrets
import string
from pathlib import Path
from typing import Optional

import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build

from config.settings import get_settings
from utils.logging_config import get_logger

logger = get_logger(__name__)

_TOKEN_FILE = "token.json"


class AuthError(Exception):
    """Raised when authentication cannot be completed."""


def _token_path() -> Path:
    settings = get_settings()
    return Path(settings.token_dir) / _TOKEN_FILE


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def save_credentials(creds: Credentials) -> None:
    _token_path().write_text(creds.to_json(), encoding="utf-8")
    logger.info("Saved OAuth credentials to disk.")


def load_saved_credentials() -> Optional[Credentials]:
    path = _token_path()
    if not path.exists():
        return None
    try:
        settings = get_settings()
        creds = Credentials.from_authorized_user_info(
            json.loads(path.read_text(encoding="utf-8")), settings.scopes
        )
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
            save_credentials(creds)
        return creds if creds and creds.valid else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load saved credentials: %s", exc)
        return None


def clear_credentials() -> None:
    path = _token_path()
    if path.exists():
        path.unlink()
        logger.info("Cleared stored credentials.")


# ---------------------------------------------------------------------------
# Web (redirect) flow
# ---------------------------------------------------------------------------
def _build_web_flow(code_verifier: Optional[str] = None) -> Flow:
    settings = get_settings()
    kwargs = {"scopes": settings.scopes}
    if code_verifier is not None:
        # Pin the verifier so authorization_url() uses it (no autogeneration)
        # and the later exchange can replay the exact same value.
        kwargs["code_verifier"] = code_verifier
        kwargs["autogenerate_code_verifier"] = False
    if settings.google_client_secrets_file and Path(settings.google_client_secrets_file).exists():
        flow = Flow.from_client_secrets_file(settings.google_client_secrets_file, **kwargs)
    else:
        flow = Flow.from_client_config(settings.client_config(), **kwargs)
    flow.redirect_uri = settings.google_redirect_uri
    return flow


def _new_code_verifier() -> str:
    """RFC 7636 code verifier: 43-128 chars from the unreserved set."""
    alphabet = string.ascii_letters + string.digits + "-._~"
    return "".join(secrets.choice(alphabet) for _ in range(128))


def _pkce_path() -> Path:
    """Disk fallback for the PKCE verifier/state across the OAuth redirect.

    Streamlit reruns the script on the redirect, and `st.session_state` is
    *usually* preserved within the same browser session — but to be robust
    (e.g. if the session id changes) we also persist to disk.
    """
    settings = get_settings()
    return Path(settings.token_dir) / "pkce.json"


def _save_pkce(state: str, verifier: str) -> None:
    """Persist the PKCE verifier + state to both session_state and disk."""
    payload = {"state": state, "code_verifier": verifier}
    try:
        import streamlit as st  # local import: auth_service stays importable headless

        st.session_state["_oauth_pkce"] = payload
    except Exception:  # noqa: BLE001
        pass
    try:
        path = _pkce_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not persist PKCE verifier to disk: %s", exc)


def _load_pkce() -> dict:
    """Retrieve the saved PKCE payload (session_state first, then disk)."""
    try:
        import streamlit as st

        payload = st.session_state.get("_oauth_pkce")
        if payload and payload.get("code_verifier"):
            return payload
    except Exception:  # noqa: BLE001
        pass
    try:
        path = _pkce_path()
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load PKCE verifier from disk: %s", exc)
    return {}


def _clear_pkce() -> None:
    try:
        import streamlit as st

        st.session_state.pop("_oauth_pkce", None)
    except Exception:  # noqa: BLE001
        pass
    try:
        path = _pkce_path()
        if path.exists():
            path.unlink()
    except OSError:
        pass


def get_authorization_url() -> tuple[str, str]:
    """Return (auth_url, state) to redirect the user to Google.

    The PKCE code verifier generated here is persisted so the later
    `exchange_code_for_credentials` call (a separate Streamlit run) can
    replay it — otherwise Google rejects the exchange with
    "Missing code verifier".
    """
    verifier = _new_code_verifier()
    flow = _build_web_flow(code_verifier=verifier)
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    _save_pkce(state, verifier)
    return auth_url, state


def exchange_code_for_credentials(code: str) -> Credentials:
    """Exchange the `?code=` returned by Google for credentials.

    Replays the PKCE verifier (and state) saved when the auth URL was built.
    """
    saved = _load_pkce()
    verifier = saved.get("code_verifier")
    flow = _build_web_flow(code_verifier=verifier) if verifier else _build_web_flow()
    state = saved.get("state")
    if state:
        try:
            flow.oauth2session._state = state
        except Exception:  # noqa: BLE001
            pass
    try:
        flow.fetch_token(code=code)
    except Exception as exc:  # noqa: BLE001
        raise AuthError(f"Failed to exchange authorization code: {exc}") from exc
    finally:
        _clear_pkce()
    creds = flow.credentials
    save_credentials(creds)
    return creds


# ---------------------------------------------------------------------------
# Installed-app (local) flow — dev convenience
# ---------------------------------------------------------------------------
def run_local_flow() -> Credentials:
    settings = get_settings()
    if settings.google_client_secrets_file and Path(settings.google_client_secrets_file).exists():
        flow = InstalledAppFlow.from_client_secrets_file(
            settings.google_client_secrets_file, scopes=settings.scopes
        )
    else:
        flow = InstalledAppFlow.from_client_config(
            settings.client_config(), scopes=settings.scopes
        )
    creds = flow.run_local_server(port=0)
    save_credentials(creds)
    return creds


# ---------------------------------------------------------------------------
# Profile / service builders
# ---------------------------------------------------------------------------
def get_user_profile(creds: Credentials) -> dict:
    try:
        service = build("oauth2", "v2", credentials=creds, cache_discovery=False)
        info = service.userinfo().get().execute()
        return {"email": info.get("email", ""), "name": info.get("name", "")}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not fetch user profile: %s", exc)
        return {"email": "", "name": ""}
