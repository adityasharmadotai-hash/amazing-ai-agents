"""
database.py — Supabase storage for content history and analytics.

Run this SQL once in Supabase SQL Editor:
────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS content_history (
    id              BIGSERIAL PRIMARY KEY,
    video_id        TEXT NOT NULL,
    video_url       TEXT,
    video_title     TEXT,
    video_summary   TEXT,
    transcript      TEXT,
    duration_mins   REAL,
    word_count      INTEGER,
    style           TEXT,
    content_type    TEXT,
    generated_text  TEXT,
    char_count      INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

GRANT ALL ON content_history TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
ALTER TABLE content_history DISABLE ROW LEVEL SECURITY;
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


def _short_ts(ts: str) -> str:
    return ts[:16].replace("T", " ") if ts else ""


# ─────────────────────────────────────────────
# Save content
# ─────────────────────────────────────────────

def save_content(
    video_id: str,
    video_url: str,
    video_title: str,
    video_summary: str,
    transcript: str,
    duration_mins: float,
    word_count: int,
    style: str,
    content_type: str,
    generated_text: str,
) -> int:
    db = _db()
    if not db:
        return -1
    try:
        resp = (
            db.table("content_history")
            .insert({
                "video_id": video_id,
                "video_url": video_url,
                "video_title": video_title,
                "video_summary": video_summary,
                "transcript": transcript[:10000],  # cap at 10k chars
                "duration_mins": duration_mins,
                "word_count": word_count,
                "style": style,
                "content_type": content_type,
                "generated_text": generated_text,
                "char_count": len(generated_text),
            })
            .execute()
        )
        return resp.data[0]["id"] if resp.data else -1
    except Exception:
        return -1


# ─────────────────────────────────────────────
# Fetch history
# ─────────────────────────────────────────────

def get_all_history(limit: int = 100) -> list:
    db = _db()
    if not db:
        return []
    try:
        resp = (
            db.table("content_history")
            .select("id, video_id, video_title, video_summary, style, content_type, char_count, created_at, video_url")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = resp.data or []
        for r in rows:
            r["created_at"] = _short_ts(r.get("created_at", ""))
        return rows
    except Exception:
        return []


def get_content_by_id(row_id: int) -> dict | None:
    db = _db()
    if not db:
        return None
    try:
        resp = (
            db.table("content_history")
            .select("*")
            .eq("id", row_id)
            .execute()
        )
        if not resp.data:
            return None
        r = resp.data[0]
        r["created_at"] = _short_ts(r.get("created_at", ""))
        return r
    except Exception:
        return None


def get_history_for_video(video_id: str) -> list:
    db = _db()
    if not db:
        return []
    try:
        resp = (
            db.table("content_history")
            .select("*")
            .eq("video_id", video_id)
            .order("created_at", desc=True)
            .execute()
        )
        rows = resp.data or []
        for r in rows:
            r["created_at"] = _short_ts(r.get("created_at", ""))
        return rows
    except Exception:
        return []


def delete_content(row_id: int):
    db = _db()
    if not db:
        return
    try:
        db.table("content_history").delete().eq("id", row_id).execute()
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
        resp = db.table("content_history").select(
            "id, video_id, video_title, style, content_type, char_count, created_at"
        ).execute()
        rows = resp.data or []

        if not rows:
            return _empty_analytics()

        total_pieces = len(rows)
        unique_videos = len(set(r["video_id"] for r in rows))
        total_chars = sum(r.get("char_count", 0) for r in rows)

        # Content type breakdown
        ct_counts = {}
        for r in rows:
            ct = r.get("content_type", "unknown")
            ct_counts[ct] = ct_counts.get(ct, 0) + 1

        # Style breakdown
        style_counts = {}
        for r in rows:
            s = r.get("style", "unknown")
            style_counts[s] = style_counts.get(s, 0) + 1

        # Recent 7 days activity (by day)
        from datetime import datetime, timedelta
        daily = {}
        for r in rows:
            ts = r.get("created_at", "")[:10]
            if ts:
                daily[ts] = daily.get(ts, 0) + 1

        # Top videos by content count
        video_counts = {}
        video_titles = {}
        for r in rows:
            vid = r.get("video_id", "")
            video_counts[vid] = video_counts.get(vid, 0) + 1
            if vid not in video_titles:
                video_titles[vid] = r.get("video_title", vid)

        top_videos = sorted(video_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_pieces": total_pieces,
            "unique_videos": unique_videos,
            "total_chars": total_chars,
            "content_type_counts": ct_counts,
            "style_counts": style_counts,
            "daily_counts": daily,
            "top_videos": [(video_titles.get(vid, vid), count) for vid, count in top_videos],
        }
    except Exception:
        return _empty_analytics()


def _empty_analytics() -> dict:
    return {
        "total_pieces": 0,
        "unique_videos": 0,
        "total_chars": 0,
        "content_type_counts": {},
        "style_counts": {},
        "daily_counts": {},
        "top_videos": [],
    }
