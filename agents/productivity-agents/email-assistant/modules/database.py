"""
modules/database.py
-------------------
SQLite persistence for cached emails, contacts, reminders,
follow-up tracking, and AI-generated summaries.
"""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/email_assistant.db")


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS emails (
            id           TEXT PRIMARY KEY,
            thread_id    TEXT,
            subject      TEXT,
            sender       TEXT,
            recipient    TEXT,
            date_str     TEXT,
            snippet      TEXT,
            body         TEXT,
            labels       TEXT,
            is_unread    INTEGER DEFAULT 0,
            is_important INTEGER DEFAULT 0,
            is_starred   INTEGER DEFAULT 0,
            ai_summary   TEXT,
            ai_priority  TEXT,
            cached_at    TEXT
        );

        CREATE TABLE IF NOT EXISTS contacts (
            email        TEXT PRIMARY KEY,
            name         TEXT,
            company      TEXT,
            last_contact TEXT,
            email_count  INTEGER DEFAULT 0,
            ai_summary   TEXT,
            notes        TEXT,
            updated_at   TEXT
        );

        CREATE TABLE IF NOT EXISTS reminders (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id     TEXT,
            title        TEXT NOT NULL,
            due_date     TEXT NOT NULL,
            note         TEXT,
            completed    INTEGER DEFAULT 0,
            created_at   TEXT
        );

        CREATE TABLE IF NOT EXISTS follow_ups (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id     TEXT NOT NULL,
            subject      TEXT,
            recipient    TEXT,
            sent_date    TEXT,
            due_date     TEXT,
            status       TEXT DEFAULT 'pending',
            note         TEXT,
            created_at   TEXT
        );

        CREATE TABLE IF NOT EXISTS drafts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            to_addr      TEXT,
            subject      TEXT,
            body         TEXT,
            tone         TEXT DEFAULT 'professional',
            original_id  TEXT,
            status       TEXT DEFAULT 'draft',
            created_at   TEXT,
            updated_at   TEXT
        );

        CREATE TABLE IF NOT EXISTS ai_cache (
            cache_key    TEXT PRIMARY KEY,
            result       TEXT NOT NULL,
            created_at   TEXT
        );

        CREATE TABLE IF NOT EXISTS analytics (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            date         TEXT NOT NULL,
            emails_received  INTEGER DEFAULT 0,
            emails_sent      INTEGER DEFAULT 0,
            emails_read      INTEGER DEFAULT 0,
            avg_response_hrs REAL DEFAULT 0,
            priority_count   INTEGER DEFAULT 0,
            recorded_at      TEXT
        );
    """)
    conn.commit()
    conn.close()


# ── Emails ────────────────────────────────────────────────────────────────────

def upsert_emails(emails: list[dict]) -> None:
    conn = _connect()
    now = datetime.now().isoformat()
    for e in emails:
        conn.execute("""
            INSERT OR REPLACE INTO emails
            (id, thread_id, subject, sender, recipient, date_str, snippet, body,
             labels, is_unread, is_important, is_starred, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            e.get("id", ""),
            e.get("thread_id", ""),
            e.get("subject", ""),
            e.get("from", ""),
            e.get("to", ""),
            e.get("date", ""),
            e.get("snippet", ""),
            e.get("body", ""),
            json.dumps(e.get("labels", [])),
            1 if e.get("is_unread") else 0,
            1 if e.get("is_important") else 0,
            1 if e.get("is_starred") else 0,
            now,
        ))
    conn.commit()
    conn.close()


def get_emails(
    limit: int = 50,
    unread_only: bool = False,
    important_only: bool = False,
    search: str = "",
) -> list[dict]:
    conn = _connect()
    conditions = []
    params = []
    if unread_only:
        conditions.append("is_unread = 1")
    if important_only:
        conditions.append("is_important = 1")
    if search:
        conditions.append("(subject LIKE ? OR sender LIKE ? OR snippet LIKE ?)")
        params += [f"%{search}%"] * 3
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = conn.execute(
        f"SELECT * FROM emails {where} ORDER BY date_str DESC LIMIT ?",
        params + [limit],
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["labels"] = json.loads(d.get("labels") or "[]")
        result.append(d)
    return result


def get_email(email_id: str) -> dict | None:
    conn = _connect()
    row = conn.execute("SELECT * FROM emails WHERE id = ?", (email_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["labels"] = json.loads(d.get("labels") or "[]")
    return d


def update_email_ai(email_id: str, summary: str, priority: str) -> None:
    conn = _connect()
    conn.execute(
        "UPDATE emails SET ai_summary = ?, ai_priority = ? WHERE id = ?",
        (summary, priority, email_id),
    )
    conn.commit()
    conn.close()


def get_email_stats() -> dict:
    conn = _connect()
    total = conn.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
    unread = conn.execute("SELECT COUNT(*) FROM emails WHERE is_unread=1").fetchone()[0]
    important = conn.execute("SELECT COUNT(*) FROM emails WHERE is_important=1").fetchone()[0]
    starred = conn.execute("SELECT COUNT(*) FROM emails WHERE is_starred=1").fetchone()[0]
    conn.close()
    return {"total": total, "unread": unread, "important": important, "starred": starred}


# ── Contacts ──────────────────────────────────────────────────────────────────

def upsert_contact(email: str, name: str = "", company: str = "") -> None:
    conn = _connect()
    now = datetime.now().isoformat()
    existing = conn.execute("SELECT email_count FROM contacts WHERE email=?", (email,)).fetchone()
    count = (existing["email_count"] + 1) if existing else 1
    conn.execute("""
        INSERT OR REPLACE INTO contacts
        (email, name, company, last_contact, email_count, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (email, name, company, now, count, now))
    conn.commit()
    conn.close()


def get_contacts(limit: int = 50) -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM contacts ORDER BY email_count DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_contact(email: str) -> dict | None:
    conn = _connect()
    row = conn.execute("SELECT * FROM contacts WHERE email=?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_contact_summary(email: str, summary: str) -> None:
    conn = _connect()
    conn.execute(
        "UPDATE contacts SET ai_summary=?, updated_at=? WHERE email=?",
        (summary, datetime.now().isoformat(), email),
    )
    conn.commit()
    conn.close()


# ── Reminders ─────────────────────────────────────────────────────────────────

def add_reminder(title: str, due_date: str, email_id: str = "", note: str = "") -> int:
    conn = _connect()
    cur = conn.execute("""
        INSERT INTO reminders (email_id, title, due_date, note, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (email_id, title, due_date, note, datetime.now().isoformat()))
    rid = cur.lastrowid
    conn.commit()
    conn.close()
    return rid


def get_reminders(include_done: bool = False) -> list[dict]:
    conn = _connect()
    where = "" if include_done else "WHERE completed=0"
    rows = conn.execute(
        f"SELECT * FROM reminders {where} ORDER BY due_date ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def complete_reminder(rid: int) -> None:
    conn = _connect()
    conn.execute("UPDATE reminders SET completed=1 WHERE id=?", (rid,))
    conn.commit()
    conn.close()


def delete_reminder(rid: int) -> None:
    conn = _connect()
    conn.execute("DELETE FROM reminders WHERE id=?", (rid,))
    conn.commit()
    conn.close()


# ── Follow-ups ────────────────────────────────────────────────────────────────

def add_follow_up(email_id: str, subject: str, recipient: str, due_date: str, note: str = "") -> int:
    conn = _connect()
    now = datetime.now().isoformat()
    cur = conn.execute("""
        INSERT INTO follow_ups (email_id, subject, recipient, sent_date, due_date, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (email_id, subject, recipient, now, due_date, note, now))
    fid = cur.lastrowid
    conn.commit()
    conn.close()
    return fid


def get_follow_ups(status: str = "pending") -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM follow_ups WHERE status=? ORDER BY due_date ASC", (status,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_follow_up_status(fid: int, status: str) -> None:
    conn = _connect()
    conn.execute("UPDATE follow_ups SET status=? WHERE id=?", (status, fid))
    conn.commit()
    conn.close()


# ── Drafts ────────────────────────────────────────────────────────────────────

def save_draft(to: str, subject: str, body: str, tone: str = "professional",
               original_id: str = "") -> int:
    conn = _connect()
    now = datetime.now().isoformat()
    cur = conn.execute("""
        INSERT INTO drafts (to_addr, subject, body, tone, original_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (to, subject, body, tone, original_id, now, now))
    did = cur.lastrowid
    conn.commit()
    conn.close()
    return did


def get_drafts() -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM drafts WHERE status='draft' ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_draft(did: int, body: str) -> None:
    conn = _connect()
    conn.execute(
        "UPDATE drafts SET body=?, updated_at=? WHERE id=?",
        (body, datetime.now().isoformat(), did),
    )
    conn.commit()
    conn.close()


def delete_draft(did: int) -> None:
    conn = _connect()
    conn.execute("DELETE FROM drafts WHERE id=?", (did,))
    conn.commit()
    conn.close()


# ── AI Cache ──────────────────────────────────────────────────────────────────

def get_cached(key: str) -> str | None:
    conn = _connect()
    row = conn.execute("SELECT result FROM ai_cache WHERE cache_key=?", (key,)).fetchone()
    conn.close()
    return row["result"] if row else None


def set_cache(key: str, result: str) -> None:
    conn = _connect()
    conn.execute(
        "INSERT OR REPLACE INTO ai_cache (cache_key, result, created_at) VALUES (?, ?, ?)",
        (key, result, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


# ── Analytics ─────────────────────────────────────────────────────────────────

def record_daily_analytics(received: int, sent: int, read: int, avg_hrs: float, priority: int) -> None:
    conn = _connect()
    today = datetime.now().date().isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO analytics
        (date, emails_received, emails_sent, emails_read, avg_response_hrs, priority_count, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (today, received, sent, read, avg_hrs, priority, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_analytics_history(days: int = 30) -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM analytics ORDER BY date DESC LIMIT ?", (days,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_overall_stats() -> dict:
    conn = _connect()
    emails = conn.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
    unread = conn.execute("SELECT COUNT(*) FROM emails WHERE is_unread=1").fetchone()[0]
    reminders = conn.execute("SELECT COUNT(*) FROM reminders WHERE completed=0").fetchone()[0]
    follow_ups = conn.execute("SELECT COUNT(*) FROM follow_ups WHERE status='pending'").fetchone()[0]
    drafts = conn.execute("SELECT COUNT(*) FROM drafts WHERE status='draft'").fetchone()[0]
    contacts = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
    conn.close()
    return {
        "emails": emails, "unread": unread, "reminders": reminders,
        "follow_ups": follow_ups, "drafts": drafts, "contacts": contacts,
    }
