-- ─────────────────────────────────────────────────────────────────────
-- AI Resume & Job Match Agent — Supabase Schema
-- ─────────────────────────────────────────────────────────────────────
-- Run this ONCE in the Supabase SQL Editor:
--   https://supabase.com/dashboard → SQL Editor → New Query
--   Paste everything below and click Run ▶
-- ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS resumes (
    id          BIGSERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    filename    TEXT,
    raw_text    TEXT,
    parsed_data JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS job_analyses (
    id              BIGSERIAL PRIMARY KEY,
    resume_id       BIGINT REFERENCES resumes(id) ON DELETE CASCADE,
    job_title       TEXT,
    company_name    TEXT,
    job_description TEXT,
    match_result    JSONB,
    ats_result      JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cover_letters (
    id              BIGSERIAL PRIMARY KEY,
    resume_id       BIGINT REFERENCES resumes(id) ON DELETE CASCADE,
    job_analysis_id BIGINT,
    company_name    TEXT,
    job_title       TEXT,
    content         TEXT,
    tone            TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS interview_questions (
    id              BIGSERIAL PRIMARY KEY,
    resume_id       BIGINT REFERENCES resumes(id) ON DELETE CASCADE,
    job_analysis_id BIGINT,
    questions_data  JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (RLS) — recommended for production
-- Uncomment and customise these policies if you add user auth:
-- ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE job_analyses ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE cover_letters ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE interview_questions ENABLE ROW LEVEL SECURITY;

-- Grant anon role access (required for the public anon key to work)
GRANT ALL ON resumes              TO anon, authenticated;
GRANT ALL ON job_analyses         TO anon, authenticated;
GRANT ALL ON cover_letters        TO anon, authenticated;
GRANT ALL ON interview_questions  TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
