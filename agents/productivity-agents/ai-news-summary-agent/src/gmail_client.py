"""
src/gmail_client.py
-------------------
Handles Google OAuth and reading messages from Gmail.

Supports:
  * Inbox emails
  * Unread emails
  * Emails from the last N hours
  * Filtering by label / folder

It returns clean Python dicts (sender, subject, body, date, ...) so the rest of
the app never has to touch the raw Gmail API payload.
"""

from __future__ import annotations

import base64
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import config


def get_credentials() -> Credentials:
    """Run the OAuth dance (or refresh a saved token) and return credentials."""
    creds: Optional[Credentials] = None

    if _file_exists(config.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, config.SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.CREDENTIALS_FILE, config.SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(config.TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds


def _file_exists(path: str) -> bool:
    import os

    return os.path.exists(path)


class GmailClient:
    """Thin wrapper around the Gmail API tuned for our use case."""

    def __init__(self, creds: Optional[Credentials] = None):
        self.creds = creds or get_credentials()
        self.service = build("gmail", "v1", credentials=self.creds)

    # --- public API ----------------------------------------------------------
    def list_labels(self) -> list[dict]:
        """Return all labels/folders so the UI can offer a dropdown."""
        result = self.service.users().labels().list(userId="me").execute()
        return result.get("labels", [])

    def fetch_emails(
        self,
        max_results: int = config.DEFAULT_MAX_EMAILS,
        label: str = config.DEFAULT_LABEL,
        unread_only: bool = False,
        last_hours: Optional[int] = None,
    ) -> list[dict]:
        """Fetch and parse emails matching the given filters."""
        query_parts = []
        if unread_only:
            query_parts.append("is:unread")
        if last_hours:
            after = int(time.time()) - last_hours * 3600
            query_parts.append(f"after:{after}")
        query = " ".join(query_parts)

        label_ids = [label] if label else None
        listing = (
            self.service.users()
            .messages()
            .list(
                userId="me",
                labelIds=label_ids,
                q=query or None,
                maxResults=max_results,
            )
            .execute()
        )

        messages = listing.get("messages", [])
        emails = []
        for msg in messages:
            try:
                emails.append(self._get_message(msg["id"]))
            except Exception as exc:  # noqa: BLE001 - one bad email shouldn't kill the run
                print(f"[gmail] skipping message {msg['id']}: {exc}")
        return emails

    # --- internals -----------------------------------------------------------
    def _get_message(self, message_id: str) -> dict:
        msg = (
            self.service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}

        return {
            "id": message_id,
            "thread_id": msg.get("threadId"),
            "sender": headers.get("from", "Unknown"),
            "subject": headers.get("subject", "(no subject)"),
            "date": self._parse_date(headers.get("date")),
            "snippet": msg.get("snippet", ""),
            "body": self._extract_body(msg["payload"]),
        }

    @staticmethod
    def _parse_date(raw: Optional[str]) -> str:
        if not raw:
            return datetime.now(timezone.utc).isoformat()
        try:
            return parsedate_to_datetime(raw).isoformat()
        except Exception:  # noqa: BLE001
            return datetime.now(timezone.utc).isoformat()

    def _extract_body(self, payload: dict) -> str:
        """Walk the MIME tree and pull out the plain-text body."""
        if payload.get("body", {}).get("data"):
            return self._decode(payload["body"]["data"])

        for part in payload.get("parts", []):
            mime = part.get("mimeType", "")
            if mime == "text/plain" and part.get("body", {}).get("data"):
                return self._decode(part["body"]["data"])
            if part.get("parts"):  # nested multipart
                nested = self._extract_body(part)
                if nested:
                    return nested
        return ""

    @staticmethod
    def _decode(data: str) -> str:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
