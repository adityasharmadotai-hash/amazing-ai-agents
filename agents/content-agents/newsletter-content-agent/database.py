"""
modules/database.py
-------------------
Lightweight SQLite persistence for local settings and generated newsletters.

Two tables:
  - settings:    key/value store (API keys + user preferences)
  - newsletters: history of everything the agent has generated
"""

import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "newsletter.db")


@contextmanager
def _conn():
    """Context-managed SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they do not yet exist."""
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS newsletters (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT,
                subject    TEXT,
                topic      TEXT,
                audience   TEXT,
                style      TEXT,
                length     TEXT,
                content_md TEXT,
                sources    TEXT,
                created_at TEXT
            )
            """
        )


# --------------------------------------------------------------------------- #
# Settings (key/value)
# --------------------------------------------------------------------------- #
def set_setting(key: str, value) -> None:
    """Store a single setting. Non-string values are JSON-encoded."""
    if not isinstance(value, str):
        value = json.dumps(value)
    with _conn() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def get_setting(key: str, default=None):
    """Fetch a setting, attempting to JSON-decode it; falls back to raw string."""
    with _conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    raw = row["value"]
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw


def save_settings(data: dict) -> None:
    """Persist many settings at once."""
    for key, value in data.items():
        set_setting(key, value)


def get_all_settings() -> dict:
    """Return every stored setting as a dict."""
    with _conn() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
    out = {}
    for row in rows:
        try:
            out[row["key"]] = json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            out[row["key"]] = row["value"]
    return out


# --------------------------------------------------------------------------- #
# Newsletters (history)
# --------------------------------------------------------------------------- #
def save_newsletter(data: dict) -> int:
    """Insert a generated newsletter and return its new id."""
    with _conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO newsletters
                (title, subject, topic, audience, style, length, content_md, sources, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("title", ""),
                data.get("subject", ""),
                data.get("topic", ""),
                data.get("audience", ""),
                data.get("style", ""),
                data.get("length", ""),
                data.get("content_md", ""),
                json.dumps(data.get("sources", [])),
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        return cur.lastrowid


def list_newsletters(limit: int = 50) -> list:
    """Return saved newsletters, newest first."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM newsletters ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        try:
            item["sources"] = json.loads(item.get("sources") or "[]")
        except (json.JSONDecodeError, TypeError):
            item["sources"] = []
        result.append(item)
    return result


def get_newsletter(newsletter_id: int):
    """Fetch a single newsletter by id."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM newsletters WHERE id = ?", (newsletter_id,)
        ).fetchone()
    if row is None:
        return None
    item = dict(row)
    try:
        item["sources"] = json.loads(item.get("sources") or "[]")
    except (json.JSONDecodeError, TypeError):
        item["sources"] = []
    return item


def delete_newsletter(newsletter_id: int) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM newsletters WHERE id = ?", (newsletter_id,))


def count_newsletters() -> int:
    with _conn() as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM newsletters").fetchone()["c"]
