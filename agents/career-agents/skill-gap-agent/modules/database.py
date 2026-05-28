"""
modules/database.py
-------------------
SQLite-backed persistence for profiles, analyses, and progress tracking.
Zero external services — the DB file lives in ./data/skill_gap.db.
"""

from __future__ import annotations
import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/skill_gap.db")


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all tables if they don't exist."""
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS profiles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at  TEXT    NOT NULL,
            name        TEXT,
            target_role TEXT    NOT NULL,
            industry    TEXT    NOT NULL,
            resume_text TEXT,
            linkedin_text TEXT,
            parsed_data TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS analyses (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at      TEXT    NOT NULL,
            profile_id      INTEGER NOT NULL,
            readiness_score INTEGER NOT NULL,
            skill_data      TEXT    NOT NULL,
            gap_data        TEXT    NOT NULL,
            roadmap_data    TEXT    NOT NULL,
            courses_data    TEXT    NOT NULL,
            interview_data  TEXT    NOT NULL,
            FOREIGN KEY (profile_id) REFERENCES profiles(id)
        );

        CREATE TABLE IF NOT EXISTS progress (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at  TEXT    NOT NULL,
            analysis_id INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            task_label  TEXT    NOT NULL,
            completed   INTEGER DEFAULT 0,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id)
        );
    """)
    conn.commit()
    conn.close()


# ── Profiles ─────────────────────────────────────────────────────────────────

def save_profile(
    target_role: str,
    industry: str,
    parsed_data: dict,
    resume_text: str = "",
    linkedin_text: str = "",
    name: str = "",
) -> int:
    conn = _connect()
    cur = conn.execute(
        """INSERT INTO profiles
           (created_at, name, target_role, industry, resume_text, linkedin_text, parsed_data)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now().isoformat(),
            name,
            target_role,
            industry,
            resume_text,
            linkedin_text,
            json.dumps(parsed_data),
        ),
    )
    profile_id = cur.lastrowid
    conn.commit()
    conn.close()
    return profile_id


def get_profiles() -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM profiles ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["parsed_data"] = json.loads(d["parsed_data"])
        result.append(d)
    return result


def get_profile(profile_id: int) -> dict | None:
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM profiles WHERE id = ?", (profile_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    d = dict(row)
    d["parsed_data"] = json.loads(d["parsed_data"])
    return d


# ── Analyses ──────────────────────────────────────────────────────────────────

def save_analysis(
    profile_id: int,
    readiness_score: int,
    skill_data: dict,
    gap_data: dict,
    roadmap_data: dict,
    courses_data: dict,
    interview_data: dict,
) -> int:
    conn = _connect()
    cur = conn.execute(
        """INSERT INTO analyses
           (created_at, profile_id, readiness_score, skill_data, gap_data,
            roadmap_data, courses_data, interview_data)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now().isoformat(),
            profile_id,
            readiness_score,
            json.dumps(skill_data),
            json.dumps(gap_data),
            json.dumps(roadmap_data),
            json.dumps(courses_data),
            json.dumps(interview_data),
        ),
    )
    analysis_id = cur.lastrowid
    conn.commit()
    conn.close()
    return analysis_id


def get_analyses(profile_id: int | None = None) -> list[dict]:
    conn = _connect()
    if profile_id:
        rows = conn.execute(
            "SELECT * FROM analyses WHERE profile_id=? ORDER BY created_at DESC",
            (profile_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM analyses ORDER BY created_at DESC"
        ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        for key in ("skill_data", "gap_data", "roadmap_data", "courses_data", "interview_data"):
            d[key] = json.loads(d[key])
        result.append(d)
    return result


def get_analysis(analysis_id: int) -> dict | None:
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    d = dict(row)
    for key in ("skill_data", "gap_data", "roadmap_data", "courses_data", "interview_data"):
        d[key] = json.loads(d[key])
    return d


# ── Progress Tracking ─────────────────────────────────────────────────────────

def save_progress_tasks(analysis_id: int, tasks: list[dict]) -> None:
    """Bulk-insert weekly tasks."""
    conn = _connect()
    conn.execute("DELETE FROM progress WHERE analysis_id = ?", (analysis_id,))
    now = datetime.now().isoformat()
    conn.executemany(
        """INSERT INTO progress (created_at, analysis_id, week_number, task_label, completed)
           VALUES (?, ?, ?, ?, 0)""",
        [(now, analysis_id, t["week"], t["label"]) for t in tasks],
    )
    conn.commit()
    conn.close()


def toggle_task(task_id: int, completed: bool) -> None:
    conn = _connect()
    conn.execute(
        "UPDATE progress SET completed = ? WHERE id = ?",
        (1 if completed else 0, task_id),
    )
    conn.commit()
    conn.close()


def get_progress(analysis_id: int) -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM progress WHERE analysis_id = ? ORDER BY week_number, id",
        (analysis_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    conn = _connect()
    profiles = conn.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
    analyses = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
    avg_score = conn.execute(
        "SELECT AVG(readiness_score) FROM analyses"
    ).fetchone()[0]
    conn.close()
    return {
        "profiles": profiles,
        "analyses": analyses,
        "avg_score": round(avg_score or 0, 1),
    }
