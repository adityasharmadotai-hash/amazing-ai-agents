"""
SQLite persistence layer for the Newsletter Content Agent.

Provides a thin, dependency-free data-access layer over SQLite with a
connection-per-call pattern (safe for Streamlit's threaded reruns). All
schema creation is idempotent so the module can be imported freely.

Tables
------
sources            Registered content sources (RSS, Reddit, YouTube, ...)
content_items      Raw collected items (deduplicated by content hash)
newsletters        Generated newsletter drafts + final versions
schedules          Automation schedules
analytics_events   Lightweight event log powering the dashboard
settings           Key/value store for app-level settings
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterable

from config import DB_PATH

_LOCK = threading.Lock()


# --------------------------------------------------------------------------- #
# Connection management
# --------------------------------------------------------------------------- #
@contextmanager
def get_connection(db_path: str = DB_PATH):
    """Yield a SQLite connection with row factory + foreign keys enabled."""
    conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    source_type   TEXT NOT NULL,
    url           TEXT,
    topic         TEXT,
    industry      TEXT,
    active        INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL,
    last_fetched  TEXT
);

CREATE TABLE IF NOT EXISTS content_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id     INTEGER,
    source_type   TEXT,
    source_name   TEXT,
    title         TEXT NOT NULL,
    url           TEXT,
    summary       TEXT,
    raw_text      TEXT,
    author        TEXT,
    topic         TEXT,
    industry      TEXT,
    published_at  TEXT,
    collected_at  TEXT NOT NULL,
    content_hash  TEXT UNIQUE,
    score         REAL DEFAULT 0,
    FOREIGN KEY (source_id) REFERENCES sources (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS newsletters (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT,
    subject_line    TEXT,
    topic           TEXT,
    industry        TEXT,
    style           TEXT,
    writing_mode    TEXT,
    status          TEXT NOT NULL DEFAULT 'draft',
    body_json       TEXT,
    body_markdown   TEXT,
    body_html       TEXT,
    engagement_score REAL DEFAULT 0,
    source_count    INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schedules (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    frequency     TEXT NOT NULL,
    topic         TEXT,
    industry      TEXT,
    style         TEXT,
    writing_mode  TEXT,
    active        INTEGER NOT NULL DEFAULT 1,
    last_run      TEXT,
    next_run      TEXT,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type  TEXT NOT NULL,
    payload     TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key         TEXT PRIMARY KEY,
    value       TEXT
);

CREATE INDEX IF NOT EXISTS idx_content_topic ON content_items (topic);
CREATE INDEX IF NOT EXISTS idx_content_collected ON content_items (collected_at);
CREATE INDEX IF NOT EXISTS idx_news_status ON newsletters (status);
"""


def init_db(db_path: str = DB_PATH) -> None:
    """Create all tables/indexes if they do not already exist."""
    with _LOCK, get_connection(db_path) as conn:
        conn.executescript(SCHEMA)


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


# --------------------------------------------------------------------------- #
# Sources
# --------------------------------------------------------------------------- #
def add_source(name, source_type, url=None, topic=None, industry=None) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO sources (name, source_type, url, topic, industry, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, source_type, url, topic, industry, _now()),
        )
        return cur.lastrowid


def list_sources(active_only: bool = False) -> list[dict]:
    q = "SELECT * FROM sources"
    if active_only:
        q += " WHERE active = 1"
    q += " ORDER BY created_at DESC"
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(q).fetchall()]


def set_source_active(source_id: int, active: bool) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE sources SET active = ? WHERE id = ?", (1 if active else 0, source_id))


def delete_source(source_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))


def mark_source_fetched(source_id: int) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE sources SET last_fetched = ? WHERE id = ?", (_now(), source_id))


# --------------------------------------------------------------------------- #
# Content items
# --------------------------------------------------------------------------- #
def upsert_content_item(item: dict) -> int | None:
    """Insert a content item; silently skip if the content_hash already exists."""
    with get_connection() as conn:
        try:
            cur = conn.execute(
                """INSERT INTO content_items
                   (source_id, source_type, source_name, title, url, summary,
                    raw_text, author, topic, industry, published_at, collected_at,
                    content_hash, score)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    item.get("source_id"),
                    item.get("source_type"),
                    item.get("source_name"),
                    item.get("title"),
                    item.get("url"),
                    item.get("summary"),
                    item.get("raw_text"),
                    item.get("author"),
                    item.get("topic"),
                    item.get("industry"),
                    item.get("published_at"),
                    _now(),
                    item.get("content_hash"),
                    item.get("score", 0),
                ),
            )
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None  # duplicate content_hash


def query_content(
    topic: str | None = None,
    industry: str | None = None,
    source_type: str | None = None,
    since: str | None = None,
    search: str | None = None,
    limit: int = 200,
) -> list[dict]:
    clauses, params = [], []
    if topic:
        clauses.append("topic = ?")
        params.append(topic)
    if industry:
        clauses.append("industry = ?")
        params.append(industry)
    if source_type:
        clauses.append("source_type = ?")
        params.append(source_type)
    if since:
        clauses.append("collected_at >= ?")
        params.append(since)
    if search:
        clauses.append("(title LIKE ? OR summary LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    q = f"SELECT * FROM content_items{where} ORDER BY score DESC, collected_at DESC LIMIT ?"
    params.append(limit)
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(q, params).fetchall()]


def content_count() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM content_items").fetchone()[0]


# --------------------------------------------------------------------------- #
# Newsletters
# --------------------------------------------------------------------------- #
def save_newsletter(data: dict) -> int:
    now = _now()
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO newsletters
               (title, subject_line, topic, industry, style, writing_mode, status,
                body_json, body_markdown, body_html, engagement_score, source_count,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get("title"),
                data.get("subject_line"),
                data.get("topic"),
                data.get("industry"),
                data.get("style"),
                data.get("writing_mode"),
                data.get("status", "draft"),
                json.dumps(data.get("body_json", {})),
                data.get("body_markdown"),
                data.get("body_html"),
                data.get("engagement_score", 0),
                data.get("source_count", 0),
                now,
                now,
            ),
        )
        return cur.lastrowid


def update_newsletter(news_id: int, fields: dict) -> None:
    if not fields:
        return
    fields = dict(fields)
    if "body_json" in fields and not isinstance(fields["body_json"], str):
        fields["body_json"] = json.dumps(fields["body_json"])
    fields["updated_at"] = _now()
    sets = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [news_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE newsletters SET {sets} WHERE id = ?", params)


def list_newsletters(status: str | None = None, search: str | None = None) -> list[dict]:
    clauses, params = [], []
    if status:
        clauses.append("status = ?")
        params.append(status)
    if search:
        clauses.append("(title LIKE ? OR topic LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM newsletters{where} ORDER BY updated_at DESC", params
        ).fetchall()
        return [_hydrate_newsletter(dict(r)) for r in rows]


def get_newsletter(news_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM newsletters WHERE id = ?", (news_id,)).fetchone()
        return _hydrate_newsletter(dict(row)) if row else None


def delete_newsletter(news_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM newsletters WHERE id = ?", (news_id,))


def _hydrate_newsletter(row: dict) -> dict:
    try:
        row["body_json"] = json.loads(row.get("body_json") or "{}")
    except (json.JSONDecodeError, TypeError):
        row["body_json"] = {}
    return row


# --------------------------------------------------------------------------- #
# Schedules
# --------------------------------------------------------------------------- #
def add_schedule(data: dict) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO schedules
               (name, frequency, topic, industry, style, writing_mode, next_run, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get("name"),
                data.get("frequency"),
                data.get("topic"),
                data.get("industry"),
                data.get("style"),
                data.get("writing_mode"),
                data.get("next_run"),
                _now(),
            ),
        )
        return cur.lastrowid


def list_schedules() -> list[dict]:
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM schedules ORDER BY created_at DESC").fetchall()]


def update_schedule(sched_id: int, fields: dict) -> None:
    if not fields:
        return
    sets = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [sched_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE schedules SET {sets} WHERE id = ?", params)


def delete_schedule(sched_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM schedules WHERE id = ?", (sched_id,))


# --------------------------------------------------------------------------- #
# Analytics events
# --------------------------------------------------------------------------- #
def log_event(event_type: str, payload: dict | None = None) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO analytics_events (event_type, payload, created_at) VALUES (?, ?, ?)",
            (event_type, json.dumps(payload or {}), _now()),
        )


def query_events(event_type: str | None = None, limit: int = 500) -> list[dict]:
    q = "SELECT * FROM analytics_events"
    params: list[Any] = []
    if event_type:
        q += " WHERE event_type = ?"
        params.append(event_type)
    q += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(q, params).fetchall()]


# --------------------------------------------------------------------------- #
# Settings KV store
# --------------------------------------------------------------------------- #
def set_setting(key: str, value: Any) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, json.dumps(value)),
        )


def get_setting(key: str, default: Any = None) -> Any:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if not row:
            return default
        try:
            return json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            return default
