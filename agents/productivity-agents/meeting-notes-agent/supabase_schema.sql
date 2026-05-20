-- ─────────────────────────────────────────────────────────────────────
-- AI Meeting Notes Agent — Supabase Schema
-- ─────────────────────────────────────────────────────────────────────
-- Run ONCE in: https://supabase.com/dashboard → SQL Editor → New Query
-- ─────────────────────────────────────────────────────────────────────

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

-- Permissions for anon key
GRANT ALL ON meetings TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- Disable RLS for simplicity
ALTER TABLE meetings DISABLE ROW LEVEL SECURITY;
