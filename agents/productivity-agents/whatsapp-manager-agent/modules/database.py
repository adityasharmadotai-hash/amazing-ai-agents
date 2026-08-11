"""
database.py — SQLite persistence shared by the webhook brain and the dashboard.

Tables
------
contacts        one row per WhatsApp user who has messaged us
conversations   one active/closed thread per contact (+ collected qualification)
messages        every inbound/outbound message, for history and the dashboard
escalations     cases the agent handed off to the human team
settings        key→JSON store for the business profile, questions, config

The design is deliberately boring: WAL mode + short-lived connections so the
FastAPI webhook and the Streamlit dashboard can both touch the file safely.
"""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Iterator

from . import config

log = config.get_logger("wamanager.db")


# ── connection plumbing ───────────────────────────────────────────────────────
@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    import os

    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA foreign_keys=ON;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
    wa_id        TEXT PRIMARY KEY,
    profile_name TEXT,
    name         TEXT,
    source       TEXT DEFAULT 'whatsapp',
    first_seen   TEXT,
    last_seen    TEXT
);

CREATE TABLE IF NOT EXISTS conversations (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    wa_id         TEXT NOT NULL REFERENCES contacts(wa_id),
    status        TEXT NOT NULL DEFAULT 'active',   -- active | escalated | closed
    stage         TEXT NOT NULL DEFAULT 'new',      -- new | greeting | qualifying | answering | escalated | closing
    agent_enabled INTEGER NOT NULL DEFAULT 1,       -- 0 when a human has taken over
    qualification TEXT NOT NULL DEFAULT '{}',       -- JSON of collected answers
    created_at    TEXT,
    updated_at    TEXT
);
CREATE INDEX IF NOT EXISTS idx_conv_wa ON conversations(wa_id);
CREATE INDEX IF NOT EXISTS idx_conv_status ON conversations(status);

CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER REFERENCES conversations(id),
    wa_id           TEXT,
    direction       TEXT,   -- in | out
    sender          TEXT,   -- customer | agent | human | system
    body            TEXT,
    wa_message_id   TEXT,
    created_at      TEXT
);
CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_msg_waid ON messages(wa_message_id)
    WHERE wa_message_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS escalations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER REFERENCES conversations(id),
    wa_id           TEXT,
    reason          TEXT,
    question        TEXT,
    status          TEXT NOT NULL DEFAULT 'open',   -- open | notified | resolved
    channel         TEXT,
    created_at      TEXT,
    resolved_at     TEXT
);
CREATE INDEX IF NOT EXISTS idx_esc_status ON escalations(status);

CREATE TABLE IF NOT EXISTS settings (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at TEXT
);
"""


def init_db() -> None:
    with _connect() as c:
        c.executescript(SCHEMA)
    log.info("Database ready at %s", config.DB_PATH)


# ── settings (business profile, questions, escalation config) ─────────────────
def get_setting(key: str, default: Any = None) -> Any:
    with _connect() as c:
        row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(row["value"])
    except Exception:
        return default


def set_setting(key: str, value: Any) -> None:
    with _connect() as c:
        c.execute(
            "INSERT INTO settings(key, value, updated_at) VALUES(?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, json.dumps(value, ensure_ascii=False), _now()),
        )


# ── contacts ──────────────────────────────────────────────────────────────────
def upsert_contact(wa_id: str, profile_name: str | None = None, source: str = "whatsapp") -> None:
    with _connect() as c:
        exists = c.execute("SELECT wa_id FROM contacts WHERE wa_id=?", (wa_id,)).fetchone()
        if exists:
            c.execute(
                "UPDATE contacts SET last_seen=?, profile_name=COALESCE(?, profile_name) WHERE wa_id=?",
                (_now(), profile_name, wa_id),
            )
        else:
            c.execute(
                "INSERT INTO contacts(wa_id, profile_name, source, first_seen, last_seen) "
                "VALUES(?,?,?,?,?)",
                (wa_id, profile_name, source, _now(), _now()),
            )


def get_contact(wa_id: str) -> dict | None:
    with _connect() as c:
        row = c.execute("SELECT * FROM contacts WHERE wa_id=?", (wa_id,)).fetchone()
    return dict(row) if row else None


# ── conversations ─────────────────────────────────────────────────────────────
def get_active_conversation(wa_id: str) -> dict | None:
    with _connect() as c:
        row = c.execute(
            "SELECT * FROM conversations WHERE wa_id=? AND status!='closed' "
            "ORDER BY id DESC LIMIT 1",
            (wa_id,),
        ).fetchone()
    return _hydrate_conv(row)


def get_or_create_conversation(wa_id: str) -> dict:
    conv = get_active_conversation(wa_id)
    if conv:
        return conv
    with _connect() as c:
        cur = c.execute(
            "INSERT INTO conversations(wa_id, status, stage, created_at, updated_at) "
            "VALUES(?, 'active', 'new', ?, ?)",
            (wa_id, _now(), _now()),
        )
        conv_id = cur.lastrowid
        row = c.execute("SELECT * FROM conversations WHERE id=?", (conv_id,)).fetchone()
    return _hydrate_conv(row)


def get_conversation(conv_id: int) -> dict | None:
    with _connect() as c:
        row = c.execute("SELECT * FROM conversations WHERE id=?", (conv_id,)).fetchone()
    return _hydrate_conv(row)


def update_conversation(
    conv_id: int,
    *,
    status: str | None = None,
    stage: str | None = None,
    agent_enabled: bool | None = None,
    qualification: dict | None = None,
) -> None:
    sets, args = [], []
    if status is not None:
        sets.append("status=?"); args.append(status)
    if stage is not None:
        sets.append("stage=?"); args.append(stage)
    if agent_enabled is not None:
        sets.append("agent_enabled=?"); args.append(1 if agent_enabled else 0)
    if qualification is not None:
        sets.append("qualification=?"); args.append(json.dumps(qualification, ensure_ascii=False))
    if not sets:
        return
    sets.append("updated_at=?"); args.append(_now())
    args.append(conv_id)
    with _connect() as c:
        c.execute(f"UPDATE conversations SET {', '.join(sets)} WHERE id=?", args)


def list_conversations(status: str | None = None, limit: int = 100) -> list[dict]:
    q = (
        "SELECT c.*, ct.profile_name, ct.name AS contact_name, "
        "(SELECT body FROM messages m WHERE m.conversation_id=c.id ORDER BY m.id DESC LIMIT 1) AS last_message "
        "FROM conversations c LEFT JOIN contacts ct ON ct.wa_id=c.wa_id "
    )
    args: list[Any] = []
    if status:
        q += "WHERE c.status=? "
        args.append(status)
    q += "ORDER BY c.updated_at DESC LIMIT ?"
    args.append(limit)
    with _connect() as c:
        rows = c.execute(q, args).fetchall()
    return [_hydrate_conv(r) for r in rows]


def _hydrate_conv(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    d = dict(row)
    try:
        d["qualification"] = json.loads(d.get("qualification") or "{}")
    except Exception:
        d["qualification"] = {}
    d["agent_enabled"] = bool(d.get("agent_enabled", 1))
    return d


# ── messages ──────────────────────────────────────────────────────────────────
def add_message(
    conversation_id: int,
    wa_id: str,
    direction: str,
    sender: str,
    body: str,
    wa_message_id: str | None = None,
) -> int:
    with _connect() as c:
        cur = c.execute(
            "INSERT INTO messages(conversation_id, wa_id, direction, sender, body, wa_message_id, created_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (conversation_id, wa_id, direction, sender, body, wa_message_id, _now()),
        )
        c.execute("UPDATE conversations SET updated_at=? WHERE id=?", (_now(), conversation_id))
        return int(cur.lastrowid)


def message_exists(wa_message_id: str) -> bool:
    """Idempotency guard — WhatsApp re-delivers webhooks, so skip dupes."""
    if not wa_message_id:
        return False
    with _connect() as c:
        row = c.execute(
            "SELECT 1 FROM messages WHERE wa_message_id=? LIMIT 1", (wa_message_id,)
        ).fetchone()
    return row is not None


def get_messages(conversation_id: int, limit: int = 200) -> list[dict]:
    with _connect() as c:
        rows = c.execute(
            "SELECT * FROM messages WHERE conversation_id=? ORDER BY id ASC LIMIT ?",
            (conversation_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_history_for_model(conversation_id: int, turns: int) -> list[dict]:
    """Recent turns as [{role: 'user'|'assistant', text}], oldest first."""
    with _connect() as c:
        rows = c.execute(
            "SELECT direction, body FROM messages WHERE conversation_id=? "
            "ORDER BY id DESC LIMIT ?",
            (conversation_id, turns),
        ).fetchall()
    out = []
    for r in reversed(rows):
        role = "user" if r["direction"] == "in" else "assistant"
        out.append({"role": role, "text": r["body"]})
    return out


# ── escalations ───────────────────────────────────────────────────────────────
def create_escalation(conversation_id: int, wa_id: str, reason: str, question: str) -> int:
    with _connect() as c:
        cur = c.execute(
            "INSERT INTO escalations(conversation_id, wa_id, reason, question, status, created_at) "
            "VALUES(?,?,?,?, 'open', ?)",
            (conversation_id, wa_id, reason, question, _now()),
        )
        return int(cur.lastrowid)


def mark_escalation(esc_id: int, status: str, channel: str | None = None) -> None:
    with _connect() as c:
        resolved = _now() if status == "resolved" else None
        c.execute(
            "UPDATE escalations SET status=?, channel=COALESCE(?, channel), "
            "resolved_at=COALESCE(?, resolved_at) WHERE id=?",
            (status, channel, resolved, esc_id),
        )


def list_escalations(status: str | None = None, limit: int = 100) -> list[dict]:
    q = (
        "SELECT e.*, ct.profile_name FROM escalations e "
        "LEFT JOIN contacts ct ON ct.wa_id=e.wa_id "
    )
    args: list[Any] = []
    if status:
        q += "WHERE e.status=? "
        args.append(status)
    q += "ORDER BY e.id DESC LIMIT ?"
    args.append(limit)
    with _connect() as c:
        rows = c.execute(q, args).fetchall()
    return [dict(r) for r in rows]


def recent_candidates(limit: int = 30) -> list[dict]:
    """Recent people we've talked to — {wa_id, name, phone} — for resolving a
    team's 'Ax, tell <name>…' command to the right candidate."""
    with _connect() as c:
        rows = c.execute(
            "SELECT c.wa_id, c.qualification, ct.profile_name "
            "FROM conversations c LEFT JOIN contacts ct ON ct.wa_id=c.wa_id "
            "ORDER BY c.updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    out, seen = [], set()
    for r in rows:
        if r["wa_id"] in seen:
            continue
        seen.add(r["wa_id"])
        try:
            q = json.loads(r["qualification"] or "{}")
        except Exception:
            q = {}
        out.append({
            "wa_id": r["wa_id"],
            "name": q.get("name") or r["profile_name"] or "",
            "phone": q.get("phone") or "",
        })
    return out


def counts() -> dict:
    with _connect() as c:
        def n(sql, *a):
            return c.execute(sql, a).fetchone()[0]

        return {
            "contacts": n("SELECT COUNT(*) FROM contacts"),
            "active": n("SELECT COUNT(*) FROM conversations WHERE status='active'"),
            "escalated": n("SELECT COUNT(*) FROM conversations WHERE status='escalated'"),
            "open_escalations": n("SELECT COUNT(*) FROM escalations WHERE status!='resolved'"),
            "messages": n("SELECT COUNT(*) FROM messages"),
        }
