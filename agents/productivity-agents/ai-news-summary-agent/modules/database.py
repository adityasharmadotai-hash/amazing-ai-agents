"""
modules/database.py
-------------------
SQLite persistence: articles, user preferences, digests, saved stories, analytics.
"""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/news_agent.db")


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    c = _conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS articles (
            id           TEXT PRIMARY KEY,
            title        TEXT NOT NULL,
            source       TEXT,
            url          TEXT,
            published    TEXT,
            summary      TEXT,
            full_text    TEXT,
            image_url    TEXT,
            topics       TEXT,
            sentiment    TEXT,
            signal_score REAL DEFAULT 0,
            is_duplicate INTEGER DEFAULT 0,
            fetched_at   TEXT
        );

        CREATE TABLE IF NOT EXISTS preferences (
            id           INTEGER PRIMARY KEY,
            topics       TEXT,
            keywords     TEXT,
            industries   TEXT,
            companies    TEXT,
            countries    TEXT,
            sources      TEXT,
            updated_at   TEXT
        );

        CREATE TABLE IF NOT EXISTS digests (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at   TEXT,
            title        TEXT,
            summary      TEXT,
            article_ids  TEXT,
            article_count INTEGER DEFAULT 0,
            sent_email   INTEGER DEFAULT 0,
            digest_type  TEXT DEFAULT 'daily'
        );

        CREATE TABLE IF NOT EXISTS saved (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id TEXT,
            saved_at  TEXT,
            note      TEXT
        );

        CREATE TABLE IF NOT EXISTS analytics (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT,
            total_fetched   INTEGER DEFAULT 0,
            total_unique    INTEGER DEFAULT 0,
            total_dupes     INTEGER DEFAULT 0,
            top_topics      TEXT,
            top_sources     TEXT,
            avg_signal      REAL DEFAULT 0,
            recorded_at     TEXT
        );

        CREATE TABLE IF NOT EXISTS schedule (
            id          INTEGER PRIMARY KEY,
            enabled     INTEGER DEFAULT 1,
            time_utc    TEXT DEFAULT '06:00',
            frequency   TEXT DEFAULT 'daily',
            last_run    TEXT,
            next_run    TEXT
        );
    """)
    # Seed default preferences
    existing = c.execute("SELECT COUNT(*) FROM preferences").fetchone()[0]
    if existing == 0:
        c.execute("""INSERT INTO preferences
            (id, topics, keywords, industries, companies, countries, sources, updated_at)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?)""", (
            json.dumps(["Technology", "AI", "Business", "Finance", "Science"]),
            json.dumps(["artificial intelligence", "machine learning", "startup", "IPO"]),
            json.dumps(["Technology", "Finance", "Healthcare"]),
            json.dumps(["Apple", "Google", "Microsoft", "OpenAI", "Tesla"]),
            json.dumps(["United States", "United Kingdom", "India"]),
            json.dumps(["TechCrunch", "Reuters", "BBC", "Hacker News", "The Verge"]),
            datetime.now().isoformat(),
        ))
    # Seed default schedule
    sched = c.execute("SELECT COUNT(*) FROM schedule").fetchone()[0]
    if sched == 0:
        c.execute("INSERT INTO schedule (id, time_utc, frequency) VALUES (1, '06:00', 'daily')")
    c.commit()
    c.close()


# ── Articles ──────────────────────────────────────────────────────────────────

def upsert_articles(articles: list[dict]) -> int:
    """Insert articles, skip duplicates. Returns count inserted."""
    c = _conn()
    inserted = 0
    now = datetime.now().isoformat()
    for a in articles:
        existing = c.execute("SELECT id FROM articles WHERE id=?", (a["id"],)).fetchone()
        if existing:
            continue
        c.execute("""
            INSERT INTO articles
            (id, title, source, url, published, summary, full_text, image_url,
             topics, sentiment, signal_score, is_duplicate, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            a.get("id", ""), a.get("title", ""), a.get("source", ""),
            a.get("url", ""), a.get("published", ""), a.get("summary", ""),
            a.get("full_text", ""), a.get("image_url", ""),
            json.dumps(a.get("topics", [])),
            a.get("sentiment", "neutral"),
            a.get("signal_score", 0.0),
            1 if a.get("is_duplicate") else 0,
            now,
        ))
        inserted += 1
    c.commit()
    c.close()
    return inserted


def get_articles(
    limit: int = 100,
    topics: list | None = None,
    min_signal: float = 0.0,
    exclude_dupes: bool = True,
    search: str = "",
    days_back: int = 7,
) -> list[dict]:
    c = _conn()
    conditions = ["1=1"]
    params: list = []

    if exclude_dupes:
        conditions.append("is_duplicate = 0")
    if min_signal > 0:
        conditions.append("signal_score >= ?")
        params.append(min_signal)
    if search:
        conditions.append("(title LIKE ? OR summary LIKE ?)")
        params += [f"%{search}%", f"%{search}%"]
    if days_back:
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=days_back)).isoformat()
        conditions.append("fetched_at >= ?")
        params.append(cutoff)

    where = " AND ".join(conditions)
    rows = c.execute(
        f"SELECT * FROM articles WHERE {where} ORDER BY signal_score DESC, fetched_at DESC LIMIT ?",
        params + [limit],
    ).fetchall()
    c.close()
    result = []
    for r in rows:
        d = dict(r)
        d["topics"] = json.loads(d.get("topics") or "[]")
        result.append(d)
    # Filter by topics in Python (JSON array stored as string)
    if topics:
        result = [a for a in result if any(t in a["topics"] for t in topics)]
    return result


def get_article(aid: str) -> dict | None:
    c = _conn()
    row = c.execute("SELECT * FROM articles WHERE id=?", (aid,)).fetchone()
    c.close()
    if not row:
        return None
    d = dict(row)
    d["topics"] = json.loads(d.get("topics") or "[]")
    return d


def mark_duplicate(aid: str) -> None:
    c = _conn()
    c.execute("UPDATE articles SET is_duplicate=1 WHERE id=?", (aid,))
    c.commit()
    c.close()


def update_article_ai(aid: str, summary: str, sentiment: str, signal_score: float, topics: list) -> None:
    c = _conn()
    c.execute("""UPDATE articles SET summary=?, sentiment=?, signal_score=?, topics=?
                 WHERE id=?""",
              (summary, sentiment, signal_score, json.dumps(topics), aid))
    c.commit()
    c.close()


def get_article_stats() -> dict:
    c = _conn()
    total = c.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    dupes = c.execute("SELECT COUNT(*) FROM articles WHERE is_duplicate=1").fetchone()[0]
    high_signal = c.execute("SELECT COUNT(*) FROM articles WHERE signal_score >= 7").fetchone()[0]
    today = datetime.now().date().isoformat()
    today_count = c.execute(
        "SELECT COUNT(*) FROM articles WHERE fetched_at LIKE ?", (f"{today}%",)
    ).fetchone()[0]
    c.close()
    return {"total": total, "dupes": dupes, "high_signal": high_signal, "today": today_count}


# ── Preferences ───────────────────────────────────────────────────────────────

def get_preferences() -> dict:
    c = _conn()
    row = c.execute("SELECT * FROM preferences WHERE id=1").fetchone()
    c.close()
    if not row:
        return {}
    d = dict(row)
    for k in ("topics", "keywords", "industries", "companies", "countries", "sources"):
        d[k] = json.loads(d.get(k) or "[]")
    return d


def save_preferences(prefs: dict) -> None:
    c = _conn()
    c.execute("""INSERT OR REPLACE INTO preferences
        (id, topics, keywords, industries, companies, countries, sources, updated_at)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?)""", (
        json.dumps(prefs.get("topics", [])),
        json.dumps(prefs.get("keywords", [])),
        json.dumps(prefs.get("industries", [])),
        json.dumps(prefs.get("companies", [])),
        json.dumps(prefs.get("countries", [])),
        json.dumps(prefs.get("sources", [])),
        datetime.now().isoformat(),
    ))
    c.commit()
    c.close()


# ── Digests ───────────────────────────────────────────────────────────────────

def save_digest(title: str, summary: str, article_ids: list, digest_type: str = "daily") -> int:
    c = _conn()
    cur = c.execute("""INSERT INTO digests
        (created_at, title, summary, article_ids, article_count, digest_type)
        VALUES (?, ?, ?, ?, ?, ?)""", (
        datetime.now().isoformat(), title, summary,
        json.dumps(article_ids), len(article_ids), digest_type,
    ))
    did = cur.lastrowid
    c.commit()
    c.close()
    return did


def get_digests(limit: int = 20) -> list[dict]:
    c = _conn()
    rows = c.execute(
        "SELECT * FROM digests ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    c.close()
    result = []
    for r in rows:
        d = dict(r)
        d["article_ids"] = json.loads(d.get("article_ids") or "[]")
        result.append(d)
    return result


# ── Saved Stories ─────────────────────────────────────────────────────────────

def save_story(article_id: str, note: str = "") -> None:
    c = _conn()
    existing = c.execute("SELECT id FROM saved WHERE article_id=?", (article_id,)).fetchone()
    if not existing:
        c.execute("INSERT INTO saved (article_id, saved_at, note) VALUES (?, ?, ?)",
                  (article_id, datetime.now().isoformat(), note))
        c.commit()
    c.close()


def get_saved_stories() -> list[dict]:
    c = _conn()
    rows = c.execute("""
        SELECT s.*, a.title, a.source, a.url, a.summary, a.signal_score, a.sentiment
        FROM saved s LEFT JOIN articles a ON s.article_id = a.id
        ORDER BY s.saved_at DESC
    """).fetchall()
    c.close()
    return [dict(r) for r in rows]


def remove_saved(sid: int) -> None:
    c = _conn()
    c.execute("DELETE FROM saved WHERE id=?", (sid,))
    c.commit()
    c.close()


# ── Analytics ─────────────────────────────────────────────────────────────────

def record_analytics(total: int, unique: int, dupes: int, topics: list, sources: list, avg_signal: float) -> None:
    c = _conn()
    today = datetime.now().date().isoformat()
    c.execute("""INSERT OR REPLACE INTO analytics
        (date, total_fetched, total_unique, total_dupes, top_topics, top_sources, avg_signal, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (
        today, total, unique, dupes,
        json.dumps(topics[:5]), json.dumps(sources[:5]),
        avg_signal, datetime.now().isoformat(),
    ))
    c.commit()
    c.close()


def get_analytics(days: int = 14) -> list[dict]:
    c = _conn()
    rows = c.execute(
        "SELECT * FROM analytics ORDER BY date DESC LIMIT ?", (days,)
    ).fetchall()
    c.close()
    result = []
    for r in rows:
        d = dict(r)
        d["top_topics"] = json.loads(d.get("top_topics") or "[]")
        d["top_sources"] = json.loads(d.get("top_sources") or "[]")
        result.append(d)
    return result


# ── Schedule ──────────────────────────────────────────────────────────────────

def get_schedule() -> dict:
    c = _conn()
    row = c.execute("SELECT * FROM schedule WHERE id=1").fetchone()
    c.close()
    return dict(row) if row else {}


def save_schedule(enabled: bool, time_utc: str, frequency: str) -> None:
    c = _conn()
    c.execute("""INSERT OR REPLACE INTO schedule (id, enabled, time_utc, frequency)
                 VALUES (1, ?, ?, ?)""", (1 if enabled else 0, time_utc, frequency))
    c.commit()
    c.close()


def update_schedule_run(last_run: str, next_run: str) -> None:
    c = _conn()
    c.execute("UPDATE schedule SET last_run=?, next_run=? WHERE id=1", (last_run, next_run))
    c.commit()
    c.close()
