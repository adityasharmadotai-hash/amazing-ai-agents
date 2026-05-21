"""
database.py — Optional Supabase persistence for conversation history and tasks.

Run in Supabase SQL Editor:
────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS conversations (
    id          BIGSERIAL PRIMARY KEY,
    session_id  TEXT,
    role        TEXT,
    content     TEXT,
    intent_type TEXT,
    audio_used  BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS saved_tasks (
    id          BIGSERIAL PRIMARY KEY,
    task_id     TEXT,
    task        TEXT,
    deadline    TEXT,
    priority    TEXT,
    status      TEXT DEFAULT 'pending',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS saved_notes (
    id          BIGSERIAL PRIMARY KEY,
    note_id     TEXT,
    title       TEXT,
    content     TEXT,
    tag         TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

GRANT ALL ON conversations, saved_tasks, saved_notes TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
ALTER TABLE conversations DISABLE ROW LEVEL SECURITY;
ALTER TABLE saved_tasks DISABLE ROW LEVEL SECURITY;
ALTER TABLE saved_notes DISABLE ROW LEVEL SECURITY;
────────────────────────────────────────────────
"""

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


def _ts(ts: str) -> str:
    return ts[:16].replace("T", " ") if ts else ""


def save_message(session_id: str, role: str, content: str, intent_type: str = "CHAT", audio_used: bool = False):
    db = _db()
    if not db:
        return
    try:
        db.table("conversations").insert({
            "session_id": session_id,
            "role": role,
            "content": content[:2000],
            "intent_type": intent_type,
            "audio_used": audio_used,
        }).execute()
    except Exception:
        pass


def get_conversation_history(session_id: str, limit: int = 50) -> list:
    db = _db()
    if not db:
        return []
    try:
        resp = (
            db.table("conversations")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


def get_analytics_from_db() -> dict:
    db = _db()
    if not db:
        return {}
    try:
        resp = db.table("conversations").select("role, intent_type, audio_used, created_at").execute()
        rows = resp.data or []
        total = len(rows)
        user_msgs = sum(1 for r in rows if r["role"] == "user")
        audio_msgs = sum(1 for r in rows if r.get("audio_used"))
        intent_counts = {}
        for r in rows:
            it = r.get("intent_type", "CHAT")
            intent_counts[it] = intent_counts.get(it, 0) + 1
        daily = {}
        for r in rows:
            day = (r.get("created_at") or "")[:10]
            if day:
                daily[day] = daily.get(day, 0) + 1
        return {
            "total_messages": total,
            "user_messages": user_msgs,
            "audio_messages": audio_msgs,
            "intent_counts": intent_counts,
            "daily_counts": daily,
        }
    except Exception:
        return {}
