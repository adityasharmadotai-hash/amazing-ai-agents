"""
database.py — SQLite persistence layer.

Stores opportunities, monitored profiles & companies, raw posts, generated
outreach messages, key/value settings, and daily analytics snapshots. A fresh
database is created automatically on first run. On Streamlit Cloud the file
lives under data/ and is recreated if the container restarts — the app reseeds
demo data so it is never empty.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterable

from .config import DB_PATH


# ── Connection helpers ───────────────────────────────────────────────────────────
def _ensure_dir() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


@contextmanager
def get_conn():
    """Yield a SQLite connection with row access by column name."""
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE,
    author_name TEXT,
    author_headline TEXT,
    company TEXT,
    url TEXT,
    text TEXT,
    industry TEXT,
    posted_at TEXT,
    fetched_at TEXT,
    processed INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT,
    post_external_id TEXT,
    person_name TEXT,
    person_headline TEXT,
    company TEXT,
    profile_url TEXT,
    post_url TEXT,
    post_text TEXT,
    opp_type TEXT,
    summary TEXT,
    why_it_matters TEXT,
    recommended_action TEXT,
    confidence INTEGER,
    score_label TEXT,
    score_value INTEGER,
    industry TEXT,
    status TEXT DEFAULT 'new',
    ai_generated INTEGER DEFAULT 0,
    signals TEXT
);

CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    headline TEXT,
    profile_url TEXT UNIQUE,
    company TEXT,
    industry TEXT,
    added_at TEXT
);

CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    page_url TEXT UNIQUE,
    industry TEXT,
    added_at TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER,
    kind TEXT,
    content TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS analytics_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT,
    opportunities_found INTEGER,
    high INTEGER,
    medium INTEGER,
    low INTEGER,
    top_industry TEXT,
    payload TEXT
);
"""


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)


# ── Settings (key/value) ─────────────────────────────────────────────────────────
def set_setting(key: str, value: Any) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value)),
        )


def get_setting(key: str, default: Any = None) -> Any:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    if row is None:
        return default
    try:
        return json.loads(row["value"])
    except Exception:
        return default


# ── Posts ────────────────────────────────────────────────────────────────────────
def upsert_post(post: dict) -> bool:
    """Insert a post if its external_id is new. Returns True if inserted."""
    with get_conn() as conn:
        exists = conn.execute(
            "SELECT 1 FROM posts WHERE external_id=?", (post["external_id"],)
        ).fetchone()
        if exists:
            return False
        conn.execute(
            """INSERT INTO posts(external_id, author_name, author_headline, company, url,
                                 text, industry, posted_at, fetched_at, processed)
               VALUES(?,?,?,?,?,?,?,?,?,0)""",
            (
                post["external_id"],
                post.get("author_name"),
                post.get("author_headline"),
                post.get("company"),
                post.get("url"),
                post.get("text"),
                post.get("industry"),
                post.get("posted_at"),
                _now(),
            ),
        )
    return True


def get_unprocessed_posts() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM posts WHERE processed=0 ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def mark_post_processed(external_id: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE posts SET processed=1 WHERE external_id=?", (external_id,))


# ── Opportunities ────────────────────────────────────────────────────────────────
def add_opportunity(opp: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO opportunities(
                created_at, post_external_id, person_name, person_headline, company,
                profile_url, post_url, post_text, opp_type, summary, why_it_matters,
                recommended_action, confidence, score_label, score_value, industry,
                status, ai_generated, signals)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                _now(),
                opp.get("post_external_id"),
                opp.get("person_name"),
                opp.get("person_headline"),
                opp.get("company"),
                opp.get("profile_url"),
                opp.get("post_url"),
                opp.get("post_text"),
                opp.get("opp_type"),
                opp.get("summary"),
                opp.get("why_it_matters"),
                opp.get("recommended_action"),
                int(opp.get("confidence", 0)),
                opp.get("score_label"),
                int(opp.get("score_value", 0)),
                opp.get("industry"),
                opp.get("status", "new"),
                int(bool(opp.get("ai_generated"))),
                json.dumps(opp.get("signals", [])),
            ),
        )
        return cur.lastrowid


def list_opportunities(
    opp_type: str | None = None,
    score_label: str | None = None,
    industry: str | None = None,
    company: str | None = None,
    person: str | None = None,
    since: str | None = None,
    min_score: int | None = None,
    status: str | None = None,
    order: str = "score",
) -> list[dict]:
    clauses: list[str] = []
    params: list[Any] = []
    if opp_type and opp_type != "All":
        clauses.append("opp_type=?")
        params.append(opp_type)
    if score_label and score_label != "All":
        clauses.append("score_label=?")
        params.append(score_label)
    if industry and industry != "All":
        clauses.append("industry=?")
        params.append(industry)
    if company:
        clauses.append("company LIKE ?")
        params.append(f"%{company}%")
    if person:
        clauses.append("person_name LIKE ?")
        params.append(f"%{person}%")
    if since:
        clauses.append("created_at >= ?")
        params.append(since)
    if min_score is not None:
        clauses.append("score_value >= ?")
        params.append(min_score)
    if status and status != "All":
        clauses.append("status=?")
        params.append(status)

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    order_sql = {
        "score": "score_value DESC, created_at DESC",
        "recent": "created_at DESC",
        "confidence": "confidence DESC",
    }.get(order, "score_value DESC")

    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM opportunities{where} ORDER BY {order_sql}", params
        ).fetchall()
    return [dict(r) for r in rows]


def get_opportunity(opp_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM opportunities WHERE id=?", (opp_id,)).fetchone()
    return dict(row) if row else None


def update_opportunity_status(opp_id: int, status: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE opportunities SET status=? WHERE id=?", (status, opp_id))


def opportunity_exists(post_external_id: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM opportunities WHERE post_external_id=?", (post_external_id,)
        ).fetchone()
    return row is not None


def delete_all_opportunities() -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM opportunities")
        conn.execute("DELETE FROM posts")
        conn.execute("DELETE FROM messages")


# ── Monitored profiles & companies ───────────────────────────────────────────────
def add_profile(name: str, headline: str, profile_url: str, company: str, industry: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO profiles(name, headline, profile_url, company, industry, added_at)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(profile_url) DO UPDATE SET
                 name=excluded.name, headline=excluded.headline,
                 company=excluded.company, industry=excluded.industry""",
            (name, headline, profile_url, company, industry, _now()),
        )


def list_profiles() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM profiles ORDER BY added_at DESC").fetchall()
    return [dict(r) for r in rows]


def delete_profile(profile_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM profiles WHERE id=?", (profile_id,))


def add_company(name: str, page_url: str, industry: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO companies(name, page_url, industry, added_at)
               VALUES(?,?,?,?)
               ON CONFLICT(page_url) DO UPDATE SET
                 name=excluded.name, industry=excluded.industry""",
            (name, page_url, industry, _now()),
        )


def list_companies() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM companies ORDER BY added_at DESC").fetchall()
    return [dict(r) for r in rows]


def delete_company(company_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM companies WHERE id=?", (company_id,))


# ── Outreach messages ────────────────────────────────────────────────────────────
def add_message(opportunity_id: int, kind: str, content: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO messages(opportunity_id, kind, content, created_at) VALUES(?,?,?,?)",
            (opportunity_id, kind, content, _now()),
        )
        return cur.lastrowid


def list_messages(opportunity_id: int | None = None) -> list[dict]:
    with get_conn() as conn:
        if opportunity_id is None:
            rows = conn.execute(
                "SELECT * FROM messages ORDER BY created_at DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM messages WHERE opportunity_id=? ORDER BY created_at DESC",
                (opportunity_id,),
            ).fetchall()
    return [dict(r) for r in rows]


# ── Analytics snapshots ──────────────────────────────────────────────────────────
def save_analytics_snapshot(snapshot: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO analytics_history(
                snapshot_date, opportunities_found, high, medium, low, top_industry, payload)
               VALUES(?,?,?,?,?,?,?)""",
            (
                snapshot.get("snapshot_date", _now()),
                snapshot.get("opportunities_found", 0),
                snapshot.get("high", 0),
                snapshot.get("medium", 0),
                snapshot.get("low", 0),
                snapshot.get("top_industry", ""),
                json.dumps(snapshot.get("payload", {})),
            ),
        )


def list_analytics_history(limit: int = 60) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM analytics_history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Aggregates for the dashboard ─────────────────────────────────────────────────
def counts() -> dict:
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM opportunities").fetchone()["c"]
        by_label = {
            r["score_label"]: r["c"]
            for r in conn.execute(
                "SELECT score_label, COUNT(*) AS c FROM opportunities GROUP BY score_label"
            ).fetchall()
        }
        by_type = {
            r["opp_type"]: r["c"]
            for r in conn.execute(
                "SELECT opp_type, COUNT(*) AS c FROM opportunities GROUP BY opp_type"
            ).fetchall()
        }
        by_industry = {
            r["industry"]: r["c"]
            for r in conn.execute(
                "SELECT industry, COUNT(*) AS c FROM opportunities "
                "WHERE industry IS NOT NULL AND industry != '' GROUP BY industry"
            ).fetchall()
        }
    return {
        "total": total,
        "high": by_label.get("High", 0),
        "medium": by_label.get("Medium", 0),
        "low": by_label.get("Low", 0),
        "by_type": by_type,
        "by_industry": by_industry,
    }


def distinct_values(column: str) -> list[str]:
    if column not in {"opp_type", "industry", "company", "person_name", "score_label"}:
        return []
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT DISTINCT {column} AS v FROM opportunities "
            f"WHERE {column} IS NOT NULL AND {column} != '' ORDER BY {column}"
        ).fetchall()
    return [r["v"] for r in rows]
