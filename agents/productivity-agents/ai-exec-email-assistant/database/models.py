"""Dataclasses + lightweight repository functions over SQLite."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional

from database.db import get_connection, init_db, transaction
from utils.helpers import now_utc


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
@dataclass
class Email:
    id: str
    thread_id: str = ""
    sender: str = ""
    sender_email: str = ""
    recipient: str = ""
    subject: str = ""
    snippet: str = ""
    body: str = ""
    labels: list[str] = field(default_factory=list)
    is_unread: bool = False
    is_starred: bool = False
    is_important: bool = False
    received_at: Optional[datetime] = None
    ai_summary: str = ""
    needs_followup: bool = False
    priority_score: float = 0.0

    def to_row(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "sender": self.sender,
            "sender_email": self.sender_email,
            "recipient": self.recipient,
            "subject": self.subject,
            "snippet": self.snippet,
            "body": self.body,
            "labels": json.dumps(self.labels),
            "is_unread": int(self.is_unread),
            "is_starred": int(self.is_starred),
            "is_important": int(self.is_important),
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "ai_summary": self.ai_summary,
            "needs_followup": int(self.needs_followup),
            "priority_score": self.priority_score,
        }

    @classmethod
    def from_row(cls, row: Any) -> "Email":
        received = row["received_at"]
        return cls(
            id=row["id"],
            thread_id=row["thread_id"] or "",
            sender=row["sender"] or "",
            sender_email=row["sender_email"] or "",
            recipient=row["recipient"] or "",
            subject=row["subject"] or "",
            snippet=row["snippet"] or "",
            body=row["body"] or "",
            labels=json.loads(row["labels"]) if row["labels"] else [],
            is_unread=bool(row["is_unread"]),
            is_starred=bool(row["is_starred"]),
            is_important=bool(row["is_important"]),
            received_at=datetime.fromisoformat(received) if received else None,
            ai_summary=row["ai_summary"] or "",
            needs_followup=bool(row["needs_followup"]),
            priority_score=row["priority_score"] or 0.0,
        )


# ---------------------------------------------------------------------------
# Email repository
# ---------------------------------------------------------------------------
def upsert_emails(emails: list[Email]) -> None:
    if not emails:
        return
    init_db()
    cols = list(emails[0].to_row().keys())
    placeholders = ", ".join(f":{c}" for c in cols)
    updates = ", ".join(f"{c}=excluded.{c}" for c in cols if c != "id")
    sql = (
        f"INSERT INTO emails ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT(id) DO UPDATE SET {updates}"
    )
    with transaction() as conn:
        conn.executemany(sql, [e.to_row() for e in emails])


def get_cached_emails(limit: int = 50, only_unread: bool = False) -> list[Email]:
    init_db()
    conn = get_connection()
    query = "SELECT * FROM emails"
    if only_unread:
        query += " WHERE is_unread = 1"
    query += " ORDER BY received_at DESC LIMIT ?"
    rows = conn.execute(query, (limit,)).fetchall()
    return [Email.from_row(r) for r in rows]


def update_email_ai_fields(
    email_id: str, summary: str | None = None,
    needs_followup: bool | None = None, priority_score: float | None = None,
) -> None:
    init_db()
    fields, params = [], []
    if summary is not None:
        fields.append("ai_summary = ?"); params.append(summary)
    if needs_followup is not None:
        fields.append("needs_followup = ?"); params.append(int(needs_followup))
    if priority_score is not None:
        fields.append("priority_score = ?"); params.append(priority_score)
    if not fields:
        return
    params.append(email_id)
    with transaction() as conn:
        conn.execute(f"UPDATE emails SET {', '.join(fields)} WHERE id = ?", params)


def get_top_contacts(limit: int = 10) -> list[dict[str, Any]]:
    init_db()
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT sender_email, sender AS name, COUNT(*) AS count
        FROM emails
        WHERE sender_email != ''
        GROUP BY sender_email
        ORDER BY count DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Drafts
# ---------------------------------------------------------------------------
def save_draft(reply_to: str, tone: str, subject: str, body: str) -> int:
    init_db()
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO drafts (reply_to, tone, subject, body) VALUES (?,?,?,?)",
            (reply_to, tone, subject, body),
        )
        return int(cur.lastrowid)


def list_drafts(limit: int = 20) -> list[dict[str, Any]]:
    init_db()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM drafts ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Briefings
# ---------------------------------------------------------------------------
def save_briefing(brief_date: str, content: str) -> None:
    init_db()
    with transaction() as conn:
        conn.execute(
            "INSERT INTO briefings (brief_date, content) VALUES (?, ?)",
            (brief_date, content),
        )


def get_latest_briefing() -> Optional[dict[str, Any]]:
    init_db()
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM briefings ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Analytics events
# ---------------------------------------------------------------------------
def log_event(event_type: str, payload: dict[str, Any] | None = None) -> None:
    init_db()
    with transaction() as conn:
        conn.execute(
            "INSERT INTO analytics_events (event_type, payload) VALUES (?, ?)",
            (event_type, json.dumps(payload or {})),
        )


def event_counts(since_days: int = 7) -> dict[str, int]:
    init_db()
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT event_type, COUNT(*) AS c
        FROM analytics_events
        WHERE created_at >= datetime('now', ?)
        GROUP BY event_type
        """,
        (f"-{since_days} days",),
    ).fetchall()
    return {r["event_type"]: r["c"] for r in rows}
