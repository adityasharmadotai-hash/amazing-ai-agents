"""Supabase persistence via PostgREST (raw httpx).

We talk to PostgREST directly instead of the supabase-py client because the
client bundled an older gotrue/postgrest that rejects the new `sb_secret_` /
`sb_publishable_` API-key format with a misleading "Invalid API key". Raw REST
accepts the new keys and needs no extra dependency.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx

from . import config

log = logging.getLogger(__name__)

_TABLE = "layoff_posts"

# Only a real YYYY-MM-DD survives into the `date` column. The LLM sometimes
# returns "last week", "September 2025", "2025-09", "2024-13-99" or "" — any of
# which makes PostgREST reject the WHOLE batch — so we validate with
# date.fromisoformat and coerce anything invalid to null.
def _clean_date(v: Any) -> str | None:
    if not isinstance(v, str):
        return None
    v = v.strip()
    try:
        return date.fromisoformat(v).isoformat()
    except ValueError:
        return None


def _clean_int(v: Any) -> int | None:
    try:
        return None if v in (None, "") else int(v)
    except (ValueError, TypeError):
        return None


def _clean_float(v: Any) -> float | None:
    try:
        return None if v in (None, "") else float(v)
    except (ValueError, TypeError):
        return None


def normalize_url(u: str | None) -> str | None:
    """Strip tracking query params + fragment so the same LinkedIn post always
    dedupes to one row (the activity id in the path is the stable key)."""
    if not u:
        return u
    p = urlsplit(u.strip())
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), "", ""))


def _base() -> str:
    if not (config.SUPABASE_URL and config.SUPABASE_SERVICE_KEY):
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_KEY are not set.")
    return config.SUPABASE_URL.rstrip("/") + "/rest/v1"


def _headers(extra: dict | None = None) -> dict:
    key = config.SUPABASE_SERVICE_KEY
    h = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


_COMPANIES_TABLE = "companies"

_FIELDS = ("source_url", "source", "company", "company_key", "poster_role",
           "person_name", "role_hint", "country", "is_us", "headcount", "location",
           "event_date", "open_to_work", "is_qualified", "summary", "confidence")

# Fields written to the company-rollup table (see agent/companies.py).
_COMPANY_FIELDS = ("company_key", "company_name", "employee_posts",
                   "recruiter_posts", "founder_posts", "announcement_posts",
                   "news_posts", "total_posts", "confidence", "locations")


def upsert_records(records: list[dict[str, Any]]) -> int:
    """Upsert on source_url. Returns the number of rows sent."""
    rows = [
        {k: r.get(k) for k in _FIELDS}
        for r in records
        if r.get("source_url")
    ]
    # normalize URLs and drop duplicates within this batch
    seen: set[str] = set()
    deduped = []
    for row in rows:
        row["source_url"] = normalize_url(row.get("source_url"))
        row["open_to_work"] = bool(row.get("open_to_work"))
        row["is_qualified"] = bool(row.get("is_qualified"))
        row["is_us"] = bool(row.get("is_us"))
        # Coerce typed columns so one bad LLM value can't fail the whole batch.
        row["event_date"] = _clean_date(row.get("event_date"))
        row["headcount"] = _clean_int(row.get("headcount"))
        row["confidence"] = _clean_float(row.get("confidence"))
        if row["source_url"] in seen:
            continue
        seen.add(row["source_url"])
        deduped.append(row)
    rows = deduped
    if not rows:
        return 0

    url = f"{_base()}/{_TABLE}?on_conflict=source_url"
    headers = _headers({"Prefer": "resolution=merge-duplicates,return=minimal"})
    resp = httpx.post(url, json=rows, headers=headers, timeout=30)
    if resp.status_code >= 300:
        # Graceful fallback: if the Company Discovery columns haven't been migrated
        # yet (supabase/companies.sql), drop them and retry so core scanning still
        # works — you just don't get the company rollup until you run the migration.
        body = resp.text[:300]
        if ("company_key" in body or "poster_role" in body
                or "column" in body.lower()):
            log.warning("Company columns missing — run supabase/companies.sql. "
                        "Storing posts WITHOUT company_key/poster_role for now. "
                        "Supabase said: %s", body)
            slim = [{k: v for k, v in r.items()
                     if k not in ("company_key", "poster_role")} for r in rows]
            resp = httpx.post(url, json=slim, headers=headers, timeout=30)
            if resp.status_code < 300:
                log.info("Stored %d records (without company fields)", len(slim))
                return len(slim)
        raise RuntimeError(f"Supabase upsert failed {resp.status_code}: {resp.text[:200]}")
    log.info("Stored %d layoff records", len(rows))
    return len(rows)


# ── Company rollup (Company Discovery Engine) ────────────────────────────────
def posts_for_rollup() -> list[dict]:
    """Every stored post with just the fields the company rollup needs (no dedup,
    all rows). Used by agent.companies.rebuild()."""
    params = {"select": "company_key,poster_role,company,location", "limit": "10000"}
    resp = httpx.get(f"{_base()}/{_TABLE}", params=params, headers=_headers(), timeout=30)
    if resp.status_code >= 300:
        raise RuntimeError(f"Supabase rollup select failed {resp.status_code}: {resp.text[:200]}")
    return resp.json()


def upsert_companies(rows: list[dict[str, Any]]) -> int:
    """Upsert the company rollup rows (on company_key). Returns rows sent."""
    payload = [{k: r.get(k) for k in _COMPANY_FIELDS}
               for r in rows if r.get("company_key")]
    for p in payload:
        p["confidence"] = _clean_float(p.get("confidence"))
        for c in ("employee_posts", "recruiter_posts", "founder_posts",
                  "announcement_posts", "news_posts", "total_posts"):
            p[c] = _clean_int(p.get(c)) or 0
    if not payload:
        return 0
    url = f"{_base()}/{_COMPANIES_TABLE}?on_conflict=company_key"
    headers = _headers({"Prefer": "resolution=merge-duplicates,return=minimal"})
    resp = httpx.post(url, json=payload, headers=headers, timeout=30)
    if resp.status_code >= 300:
        raise RuntimeError(f"Supabase companies upsert failed {resp.status_code}: {resp.text[:200]}")
    log.info("Rolled up %d companies", len(payload))
    return len(payload)


def list_companies(limit: int = 300, min_confidence: float | None = None) -> list[dict]:
    """Discovered companies, ranked by confidence then post volume."""
    params = {
        "select": "*",
        "order": "confidence.desc,total_posts.desc",
        "limit": str(limit),
    }
    if min_confidence is not None:
        params["confidence"] = f"gte.{min_confidence}"
    resp = httpx.get(f"{_base()}/{_COMPANIES_TABLE}", params=params,
                     headers=_headers(), timeout=30)
    if resp.status_code >= 300:
        raise RuntimeError(f"Supabase companies select failed {resp.status_code}: {resp.text[:200]}")
    return resp.json()


def list_records(limit: int = 200, company: str | None = None,
                 open_to_work: bool | None = None,
                 qualified: bool | None = None) -> list[dict]:
    params = {
        "select": "*",
        "order": "created_at.desc",
        "limit": str(limit),
    }
    if company:
        params["company"] = f"ilike.*{company}*"
    if open_to_work is not None:
        params["open_to_work"] = f"eq.{str(open_to_work).lower()}"
    if qualified is not None:
        params["is_qualified"] = f"eq.{str(qualified).lower()}"

    resp = httpx.get(f"{_base()}/{_TABLE}", params=params, headers=_headers(), timeout=30)
    if resp.status_code >= 300:
        raise RuntimeError(f"Supabase select failed {resp.status_code}: {resp.text[:200]}")
    rows = resp.json()
    # collapse the same person appearing in multiple posts (different URLs) —
    # keep the newest (rows are ordered created_at desc). Company/announcement
    # rows (no person_name) are never collapsed.
    seen: set = set()
    out = []
    for r in rows:
        name = (r.get("person_name") or "").strip().lower()
        key = (name, (r.get("company") or "").strip().lower())
        if name and key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def delete_all() -> int:
    """Delete EVERY row in the leads table. Returns the number deleted.

    Irreversible. PostgREST requires a filter for a DELETE, so we match all rows
    with id >= 0 (the identity column starts at 1).
    """
    url = f"{_base()}/{_TABLE}?id=gte.0"
    headers = _headers({"Prefer": "return=representation"})
    resp = httpx.delete(url, headers=headers, timeout=60)
    if resp.status_code >= 300:
        raise RuntimeError(f"Supabase delete failed {resp.status_code}: {resp.text[:200]}")
    try:
        return len(resp.json())
    except Exception:  # noqa: BLE001
        return 0


def table_exists() -> bool:
    """True if the layoff_posts table is reachable via PostgREST."""
    resp = httpx.get(f"{_base()}/{_TABLE}", params={"select": "id", "limit": "1"},
                     headers=_headers(), timeout=20)
    return resp.status_code < 300
