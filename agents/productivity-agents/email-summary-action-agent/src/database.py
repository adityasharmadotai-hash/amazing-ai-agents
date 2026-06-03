"""
src/database.py
---------------
SQLite persistence layer.

Why SQLite? It is zero-config, ships with Python, and is perfect for a
single-user agent. It gives us three things:

  1. Deduplication  -> we never analyze the same email twice (keyed on Gmail id)
  2. Dashboard data -> fast local queries for the charts and counters
  3. Status sync    -> mark action items Pending / Completed

The Google Sheet is the shareable output; SQLite is the source of truth.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator, Optional

import config


SCHEMA = """
CREATE TABLE IF NOT EXISTS emails (
    id          TEXT PRIMARY KEY,
    date        TEXT,
    sender      TEXT,
    subject     TEXT,
    summary     TEXT,
    action_item TEXT,
    priority    TEXT,
    due_date    TEXT,
    status      TEXT DEFAULT 'Pending',
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS app_meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db() -> None:
    with _conn() as con:
        con.executescript(SCHEMA)


def email_exists(email_id: str) -> bool:
    with _conn() as con:
        row = con.execute("SELECT 1 FROM emails WHERE id = ?", (email_id,)).fetchone()
        return row is not None


def insert_email(record: dict) -> bool:
    """Insert one analyzed email. Returns False if it already existed."""
    if email_exists(record["id"]):
        return False
    with _conn() as con:
        con.execute(
            """
            INSERT INTO emails
                (id, date, sender, subject, summary, action_item, priority, due_date, status)
            VALUES
                (:id, :date, :sender, :subject, :summary, :action_item, :priority, :due_date, :status)
            """,
            {
                "id": record["id"],
                "date": record.get("date", ""),
                "sender": record.get("sender", ""),
                "subject": record.get("subject", ""),
                "summary": record.get("summary", ""),
                "action_item": record.get("action_item", "None"),
                "priority": record.get("priority", "Low"),
                "due_date": record.get("due_date", ""),
                "status": record.get("status", "Pending"),
            },
        )
    return True


def get_all_emails(
    priority: Optional[str] = None,
    status: Optional[str] = None,
) -> list[dict]:
    query = "SELECT * FROM emails WHERE 1=1"
    params: list = []
    if priority and priority != "All":
        query += " AND priority = ?"
        params.append(priority)
    if status and status != "All":
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY date DESC"
    with _conn() as con:
        return [dict(r) for r in con.execute(query, params).fetchall()]


def update_status(email_id: str, status: str) -> None:
    with _conn() as con:
        con.execute("UPDATE emails SET status = ? WHERE id = ?", (status, email_id))


def get_stats() -> dict:
    with _conn() as con:
        total = con.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
        by_priority = {
            r["priority"]: r["n"]
            for r in con.execute(
                "SELECT priority, COUNT(*) n FROM emails GROUP BY priority"
            ).fetchall()
        }
        by_status = {
            r["status"]: r["n"]
            for r in con.execute(
                "SELECT status, COUNT(*) n FROM emails GROUP BY status"
            ).fetchall()
        }
    return {
        "total": total,
        "high": by_priority.get("High", 0),
        "medium": by_priority.get("Medium", 0),
        "low": by_priority.get("Low", 0),
        "pending": by_status.get("Pending", 0),
        "completed": by_status.get("Completed", 0),
    }


# --- generic key/value meta (stores the created sheet id, last run, etc.) ----
def set_meta(key: str, value: str) -> None:
    with _conn() as con:
        con.execute(
            "INSERT INTO app_meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def get_meta(key: str) -> Optional[str]:
    with _conn() as con:
        row = con.execute("SELECT value FROM app_meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None


def delete_meta(key: str) -> None:
    with _conn() as con:
        con.execute("DELETE FROM app_meta WHERE key = ?", (key,))
