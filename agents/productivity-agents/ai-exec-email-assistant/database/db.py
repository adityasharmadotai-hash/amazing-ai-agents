"""SQLite connection management and schema bootstrap."""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from typing import Iterator

from config.settings import get_settings
from utils.logging_config import get_logger

logger = get_logger(__name__)

_LOCAL = threading.local()

SCHEMA = """
CREATE TABLE IF NOT EXISTS emails (
    id              TEXT PRIMARY KEY,
    thread_id       TEXT,
    sender          TEXT,
    sender_email    TEXT,
    recipient       TEXT,
    subject         TEXT,
    snippet         TEXT,
    body            TEXT,
    labels          TEXT,
    is_unread       INTEGER DEFAULT 0,
    is_starred      INTEGER DEFAULT 0,
    is_important    INTEGER DEFAULT 0,
    received_at     TEXT,
    cached_at       TEXT DEFAULT (datetime('now')),
    ai_summary      TEXT,
    needs_followup  INTEGER DEFAULT 0,
    priority_score  REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS drafts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    reply_to    TEXT,
    tone        TEXT,
    subject     TEXT,
    body        TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS briefings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_date  TEXT,
    content     TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS analytics_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type  TEXT,
    payload     TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_emails_received ON emails(received_at);
CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender_email);
CREATE INDEX IF NOT EXISTS idx_briefings_date ON briefings(brief_date);
"""


def _connect() -> sqlite3.Connection:
    settings = get_settings()
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def get_connection() -> sqlite3.Connection:
    """Thread-local connection (Streamlit reruns across threads)."""
    conn = getattr(_LOCAL, "conn", None)
    if conn is None:
        conn = _connect()
        _LOCAL.conn = conn
    return conn


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


_INITIALISED = False


def init_db() -> None:
    global _INITIALISED
    if _INITIALISED:
        return
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    _INITIALISED = True
    logger.info("Database initialised at %s", get_settings().db_path)
