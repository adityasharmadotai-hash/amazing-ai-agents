"""
gmail_connector.py — Real Gmail integration via Google OAuth (read-only).

This is the live counterpart to the demo `_seed_emails()` in connectors.py.
It signs in with Google, reads recent messages, and returns them in the exact
same dict shape the rest of the app expects, so nothing downstream changes.

Everything degrades gracefully: if the Google libraries aren't installed or the
user hasn't connected an account, the app simply keeps using demo data.

Setup (one time):
  1. Google Cloud Console → new project → enable the Gmail API.
  2. Create an OAuth client ID of type "Desktop app" → download credentials.json.
  3. In the app: Settings → Connect Gmail → upload credentials.json → Connect.
"""

import os
from datetime import datetime

# Credentials + token are stored at the project root and are git-ignored.
_ROOT = os.path.dirname(os.path.dirname(__file__))
CREDENTIALS_PATH = os.path.join(_ROOT, "credentials.json")
TOKEN_PATH = os.path.join(_ROOT, "token.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except Exception:
    GOOGLE_AVAILABLE = False


# ── Status helpers ──────────────────────────────────────────────────────────────

def gmail_available() -> bool:
    """Are the Google client libraries installed?"""
    return GOOGLE_AVAILABLE


def has_credentials() -> bool:
    """Has the user uploaded their credentials.json?"""
    return os.path.exists(CREDENTIALS_PATH)


def is_authenticated() -> bool:
    """Has the user completed the OAuth sign-in (token saved)?"""
    return os.path.exists(TOKEN_PATH)


# ── Credential / token plumbing ─────────────────────────────────────────────────

def save_credentials_file(uploaded_bytes: bytes):
    with open(CREDENTIALS_PATH, "wb") as f:
        f.write(uploaded_bytes)


def _save_token(creds):
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        f.write(creds.to_json())


def _load_creds():
    if not GOOGLE_AVAILABLE or not os.path.exists(TOKEN_PATH):
        return None
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
        except Exception:
            return None
    return creds


def connect() -> tuple:
    """Run the OAuth flow (opens a browser on this machine). Returns (ok, message)."""
    if not GOOGLE_AVAILABLE:
        return False, ("Google libraries not installed. Run:\n"
                       "pip install google-auth google-auth-oauthlib google-api-python-client")
    if not has_credentials():
        return False, "Upload your credentials.json first."
    try:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
        _save_token(creds)
        return True, "✅ Connected to Gmail!"
    except Exception as e:
        return False, f"Auth failed: {e}"


def disconnect():
    if os.path.exists(TOKEN_PATH):
        os.remove(TOKEN_PATH)


# ── Reading mail ────────────────────────────────────────────────────────────────

def _service():
    creds = _load_creds()
    if not creds:
        return None
    return build("gmail", "v1", credentials=creds)


def _header(headers, name):
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def _split_sender(raw):
    """'Priya Menon <priya@abc.com>' → ('Priya Menon', 'priya@abc.com')."""
    if "<" in raw and ">" in raw:
        name = raw.split("<")[0].strip().strip('"')
        email = raw.split("<")[1].split(">")[0].strip()
        return (name or email), email
    return raw, raw


def fetch_emails(max_results: int = 15, query: str = "newer_than:7d") -> list:
    """Return recent emails in the app's email shape (no AI tags yet)."""
    svc = _service()
    if not svc:
        return []
    resp = svc.users().messages().list(
        userId="me", q=query, maxResults=max_results).execute()
    out = []
    for ref in resp.get("messages", []):
        m = svc.users().messages().get(
            userId="me", id=ref["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]).execute()
        headers = m.get("payload", {}).get("headers", [])
        name, email = _split_sender(_header(headers, "From"))
        ts = int(m.get("internalDate", "0")) / 1000
        received = datetime.fromtimestamp(ts).isoformat() if ts else datetime.now().isoformat()
        out.append({
            "id": m["id"],
            "sender": name,
            "sender_email": email,
            "subject": _header(headers, "Subject") or "(no subject)",
            "snippet": m.get("snippet", ""),
            "received": received,
            "unread": "UNREAD" in m.get("labelIds", []),
            # placeholder tags — overwritten by brief.classify_emails()
            "priority": "medium",
            "category": "Personal",
            "needs_followup": False,
            "is_issue": False,
        })
    return out
