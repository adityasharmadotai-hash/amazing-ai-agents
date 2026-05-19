-- ─────────────────────────────────────────────────────────────────────
-- AI Content Repurposing Agent — Supabase Schema
-- ─────────────────────────────────────────────────────────────────────
-- Run ONCE in: https://supabase.com/dashboard → SQL Editor → New Query
-- ─────────────────────────────────────────────────────────────────────

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

-- Permissions for anon key
GRANT ALL ON content_history TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- Disable RLS for simplicity
ALTER TABLE content_history DISABLE ROW LEVEL SECURITY;
