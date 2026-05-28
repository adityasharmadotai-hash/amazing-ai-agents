"""
modules/gmail_client.py
-----------------------
Gmail API + Google Calendar API integration.
Handles OAuth2 flow, email fetching, sending, and calendar events.
"""
from __future__ import annotations
import base64
import email as email_lib
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Google API imports (graceful fallback if not installed)
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/contacts.readonly",
]

CREDENTIALS_PATH = Path("credentials/google_credentials.json")
TOKEN_PATH = Path("credentials/google_token.json")


# ── OAuth Flow ────────────────────────────────────────────────────────────────

def get_oauth_flow(client_id: str, client_secret: str, redirect_uri: str) -> Any:
    """Create an OAuth2 flow for Google APIs."""
    if not GOOGLE_AVAILABLE:
        raise ImportError("Google API libraries not installed.")
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = redirect_uri
    return flow


def get_auth_url(flow: Any) -> str:
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def exchange_code(flow: Any, code: str) -> dict:
    flow.fetch_token(code=code)
    creds = flow.credentials
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else SCOPES,
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
    }
    TOKEN_PATH.parent.mkdir(exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(token_data))
    return token_data


def load_credentials() -> Any | None:
    """Load saved credentials from token file."""
    if not GOOGLE_AVAILABLE or not TOKEN_PATH.exists():
        return None
    try:
        data = json.loads(TOKEN_PATH.read_text())
        from google.oauth2.credentials import Credentials
        creds = Credentials(
            token=data.get("token"),
            refresh_token=data.get("refresh_token"),
            token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            scopes=data.get("scopes", SCOPES),
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            data["token"] = creds.token
            if creds.expiry:
                data["expiry"] = creds.expiry.isoformat()
            TOKEN_PATH.write_text(json.dumps(data))
        return creds
    except Exception:
        return None


def is_authenticated() -> bool:
    creds = load_credentials()
    return creds is not None and creds.valid


def revoke_credentials() -> None:
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()


# ── Gmail Client ──────────────────────────────────────────────────────────────

def _gmail_service():
    creds = load_credentials()
    if not creds:
        raise ValueError("Not authenticated. Please connect Gmail first.")
    return build("gmail", "v1", credentials=creds)


def _calendar_service():
    creds = load_credentials()
    if not creds:
        raise ValueError("Not authenticated.")
    return build("calendar", "v3", credentials=creds)


def get_profile() -> dict:
    """Get the authenticated user's Gmail profile."""
    try:
        svc = _gmail_service()
        return svc.users().getProfile(userId="me").execute()
    except Exception as e:
        return {"emailAddress": "unknown", "error": str(e)}


def fetch_emails(
    max_results: int = 50,
    label: str = "INBOX",
    query: str = "",
    include_body: bool = False,
) -> list[dict]:
    """Fetch emails from Gmail."""
    try:
        svc = _gmail_service()
        q = f"label:{label} {query}".strip()
        result = svc.users().messages().list(
            userId="me", maxResults=max_results, q=q
        ).execute()
        messages = result.get("messages", [])
        emails = []
        for msg in messages:
            detail = svc.users().messages().get(
                userId="me",
                messageId=msg["id"],
                format="full" if include_body else "metadata",
                metadataHeaders=["From", "To", "Subject", "Date", "CC", "Message-ID"],
            ).execute()
            emails.append(_parse_email(detail, include_body))
        return emails
    except Exception as e:
        return []


def fetch_thread(thread_id: str) -> list[dict]:
    """Fetch all messages in a thread."""
    try:
        svc = _gmail_service()
        thread = svc.users().threads().get(
            userId="me", id=thread_id, format="full"
        ).execute()
        return [_parse_email(msg, include_body=True) for msg in thread.get("messages", [])]
    except Exception:
        return []


def fetch_email_body(message_id: str) -> str:
    """Fetch full body of a single email."""
    try:
        svc = _gmail_service()
        detail = svc.users().messages().get(
            userId="me", messageId=message_id, format="full"
        ).execute()
        return _extract_body(detail.get("payload", {}))
    except Exception:
        return ""


def _parse_email(msg: dict, include_body: bool = False) -> dict:
    """Convert raw Gmail API message to clean dict."""
    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    body = ""
    if include_body:
        body = _extract_body(msg.get("payload", {}))

    labels = msg.get("labelIds", [])
    return {
        "id": msg.get("id", ""),
        "thread_id": msg.get("threadId", ""),
        "subject": headers.get("Subject", "(no subject)"),
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "cc": headers.get("CC", ""),
        "date": headers.get("Date", ""),
        "snippet": msg.get("snippet", ""),
        "body": body,
        "labels": labels,
        "is_unread": "UNREAD" in labels,
        "is_important": "IMPORTANT" in labels,
        "is_starred": "STARRED" in labels,
        "message_id_header": headers.get("Message-ID", ""),
    }


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text body from Gmail payload."""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if body_data and mime_type in ("text/plain", "text/html"):
        text = base64.urlsafe_b64decode(body_data + "==").decode("utf-8", errors="ignore")
        if mime_type == "text/html":
            # Strip HTML tags
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
        return text[:3000]  # Cap at 3000 chars for API efficiency

    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result
    return ""


def send_email(to: str, subject: str, body: str, reply_to_id: str = "", thread_id: str = "") -> bool:
    """Send an email via Gmail API."""
    try:
        svc = _gmail_service()
        message = email_lib.mime.text.MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        if reply_to_id:
            message["In-Reply-To"] = reply_to_id
            message["References"] = reply_to_id

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body_dict: dict = {"raw": raw}
        if thread_id:
            body_dict["threadId"] = thread_id

        svc.users().messages().send(userId="me", body=body_dict).execute()
        return True
    except Exception as e:
        return False


def mark_as_read(message_id: str) -> bool:
    try:
        svc = _gmail_service()
        svc.users().messages().modify(
            userId="me", id=message_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()
        return True
    except Exception:
        return False


def star_email(message_id: str) -> bool:
    try:
        svc = _gmail_service()
        svc.users().messages().modify(
            userId="me", id=message_id,
            body={"addLabelIds": ["STARRED"]}
        ).execute()
        return True
    except Exception:
        return False


def get_labels() -> list[dict]:
    try:
        svc = _gmail_service()
        result = svc.users().labels().list(userId="me").execute()
        return result.get("labels", [])
    except Exception:
        return []


# ── Google Calendar ───────────────────────────────────────────────────────────

def fetch_upcoming_events(days_ahead: int = 7, max_results: int = 20) -> list[dict]:
    """Fetch upcoming calendar events."""
    try:
        svc = _calendar_service()
        now = datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + timedelta(days=days_ahead)).isoformat() + "Z"

        events_result = svc.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])
        return [_parse_event(e) for e in events]
    except Exception:
        return []


def fetch_todays_events() -> list[dict]:
    """Fetch today's calendar events."""
    try:
        svc = _calendar_service()
        today = datetime.utcnow().date()
        time_min = datetime(today.year, today.month, today.day).isoformat() + "Z"
        time_max = datetime(today.year, today.month, today.day, 23, 59, 59).isoformat() + "Z"

        result = svc.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        return [_parse_event(e) for e in result.get("items", [])]
    except Exception:
        return []


def _parse_event(event: dict) -> dict:
    start = event.get("start", {})
    end = event.get("end", {})
    attendees = [a.get("email", "") for a in event.get("attendees", [])]
    return {
        "id": event.get("id", ""),
        "title": event.get("summary", "(No title)"),
        "description": event.get("description", ""),
        "start": start.get("dateTime", start.get("date", "")),
        "end": end.get("dateTime", end.get("date", "")),
        "location": event.get("location", ""),
        "attendees": attendees,
        "organizer": event.get("organizer", {}).get("email", ""),
        "meet_link": event.get("hangoutLink", ""),
        "status": event.get("status", "confirmed"),
        "conference_data": event.get("conferenceData", {}),
    }
