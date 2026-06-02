"""Gmail API service.

Wraps the Gmail REST API into clean, typed methods that return `Email`
dataclasses and persist them to the local cache.
"""
from __future__ import annotations

import base64
from datetime import datetime
from email.mime.text import MIMEText
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from database.models import Email, upsert_emails
from utils.helpers import (
    decode_b64url,
    extract_display_name,
    extract_email_address,
    parse_header_date,
    retry,
    strip_html,
    truncate,
)
from utils.logging_config import get_logger

logger = get_logger(__name__)

_SYSTEM_LABELS = {"UNREAD", "STARRED", "IMPORTANT", "INBOX", "SENT", "DRAFT"}


class GmailError(Exception):
    pass


class GmailService:
    def __init__(self, credentials: Credentials):
        self._service = build("gmail", "v1", credentials=credentials, cache_discovery=False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @retry(attempts=3, exceptions=(HttpError,))
    def _list_message_ids(self, query: str, max_results: int) -> list[str]:
        try:
            resp = (
                self._service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )
        except HttpError as exc:
            raise GmailError(f"Gmail list failed: {exc}") from exc
        return [m["id"] for m in resp.get("messages", [])]

    @retry(attempts=3, exceptions=(HttpError,))
    def _get_message(self, msg_id: str) -> dict:
        return (
            self._service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )

    @staticmethod
    def _extract_body(payload: dict) -> str:
        """Recursively pull the best text body from a Gmail payload."""
        mime = payload.get("mimeType", "")
        body_data = payload.get("body", {}).get("data")
        if mime == "text/plain" and body_data:
            return decode_b64url(body_data)
        if mime == "text/html" and body_data:
            return strip_html(decode_b64url(body_data))
        # Multipart — prefer plain, fall back to html.
        plain, html = "", ""
        for part in payload.get("parts", []) or []:
            sub = GmailService._extract_body(part)
            if part.get("mimeType") == "text/plain" and sub:
                plain = plain or sub
            elif part.get("mimeType") == "text/html" and sub:
                html = html or sub
            elif sub:
                plain = plain or sub
        return plain or html

    def _parse_message(self, msg: dict) -> Email:
        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
        label_ids = msg.get("labelIds", [])
        from_header = headers.get("from", "")
        received = parse_header_date(headers.get("date"))
        body = truncate(self._extract_body(msg.get("payload", {})), 8000)
        return Email(
            id=msg["id"],
            thread_id=msg.get("threadId", ""),
            sender=extract_display_name(from_header),
            sender_email=extract_email_address(from_header),
            recipient=headers.get("to", ""),
            subject=headers.get("subject", "(no subject)"),
            snippet=msg.get("snippet", ""),
            body=body,
            labels=label_ids,
            is_unread="UNREAD" in label_ids,
            is_starred="STARRED" in label_ids,
            is_important="IMPORTANT" in label_ids,
            received_at=received,
        )

    def _fetch_and_cache(self, query: str, max_results: int) -> list[Email]:
        ids = self._list_message_ids(query, max_results)
        emails: list[Email] = []
        for mid in ids:
            try:
                emails.append(self._parse_message(self._get_message(mid)))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping message %s: %s", mid, exc)
        if emails:
            upsert_emails(emails)
        return emails

    # ------------------------------------------------------------------
    # Public read methods
    # ------------------------------------------------------------------
    def read_inbox(self, max_results: int = 25) -> list[Email]:
        return self._fetch_and_cache("in:inbox", max_results)

    def read_unread(self, max_results: int = 25) -> list[Email]:
        return self._fetch_and_cache("in:inbox is:unread", max_results)

    def search(self, query: str, max_results: int = 25) -> list[Email]:
        return self._fetch_and_cache(query, max_results)

    def from_sender(self, name_or_email: str, max_results: int = 25) -> list[Email]:
        return self._fetch_and_cache(f"from:{name_or_email}", max_results)

    def starred(self, max_results: int = 25) -> list[Email]:
        return self._fetch_and_cache("is:starred", max_results)

    def important(self, max_results: int = 25) -> list[Email]:
        return self._fetch_and_cache("is:important", max_results)

    def by_label(self, label: str, max_results: int = 25) -> list[Email]:
        q = f"label:{label}" if label.upper() not in _SYSTEM_LABELS else f"in:{label.lower()}"
        return self._fetch_and_cache(q, max_results)

    @retry(attempts=3, exceptions=(HttpError,))
    def list_labels(self) -> list[str]:
        resp = self._service.users().labels().list(userId="me").execute()
        return sorted(l["name"] for l in resp.get("labels", []))

    def get_thread(self, thread_id: str) -> list[Email]:
        try:
            thread = (
                self._service.users().threads().get(userId="me", id=thread_id, format="full").execute()
            )
        except HttpError as exc:
            raise GmailError(f"Failed to fetch thread: {exc}") from exc
        return [self._parse_message(m) for m in thread.get("messages", [])]

    # ------------------------------------------------------------------
    # Write methods
    # ------------------------------------------------------------------
    def _raw_message(self, to: str, subject: str, body: str,
                     thread_id: Optional[str] = None) -> dict:
        mime = MIMEText(body)
        mime["to"] = to
        mime["subject"] = subject
        raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
        msg: dict = {"raw": raw}
        if thread_id:
            msg["threadId"] = thread_id
        return msg

    @retry(attempts=2, exceptions=(HttpError,))
    def create_draft(self, to: str, subject: str, body: str,
                     thread_id: Optional[str] = None) -> str:
        try:
            draft = (
                self._service.users()
                .drafts()
                .create(userId="me", body={"message": self._raw_message(to, subject, body, thread_id)})
                .execute()
            )
            return draft.get("id", "")
        except HttpError as exc:
            raise GmailError(f"Failed to create draft: {exc}") from exc

    @retry(attempts=2, exceptions=(HttpError,))
    def send_email(self, to: str, subject: str, body: str,
                   thread_id: Optional[str] = None) -> str:
        try:
            sent = (
                self._service.users()
                .messages()
                .send(userId="me", body=self._raw_message(to, subject, body, thread_id))
                .execute()
            )
            return sent.get("id", "")
        except HttpError as exc:
            raise GmailError(f"Failed to send email: {exc}") from exc

    @retry(attempts=2, exceptions=(HttpError,))
    def mark_read(self, msg_id: str) -> None:
        self._service.users().messages().modify(
            userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]}
        ).execute()
