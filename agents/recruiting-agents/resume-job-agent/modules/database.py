"""
database.py — Supabase (PostgreSQL) storage for resumes, jobs, and analyses.

Drop-in replacement for the old SQLite module.
Every public function keeps the exact same signature and return shape
so app.py needs zero changes.

Supabase table schemas (run once in the Supabase SQL Editor):
────────────────────────────────────────────────────────────────
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
────────────────────────────────────────────────────────────────
"""

import json
import os

import streamlit as st
from supabase import Client, create_client


# ─────────────────────────────────────────────
# Client
# ─────────────────────────────────────────────

@st.cache_resource
def get_client() -> Client:
    """
    Return a cached Supabase client.
    Reads from st.secrets (Streamlit Cloud) or env vars (local .env).
    """
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        raise RuntimeError(
            "Supabase credentials missing. "
            "Set SUPABASE_URL and SUPABASE_KEY in .streamlit/secrets.toml or your .env file."
        )
    return create_client(url, key)


def _db() -> Client:
    return get_client()


# ─────────────────────────────────────────────
# init_db — no-op for Supabase
# ─────────────────────────────────────────────

def init_db():
    """No-op: tables are created once in Supabase SQL Editor. Called for compatibility."""
    pass


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _parse_json_fields(row: dict, fields: list) -> dict:
    """JSONB columns come back as dicts; coerce strings just in case."""
    for f in fields:
        val = row.get(f)
        if isinstance(val, str):
            try:
                row[f] = json.loads(val)
            except Exception:
                row[f] = {}
        elif val is None:
            row[f] = {}
    return row


def _short_ts(ts: str) -> str:
    """Trim ISO timestamp to 'YYYY-MM-DD HH:MM'."""
    if not ts:
        return ""
    return ts[:16].replace("T", " ")


# ─────────────────────────────────────────────
# Resumes
# ─────────────────────────────────────────────

def save_resume(name: str, filename: str, raw_text: str, parsed_data: dict) -> int:
    resp = (
        _db()
        .table("resumes")
        .insert({
            "name": name,
            "filename": filename,
            "raw_text": raw_text,
            "parsed_data": parsed_data,
        })
        .execute()
    )
    return resp.data[0]["id"]


def get_all_resumes() -> list:
    resp = (
        _db()
        .table("resumes")
        .select("id, name, filename, created_at")
        .order("created_at", desc=True)
        .execute()
    )
    rows = resp.data or []
    for r in rows:
        r["created_at"] = _short_ts(r.get("created_at", ""))
    return rows


def get_resume_by_id(resume_id: int):
    resp = (
        _db()
        .table("resumes")
        .select("*")
        .eq("id", resume_id)
        .execute()
    )
    if not resp.data:
        return None
    row = resp.data[0]
    if not isinstance(row.get("parsed_data"), dict):
        row["parsed_data"] = {}
    row["created_at"] = _short_ts(row.get("created_at", ""))
    return row


def delete_resume(resume_id: int):
    """ON DELETE CASCADE handles related rows automatically."""
    _db().table("resumes").delete().eq("id", resume_id).execute()


# ─────────────────────────────────────────────
# Job Analyses
# ─────────────────────────────────────────────

def save_job_analysis(
    resume_id: int,
    job_title: str,
    company_name: str,
    job_description: str,
    match_result: dict,
    ats_result: dict,
) -> int:
    resp = (
        _db()
        .table("job_analyses")
        .insert({
            "resume_id": resume_id,
            "job_title": job_title,
            "company_name": company_name,
            "job_description": job_description,
            "match_result": match_result,
            "ats_result": ats_result,
        })
        .execute()
    )
    return resp.data[0]["id"]


def get_analyses_for_resume(resume_id: int) -> list:
    resp = (
        _db()
        .table("job_analyses")
        .select("*")
        .eq("resume_id", resume_id)
        .order("created_at", desc=True)
        .execute()
    )
    rows = resp.data or []
    for r in rows:
        _parse_json_fields(r, ["match_result", "ats_result"])
        r["created_at"] = _short_ts(r.get("created_at", ""))
    return rows


def get_all_analyses() -> list:
    """Fetch all analyses with candidate name via Supabase nested select."""
    resp = (
        _db()
        .table("job_analyses")
        .select("*, resumes(name)")
        .order("created_at", desc=True)
        .execute()
    )
    rows = resp.data or []
    result = []
    for r in rows:
        _parse_json_fields(r, ["match_result", "ats_result"])
        r["created_at"] = _short_ts(r.get("created_at", ""))
        r["candidate_name"] = (r.pop("resumes", None) or {}).get("name", "")
        result.append(r)
    return result


# ─────────────────────────────────────────────
# Cover Letters
# ─────────────────────────────────────────────

def save_cover_letter(
    resume_id: int,
    job_analysis_id: int,
    company_name: str,
    job_title: str,
    content: str,
    tone: str,
) -> int:
    resp = (
        _db()
        .table("cover_letters")
        .insert({
            "resume_id": resume_id,
            "job_analysis_id": job_analysis_id,
            "company_name": company_name,
            "job_title": job_title,
            "content": content,
            "tone": tone,
        })
        .execute()
    )
    return resp.data[0]["id"]


def get_cover_letters_for_resume(resume_id: int) -> list:
    resp = (
        _db()
        .table("cover_letters")
        .select("*")
        .eq("resume_id", resume_id)
        .order("created_at", desc=True)
        .execute()
    )
    rows = resp.data or []
    for r in rows:
        r["created_at"] = _short_ts(r.get("created_at", ""))
    return rows


# ─────────────────────────────────────────────
# Interview Questions
# ─────────────────────────────────────────────

def save_interview_questions(resume_id: int, job_analysis_id: int, questions_data: dict) -> int:
    resp = (
        _db()
        .table("interview_questions")
        .insert({
            "resume_id": resume_id,
            "job_analysis_id": job_analysis_id,
            "questions_data": questions_data,
        })
        .execute()
    )
    return resp.data[0]["id"]


def get_interview_questions_for_resume(resume_id: int) -> list:
    resp = (
        _db()
        .table("interview_questions")
        .select("*")
        .eq("resume_id", resume_id)
        .order("created_at", desc=True)
        .execute()
    )
    rows = resp.data or []
    for r in rows:
        _parse_json_fields(r, ["questions_data"])
        r["created_at"] = _short_ts(r.get("created_at", ""))
    return rows


# ─────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────

def get_dashboard_stats() -> dict:
    db = _db()

    total_resumes       = len((db.table("resumes").select("id").execute()).data or [])
    total_analyses      = len((db.table("job_analyses").select("id").execute()).data or [])
    total_cover_letters = len((db.table("cover_letters").select("id").execute()).data or [])

    analyses_resp = db.table("job_analyses").select("match_result").execute()
    scores = []
    for row in (analyses_resp.data or []):
        mr = row.get("match_result") or {}
        if isinstance(mr, str):
            try:
                mr = json.loads(mr)
            except Exception:
                continue
        if "match_score" in mr:
            scores.append(mr["match_score"])

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    recent_resp = (
        db
        .table("job_analyses")
        .select("company_name, job_title, match_result, created_at, resumes(name)")
        .order("created_at", desc=True)
        .limit(5)
        .execute()
    )
    recent = []
    for row in (recent_resp.data or []):
        _parse_json_fields(row, ["match_result"])
        row["name"] = (row.pop("resumes", None) or {}).get("name", "")
        row["created_at"] = _short_ts(row.get("created_at", ""))
        recent.append(row)

    return {
        "total_resumes": total_resumes,
        "total_analyses": total_analyses,
        "total_cover_letters": total_cover_letters,
        "avg_match_score": avg_score,
        "all_scores": scores,
        "recent_analyses": recent,
    }
