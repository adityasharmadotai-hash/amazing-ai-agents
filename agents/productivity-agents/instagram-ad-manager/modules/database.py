"""
database.py — SQLite storage for the Instagram AI Ad Manager.

Self-contained local database (`data/admanager.db`). Holds the campaign cache
synced from the Meta Marketing API plus everything the team edits and the AI
learns from: lead statuses, recommendation history, and stored AI analyses.

Note: on Streamlit Cloud the filesystem is ephemeral, so cloud-side edits reset
on redeploy. For durable multi-user hosting, swap this module for Postgres.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime
from typing import Any, Iterable

from . import config

try:
    import streamlit as st
except Exception:  # pragma: no cover - allows use outside Streamlit
    st = None

log = config.get_logger("admanager.db")

# ── Paths ─────────────────────────────────────────────────────────────────────
# `ADMANAGER_DB_PATH` lets the app and the background sync job share a persistent
# location (e.g. a mounted disk) instead of the ephemeral default.
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.environ.get("ADMANAGER_DB_PATH") or os.path.join(_DATA_DIR, "admanager.db")

LEAD_STATUSES = [
    "New",
    "Qualified",
    "Interview Scheduled",
    "Hired",
    "Rejected",
    "Duplicate",
    "Invalid",
    "No Response",
]

# Statuses the team considers a "good" lead (used for quality analytics).
QUALIFIED_STATUSES = {"Qualified", "Interview Scheduled", "Hired"}
REJECTED_STATUSES = {"Rejected", "Invalid", "Duplicate", "No Response"}


# ── Connection ────────────────────────────────────────────────────────────────
def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


if st is not None:
    _get_conn = st.cache_resource(_connect)
else:  # pragma: no cover
    _CONN: sqlite3.Connection | None = None

    def _get_conn() -> sqlite3.Connection:
        global _CONN
        if _CONN is None:
            _CONN = _connect()
        return _CONN


def get_conn() -> sqlite3.Connection:
    conn = _get_conn()
    init_db(conn)
    return conn


# ── Schema ────────────────────────────────────────────────────────────────────
_SCHEMA = """
CREATE TABLE IF NOT EXISTS campaigns (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    status      TEXT,
    objective   TEXT,
    budget      REAL DEFAULT 0,
    updated_at  TEXT
);

CREATE TABLE IF NOT EXISTS metrics_daily (
    campaign_id TEXT NOT NULL,
    date        TEXT NOT NULL,
    placement   TEXT DEFAULT 'All',
    spend       REAL DEFAULT 0,
    reach       INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    clicks      INTEGER DEFAULT 0,
    leads       INTEGER DEFAULT 0,
    PRIMARY KEY (campaign_id, date, placement)
);

CREATE TABLE IF NOT EXISTS leads (
    id          TEXT PRIMARY KEY,
    name        TEXT,
    email       TEXT,
    phone       TEXT,
    campaign_id TEXT,
    ad_name     TEXT,
    received_at TEXT,
    status      TEXT DEFAULT 'New',
    audience    TEXT,
    age_range   TEXT
);

CREATE TABLE IF NOT EXISTS recommendations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT,
    type        TEXT,
    target      TEXT,
    rationale   TEXT,
    status      TEXT DEFAULT 'pending',   -- pending | implemented | dismissed
    outcome     TEXT DEFAULT 'unknown',   -- unknown | improved | worse | neutral
    verified_at TEXT,
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS analyses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT,
    kind        TEXT,                     -- performance | summary | lead_learning | health | ...
    payload     TEXT,
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT,
    severity    TEXT DEFAULT 'info',      -- info | success | warning | critical
    title       TEXT,
    body        TEXT,
    category    TEXT,
    read        INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sync_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at   TEXT,
    finished_at  TEXT,
    status       TEXT,                    -- running | success | error | partial
    source       TEXT,                    -- manual | scheduled | sample
    campaigns    INTEGER DEFAULT 0,
    metrics      INTEGER DEFAULT 0,
    leads        INTEGER DEFAULT 0,
    ran_ai       INTEGER DEFAULT 0,
    message      TEXT
);

CREATE TABLE IF NOT EXISTS app_meta (
    key    TEXT PRIMARY KEY,
    value  TEXT
);

CREATE INDEX IF NOT EXISTS idx_metrics_date ON metrics_daily(date);
CREATE INDEX IF NOT EXISTS idx_metrics_campaign ON metrics_daily(campaign_id);
CREATE INDEX IF NOT EXISTS idx_leads_received ON leads(received_at);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_campaign ON leads(campaign_id);
CREATE INDEX IF NOT EXISTS idx_notif_read ON notifications(read);
"""

# Columns added after the first release — applied idempotently in _migrate().
_MIGRATIONS = {
    "recommendations": [
        ("confidence", "REAL DEFAULT 0"),
        ("expected_impact", "TEXT DEFAULT ''"),
        ("priority", "TEXT DEFAULT 'medium'"),
    ],
}

_INITED = False


def init_db(conn: sqlite3.Connection | None = None) -> None:
    """Create tables once and apply column migrations (idempotent)."""
    global _INITED
    if _INITED:
        return
    conn = conn or _get_conn()
    conn.executescript(_SCHEMA)
    _migrate(conn)
    conn.commit()
    _INITED = True


def _migrate(conn: sqlite3.Connection) -> None:
    for table, cols in _MIGRATIONS.items():
        existing = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for name, decl in cols:
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
                log.info("migrated: added %s.%s", table, name)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ── Data version (drives Streamlit cache invalidation) ────────────────────────
def _bump() -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO app_meta(key, value) VALUES('data_version', '1') "
        "ON CONFLICT(key) DO UPDATE SET value = CAST(value AS INTEGER) + 1"
    )
    conn.commit()


def get_version() -> int:
    conn = get_conn()
    row = conn.execute("SELECT value FROM app_meta WHERE key='data_version'").fetchone()
    return int(row["value"]) if row else 0


def set_meta(key: str, value: str) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO app_meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()


def get_meta(key: str, default: str | None = None) -> str | None:
    conn = get_conn()
    row = conn.execute("SELECT value FROM app_meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


# ── Upserts (from Meta sync or demo seed) ─────────────────────────────────────
def upsert_campaigns(rows: Iterable[dict]) -> int:
    conn = get_conn()
    n = 0
    for r in rows:
        conn.execute(
            """INSERT INTO campaigns (id, name, status, objective, budget, updated_at)
               VALUES (:id, :name, :status, :objective, :budget, :updated_at)
               ON CONFLICT(id) DO UPDATE SET
                   name=excluded.name, status=excluded.status,
                   objective=excluded.objective, budget=excluded.budget,
                   updated_at=excluded.updated_at""",
            {
                "id": str(r["id"]),
                "name": r.get("name", ""),
                "status": r.get("status", "UNKNOWN"),
                "objective": r.get("objective", ""),
                "budget": float(r.get("budget", 0) or 0),
                "updated_at": r.get("updated_at") or _now(),
            },
        )
        n += 1
    conn.commit()
    _bump()
    return n


def upsert_metrics(rows: Iterable[dict]) -> int:
    conn = get_conn()
    n = 0
    for r in rows:
        conn.execute(
            """INSERT INTO metrics_daily
                   (campaign_id, date, placement, spend, reach, impressions, clicks, leads)
               VALUES (:campaign_id, :date, :placement, :spend, :reach, :impressions, :clicks, :leads)
               ON CONFLICT(campaign_id, date, placement) DO UPDATE SET
                   spend=excluded.spend, reach=excluded.reach,
                   impressions=excluded.impressions, clicks=excluded.clicks,
                   leads=excluded.leads""",
            {
                "campaign_id": str(r["campaign_id"]),
                "date": r["date"],
                "placement": r.get("placement", "All"),
                "spend": float(r.get("spend", 0) or 0),
                "reach": int(r.get("reach", 0) or 0),
                "impressions": int(r.get("impressions", 0) or 0),
                "clicks": int(r.get("clicks", 0) or 0),
                "leads": int(r.get("leads", 0) or 0),
            },
        )
        n += 1
    conn.commit()
    _bump()
    return n


def upsert_leads(rows: Iterable[dict]) -> int:
    conn = get_conn()
    n = 0
    for r in rows:
        # Preserve a team-edited status if the lead already exists.
        conn.execute(
            """INSERT INTO leads
                   (id, name, email, phone, campaign_id, ad_name, received_at, status, audience, age_range)
               VALUES (:id, :name, :email, :phone, :campaign_id, :ad_name, :received_at, :status, :audience, :age_range)
               ON CONFLICT(id) DO UPDATE SET
                   name=excluded.name, email=excluded.email, phone=excluded.phone,
                   campaign_id=excluded.campaign_id, ad_name=excluded.ad_name,
                   received_at=excluded.received_at, audience=excluded.audience,
                   age_range=excluded.age_range""",
            {
                "id": str(r["id"]),
                "name": r.get("name", ""),
                "email": r.get("email", ""),
                "phone": r.get("phone", ""),
                "campaign_id": str(r.get("campaign_id", "")),
                "ad_name": r.get("ad_name", ""),
                "received_at": r.get("received_at") or _now(),
                "status": r.get("status", "New"),
                "audience": r.get("audience", ""),
                "age_range": r.get("age_range", ""),
            },
        )
        n += 1
    conn.commit()
    _bump()
    return n


# ── Reads with filters ────────────────────────────────────────────────────────
def get_campaigns() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM campaigns ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def campaign_name_map() -> dict[str, str]:
    return {c["id"]: c["name"] for c in get_campaigns()}


def get_metrics(
    start: str | None = None,
    end: str | None = None,
    campaign_id: str | None = None,
) -> list[dict]:
    conn = get_conn()
    q = "SELECT * FROM metrics_daily WHERE 1=1"
    p: list[Any] = []
    if start:
        q += " AND date >= ?"
        p.append(start)
    if end:
        q += " AND date <= ?"
        p.append(end)
    if campaign_id and campaign_id != "All":
        q += " AND campaign_id = ?"
        p.append(campaign_id)
    q += " ORDER BY date"
    return [dict(r) for r in conn.execute(q, p).fetchall()]


def get_leads(
    start: str | None = None,
    end: str | None = None,
    campaign_id: str | None = None,
    status: str | None = None,
    ad_name: str | None = None,
) -> list[dict]:
    conn = get_conn()
    q = "SELECT * FROM leads WHERE 1=1"
    p: list[Any] = []
    if start:
        q += " AND received_at >= ?"
        p.append(start)
    if end:
        q += " AND received_at <= ?"
        p.append(end + "T23:59:59")
    if campaign_id and campaign_id != "All":
        q += " AND campaign_id = ?"
        p.append(campaign_id)
    if status and status != "All":
        q += " AND status = ?"
        p.append(status)
    if ad_name and ad_name != "All":
        q += " AND ad_name = ?"
        p.append(ad_name)
    q += " ORDER BY received_at DESC"
    return [dict(r) for r in conn.execute(q, p).fetchall()]


def update_lead_status(lead_id: str, status: str) -> None:
    conn = get_conn()
    conn.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
    conn.commit()
    _bump()


def ad_names() -> list[str]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT ad_name FROM leads WHERE ad_name != '' ORDER BY ad_name"
    ).fetchall()
    return [r["ad_name"] for r in rows]


# ── Recommendations (continuous learning) ─────────────────────────────────────
def add_recommendation(
    rec_type: str,
    target: str,
    rationale: str,
    rec_date: str | None = None,
    confidence: float = 0.0,
    expected_impact: str = "",
    priority: str = "medium",
) -> int:
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO recommendations
               (date, type, target, rationale, status, outcome, created_at,
                confidence, expected_impact, priority)
           VALUES (?, ?, ?, ?, 'pending', 'unknown', ?, ?, ?, ?)""",
        (rec_date or date.today().isoformat(), rec_type, target, rationale, _now(),
         float(confidence or 0), expected_impact or "", priority or "medium"),
    )
    conn.commit()
    _bump()
    return int(cur.lastrowid)


def update_recommendation(rec_id: int, status: str | None = None, outcome: str | None = None) -> None:
    conn = get_conn()
    if status is not None:
        conn.execute("UPDATE recommendations SET status = ? WHERE id = ?", (status, rec_id))
    if outcome is not None:
        conn.execute(
            "UPDATE recommendations SET outcome = ?, verified_at = ? WHERE id = ?",
            (outcome, _now(), rec_id),
        )
    conn.commit()
    _bump()


def get_recommendations(limit: int | None = None) -> list[dict]:
    conn = get_conn()
    q = "SELECT * FROM recommendations ORDER BY date DESC, id DESC"
    if limit:
        q += f" LIMIT {int(limit)}"
    return [dict(r) for r in conn.execute(q).fetchall()]


def has_recommendation_today(rec_date: str | None = None) -> bool:
    conn = get_conn()
    d = rec_date or date.today().isoformat()
    row = conn.execute("SELECT COUNT(*) AS c FROM recommendations WHERE date = ?", (d,)).fetchone()
    return row["c"] > 0


# ── Analyses (stored AI output history) ───────────────────────────────────────
def save_analysis(kind: str, payload: dict, analysis_date: str | None = None) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO analyses (date, kind, payload, created_at) VALUES (?, ?, ?, ?)",
        (analysis_date or date.today().isoformat(), kind, json.dumps(payload), _now()),
    )
    conn.commit()
    _bump()
    return int(cur.lastrowid)


def latest_analysis(kind: str) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM analyses WHERE kind = ? ORDER BY id DESC LIMIT 1", (kind,)
    ).fetchone()
    if not row:
        return None
    d = dict(row)
    try:
        d["payload"] = json.loads(d["payload"])
    except Exception:
        d["payload"] = {}
    return d


def get_analyses(kind: str | None = None, limit: int = 30) -> list[dict]:
    conn = get_conn()
    if kind:
        rows = conn.execute(
            "SELECT * FROM analyses WHERE kind = ? ORDER BY id DESC LIMIT ?", (kind, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM analyses ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["payload"] = json.loads(d["payload"])
        except Exception:
            d["payload"] = {}
        out.append(d)
    return out


# ── Housekeeping ──────────────────────────────────────────────────────────────
def has_data() -> bool:
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) AS c FROM campaigns").fetchone()
    return row["c"] > 0


def date_bounds() -> tuple[str | None, str | None]:
    """Earliest and latest metric dates present, for default filter ranges."""
    conn = get_conn()
    row = conn.execute("SELECT MIN(date) AS lo, MAX(date) AS hi FROM metrics_daily").fetchone()
    return (row["lo"], row["hi"])


def clear_all() -> None:
    """Wipe content + notifications. Keeps sync_log (audit trail) intact so an
    in-progress sync that reseeds sample data doesn't erase its own log row."""
    conn = get_conn()
    for t in ("campaigns", "metrics_daily", "leads", "recommendations", "analyses",
              "notifications"):
        conn.execute(f"DELETE FROM {t}")
    conn.commit()
    _bump()


# ── Notifications (notification center) ───────────────────────────────────────
def add_notification(title: str, body: str, severity: str = "info", category: str = "General") -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO notifications (created_at, severity, title, body, category, read) "
        "VALUES (?, ?, ?, ?, ?, 0)",
        (_now(), severity, title, body, category),
    )
    conn.commit()
    _bump()
    return int(cur.lastrowid)


def get_notifications(unread_only: bool = False, limit: int = 100) -> list[dict]:
    conn = get_conn()
    q = "SELECT * FROM notifications"
    if unread_only:
        q += " WHERE read = 0"
    q += " ORDER BY id DESC LIMIT ?"
    return [dict(r) for r in conn.execute(q, (limit,)).fetchall()]


def unread_count() -> int:
    conn = get_conn()
    return conn.execute("SELECT COUNT(*) AS c FROM notifications WHERE read = 0").fetchone()["c"]


def mark_notification_read(notif_id: int) -> None:
    conn = get_conn()
    conn.execute("UPDATE notifications SET read = 1 WHERE id = ?", (notif_id,))
    conn.commit()
    _bump()


def mark_all_read() -> None:
    conn = get_conn()
    conn.execute("UPDATE notifications SET read = 1 WHERE read = 0")
    conn.commit()
    _bump()


def clear_notifications() -> None:
    conn = get_conn()
    conn.execute("DELETE FROM notifications")
    conn.commit()
    _bump()


# ── Sync log ──────────────────────────────────────────────────────────────────
def start_sync(source: str) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO sync_log (started_at, status, source) VALUES (?, 'running', ?)",
        (_now(), source),
    )
    conn.commit()
    return int(cur.lastrowid)


def finish_sync(sync_id: int, status: str, campaigns: int = 0, metrics: int = 0,
                leads: int = 0, ran_ai: bool = False, message: str = "") -> None:
    conn = get_conn()
    conn.execute(
        """UPDATE sync_log SET finished_at=?, status=?, campaigns=?, metrics=?, leads=?,
               ran_ai=?, message=? WHERE id=?""",
        (_now(), status, campaigns, metrics, leads, 1 if ran_ai else 0, message, sync_id),
    )
    conn.commit()
    if status in ("success", "partial"):
        set_meta("last_sync_at", _now())
        set_meta("last_sync_status", status)
    _bump()


def last_sync() -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM sync_log WHERE status != 'running' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return dict(row) if row else None


def recent_syncs(limit: int = 12) -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM sync_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]
