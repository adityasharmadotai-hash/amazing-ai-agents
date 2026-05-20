"""
database.py — Supabase storage for meeting notes and analytics.

Run this SQL once in Supabase SQL Editor:
────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS meetings (
    id              BIGSERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    filename        TEXT,
    transcript      TEXT,
    analysis        JSONB,
    follow_up_email TEXT,
    duration_secs   REAL,
    word_count      INTEGER,
    attendee_count  INTEGER,
    sentiment       TEXT,
    file_size_mb    REAL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

GRANT ALL ON meetings TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
ALTER TABLE meetings DISABLE ROW LEVEL SECURITY;
────────────────────────────────────────────────────────
"""

import json
import os
import streamlit as st


@st.cache_resource
def _get_client_cached(url: str, key: str):
    from supabase import create_client
    return create_client(url, key)


def _db():
    try:
        url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY", "")
    except Exception:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        return None
    try:
        return _get_client_cached(url, key)
    except Exception:
        return None


def is_configured() -> bool:
    return _db() is not None


def init_db():
    """No-op — tables created via SQL Editor."""
    pass


def _ts(ts: str) -> str:
    return ts[:16].replace("T", " ") if ts else ""


# ─────────────────────────────────────────────
# Save meeting
# ─────────────────────────────────────────────

def save_meeting(
    title: str,
    filename: str,
    transcript: str,
    analysis: dict,
    follow_up_email: str,
    duration_secs: float,
    word_count: int,
    file_size_mb: float,
) -> int:
    db = _db()
    if not db:
        return -1
    try:
        attendees = analysis.get("attendees", [])
        sentiment = analysis.get("sentiment", "Neutral")
        resp = (
            db.table("meetings")
            .insert({
                "title": title,
                "filename": filename,
                "transcript": transcript[:15000],
                "analysis": analysis,
                "follow_up_email": follow_up_email,
                "duration_secs": duration_secs,
                "word_count": word_count,
                "attendee_count": len(attendees),
                "sentiment": sentiment,
                "file_size_mb": file_size_mb,
            })
            .execute()
        )
        return resp.data[0]["id"] if resp.data else -1
    except Exception:
        return -1


# ─────────────────────────────────────────────
# Fetch meetings
# ─────────────────────────────────────────────

def get_all_meetings(limit: int = 50) -> list:
    db = _db()
    if not db:
        return []
    try:
        resp = (
            db.table("meetings")
            .select("id, title, filename, duration_secs, word_count, attendee_count, sentiment, file_size_mb, created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = resp.data or []
        for r in rows:
            r["created_at"] = _ts(r.get("created_at", ""))
        return rows
    except Exception:
        return []


def get_meeting_by_id(meeting_id: int) -> dict | None:
    db = _db()
    if not db:
        return None
    try:
        resp = db.table("meetings").select("*").eq("id", meeting_id).execute()
        if not resp.data:
            return None
        r = resp.data[0]
        if not isinstance(r.get("analysis"), dict):
            r["analysis"] = {}
        r["created_at"] = _ts(r.get("created_at", ""))
        return r
    except Exception:
        return None


def search_meetings(query: str) -> list:
    """Search meetings by title (case-insensitive)."""
    db = _db()
    if not db:
        return []
    try:
        resp = (
            db.table("meetings")
            .select("id, title, filename, duration_secs, word_count, sentiment, created_at")
            .ilike("title", f"%{query}%")
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        rows = resp.data or []
        for r in rows:
            r["created_at"] = _ts(r.get("created_at", ""))
        return rows
    except Exception:
        return []


def delete_meeting(meeting_id: int):
    db = _db()
    if not db:
        return
    try:
        db.table("meetings").delete().eq("id", meeting_id).execute()
    except Exception:
        pass


# ─────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────

def get_analytics() -> dict:
    db = _db()
    if not db:
        return _empty_analytics()
    try:
        resp = db.table("meetings").select(
            "id, duration_secs, word_count, attendee_count, sentiment, created_at"
        ).execute()
        rows = resp.data or []

        if not rows:
            return _empty_analytics()

        total = len(rows)
        total_duration = sum(r.get("duration_secs", 0) or 0 for r in rows)
        total_words = sum(r.get("word_count", 0) or 0 for r in rows)
        avg_attendees = round(sum(r.get("attendee_count", 0) or 0 for r in rows) / total, 1)

        # Sentiment breakdown
        sentiment_counts = {}
        for r in rows:
            s = r.get("sentiment", "Neutral") or "Neutral"
            sentiment_counts[s] = sentiment_counts.get(s, 0) + 1

        # Daily activity
        daily = {}
        for r in rows:
            ts = (r.get("created_at") or "")[:10]
            if ts:
                daily[ts] = daily.get(ts, 0) + 1

        # Duration distribution buckets
        dur_buckets = {"< 15 min": 0, "15-30 min": 0, "30-60 min": 0, "> 60 min": 0}
        for r in rows:
            d = (r.get("duration_secs") or 0) / 60
            if d < 15:
                dur_buckets["< 15 min"] += 1
            elif d < 30:
                dur_buckets["15-30 min"] += 1
            elif d < 60:
                dur_buckets["30-60 min"] += 1
            else:
                dur_buckets["> 60 min"] += 1

        return {
            "total_meetings": total,
            "total_duration_mins": round(total_duration / 60, 1),
            "avg_duration_mins": round(total_duration / 60 / total, 1) if total else 0,
            "total_words": total_words,
            "avg_attendees": avg_attendees,
            "sentiment_counts": sentiment_counts,
            "daily_counts": daily,
            "duration_buckets": dur_buckets,
        }
    except Exception:
        return _empty_analytics()


def _empty_analytics() -> dict:
    return {
        "total_meetings": 0,
        "total_duration_mins": 0,
        "avg_duration_mins": 0,
        "total_words": 0,
        "avg_attendees": 0,
        "sentiment_counts": {},
        "daily_counts": {},
        "duration_buckets": {},
    }
