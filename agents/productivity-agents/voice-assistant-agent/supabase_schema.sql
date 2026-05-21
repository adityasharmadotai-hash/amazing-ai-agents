-- ─────────────────────────────────────────────────────────────────────
-- ARIA Voice Assistant Agent — Supabase Schema
-- ─────────────────────────────────────────────────────────────────────
-- Run ONCE in: Supabase Dashboard → SQL Editor → New Query → Run ▶
-- ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS conversations (
    id          BIGSERIAL PRIMARY KEY,
    session_id  TEXT,
    role        TEXT,
    content     TEXT,
    intent_type TEXT DEFAULT 'CHAT',
    audio_used  BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS saved_tasks (
    id           BIGSERIAL PRIMARY KEY,
    task_id      TEXT,
    task         TEXT,
    deadline     TEXT,
    priority     TEXT DEFAULT 'Medium',
    status       TEXT DEFAULT 'pending',
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS saved_notes (
    id         BIGSERIAL PRIMARY KEY,
    note_id    TEXT,
    title      TEXT,
    content    TEXT,
    tag        TEXT DEFAULT 'General',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Permissions
GRANT ALL ON conversations, saved_tasks, saved_notes TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- Disable RLS (simple setup)
ALTER TABLE conversations DISABLE ROW LEVEL SECURITY;
ALTER TABLE saved_tasks   DISABLE ROW LEVEL SECURITY;
ALTER TABLE saved_notes   DISABLE ROW LEVEL SECURITY;
