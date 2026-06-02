"""Gmail OAuth + email fetching."""
import base64
import os
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Read-only Gmail PLUS Sheets/Drive so the SAME token.json works for both.
# (If you change these, delete token.json and log in again.)
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_credentials(
    credentials_file: str = "credentials.json",
    token_file: str = "token.json",
):
    """Authenticate and return cached/refreshed OAuth credentials."""
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # Refresh or run the browser login flow if needed.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return creds


def get_gmail_service(
    credentials_file: str = "credentials.json",
    token_file: str = "token.json",
):
    """Authenticate and return a Gmail API client."""
    creds = get_credentials(credentials_file, token_file)
    return build("gmail", "v1", credentials=creds)


def _header(headers: list[dict], name: str) -> str:
    """Pull a single header value (e.g. 'From', 'Subject')."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _extract_body(payload: dict) -> str:
    """Walk the MIME tree and return plain-text body."""
    if payload.get("body", {}).get("data"):
        data = payload["body"]["data"]
        return base64.urlsafe_b64decode(data).decode("utf-8", "ignore")

    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part["body"].get("data"):
            data = part["body"]["data"]
            return base64.urlsafe_b64decode(data).decode("utf-8", "ignore")
        # Nested multipart
        nested = _extract_body(part)
        if nested:
            return nested
    return ""


def build_query(mode: str = "inbox", label: str | None = None) -> str:
    """Translate a friendly mode into a Gmail search query."""
    if mode == "unread":
        q = "is:unread"
    elif mode == "last_24h":
        after = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())
        q = f"after:{after}"
    else:  # inbox
        q = "in:inbox"
    if label:
        q += f" label:{label}"
    return q


def fetch_emails(service, mode: str = "inbox",
                 label: str | None = None, max_results: int = 25) -> list[dict]:
    """Return a list of cleaned email dicts."""
    query = build_query(mode, label)
    resp = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    emails = []
    for meta in resp.get("messages", []):
        msg = service.users().messages().get(
            userId="me", id=meta["id"], format="full"
        ).execute()

        headers = msg["payload"]["headers"]
        raw_date = _header(headers, "Date")
        try:
            date = parsedate_to_datetime(raw_date).strftime("%Y-%m-%d %H:%M")
        except Exception:
            date = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

        emails.append({
            "email_id": meta["id"],
            "date": date,
            "sender": _header(headers, "From"),
            "subject": _header(headers, "Subject") or "(no subject)",
            "body": _extract_body(msg["payload"])[:4000],  # cap for the LLM
        })
    return emails


def list_labels(service) -> list[str]:
    """Return the user's Gmail label names."""
    resp = service.users().labels().list(userId="me").execute()
    return [l["name"] for l in resp.get("labels", [])]
