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


# Cloudflare gateway codes that mean the Supabase ORIGIN was unreachable. On a
# free project this is almost always a PAUSED project (they pause after ~1 week
# idle). PostgREST never returns these — Cloudflare does, with an HTML error
# page, so dumping the body at the user is useless.
_UNREACHABLE_STATUS = {520, 521, 522, 523, 524, 525, 526, 527, 530}


def _is_missing_column(resp: httpx.Response, column: str | None = None) -> bool:
    """True if a PostgREST response is the 'column does not exist' error (42703).

    Pass `column` to require that specific column be the one missing.
    """
    try:
        body = resp.json()
    except Exception:  # noqa: BLE001 — non-JSON (e.g. HTML) body
        return False
    if not isinstance(body, dict) or body.get("code") != "42703":
        return False
    return column is None or column in (body.get("message") or "")


def _fail(action: str, resp: httpx.Response) -> RuntimeError:
    """Build a clean, actionable error from a non-2xx PostgREST response.

    Supabase sits behind Cloudflare, so a paused/down project returns a 52x
    status with a full HTML error page. We detect that and explain what to do
    instead of surfacing raw HTML. We also detect schema drift (a column the
    code expects that the table doesn't have yet).
    """
    status = resp.status_code
    body = (resp.text or "").strip()
    looks_html = body[:15].lower().startswith(("<!doctype", "<html"))
    if status in _UNREACHABLE_STATUS or (status >= 500 and looks_html):
        return RuntimeError(
            f"Supabase is unreachable (HTTP {status}). The project is most likely "
            "PAUSED — free Supabase projects pause after ~1 week of inactivity. "
            "Open https://supabase.com/dashboard, select your project and click "
            "Restore/Resume, wait ~1 minute, then try again. (Also double-check "
            "SUPABASE_URL on the Settings page.)"
        )
    if _is_missing_column(resp):
        msg = ""
        try:
            msg = resp.json().get("message") or ""
        except Exception:  # noqa: BLE001
            pass
        return RuntimeError(
            f"Your Supabase schema is out of date ({msg}). Re-run the latest "
            "supabase/companies.sql (and supabase/layoff_posts.sql) in the Supabase "
            "SQL editor — they're idempotent and safe to re-run — then try again."
        )
    detail = "(HTML error page)" if looks_html else body[:200]
    return RuntimeError(f"Supabase {action} failed {status}: {detail}")


_COMPANIES_TABLE = "companies"

_FIELDS = ("source_url", "source", "company", "company_key", "poster_role",
           "person_name", "role_hint", "country", "is_us", "headcount", "location",
           "event_date", "open_to_work", "is_qualified", "summary", "confidence")

# Fields written to the company-rollup table (see agent/companies.py).
_COMPANY_FIELDS = ("company_key", "company_name", "employee_posts",
                   "recruiter_posts", "founder_posts", "announcement_posts",
                   "news_posts", "total_posts", "confidence", "locations",
                   "in_location", "in_location_posts")


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
        raise _fail("upsert", resp)
    log.info("Stored %d layoff records", len(rows))
    return len(rows)


# ── Company rollup (Company Discovery Engine) ────────────────────────────────
def posts_for_rollup() -> list[dict]:
    """Every stored post with just the fields the company rollup needs (no dedup,
    all rows). Used by agent.companies.rebuild()."""
    params = {"select": "company_key,poster_role,company,location,country,is_us",
              "limit": "10000"}
    resp = httpx.get(f"{_base()}/{_TABLE}", params=params, headers=_headers(), timeout=30)
    if resp.status_code >= 300:
        raise _fail("rollup select", resp)
    return resp.json()


def upsert_companies(rows: list[dict[str, Any]]) -> int:
    """Upsert the company rollup rows (on company_key). Returns rows sent."""
    payload = [{k: r.get(k) for k in _COMPANY_FIELDS}
               for r in rows if r.get("company_key")]
    for p in payload:
        p["confidence"] = _clean_float(p.get("confidence"))
        p["in_location"] = bool(p.get("in_location"))
        for c in ("employee_posts", "recruiter_posts", "founder_posts",
                  "announcement_posts", "news_posts", "total_posts",
                  "in_location_posts"):
            p[c] = _clean_int(p.get(c)) or 0
    if not payload:
        return 0
    url = f"{_base()}/{_COMPANIES_TABLE}?on_conflict=company_key"
    headers = _headers({"Prefer": "resolution=merge-duplicates,return=minimal"})
    resp = httpx.post(url, json=payload, headers=headers, timeout=30)
    if resp.status_code >= 300:
        raise _fail("companies upsert", resp)
    log.info("Rolled up %d companies", len(payload))
    return len(payload)


def list_companies(limit: int = 300, min_confidence: float | None = None,
                   in_location: bool | None = None) -> list[dict]:
    """Discovered companies, ranked by confidence then post volume.

    in_location=True returns only companies with at least one post in the target
    location (e.g. SF/California)."""
    def _params(with_in_location: bool) -> dict:
        p = {
            "select": "*",
            "order": "confidence.desc,total_posts.desc",
            "limit": str(limit),
        }
        if min_confidence is not None:
            p["confidence"] = f"gte.{min_confidence}"
        if with_in_location and in_location is not None:
            p["in_location"] = f"eq.{str(in_location).lower()}"
        return p

    url = f"{_base()}/{_COMPANIES_TABLE}"
    resp = httpx.get(url, params=_params(True), headers=_headers(), timeout=30)
    # Stale schema: the companies table predates the in_location column (run
    # supabase/companies.sql to add it). Rather than failing the whole Companies
    # tab, retry WITHOUT the location filter so discovered companies still show.
    if (resp.status_code >= 300 and in_location is not None
            and _is_missing_column(resp, "in_location")):
        log.warning("companies.in_location is missing — run supabase/companies.sql "
                    "to enable the location filter. Returning companies unfiltered.")
        resp = httpx.get(url, params=_params(False), headers=_headers(), timeout=30)
    if resp.status_code >= 300:
        raise _fail("companies select", resp)
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
        raise _fail("select", resp)
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
        raise _fail("delete", resp)
    try:
        return len(resp.json())
    except Exception:  # noqa: BLE001
        return 0


def table_exists() -> bool:
    """True if the layoff_posts table is reachable via PostgREST."""
    resp = httpx.get(f"{_base()}/{_TABLE}", params={"select": "id", "limit": "1"},
                     headers=_headers(), timeout=20)
    return resp.status_code < 300


def _table_absent(resp: httpx.Response) -> bool:
    """True if PostgREST reports the table itself is missing (not just a column).

    A missing table returns 404 (often with a PGRST2xx code like PGRST205,
    'Could not find the table … in the schema cache').
    """
    if resp.status_code == 404:
        return True
    try:
        return str(resp.json().get("code", "")).startswith("PGRST2")
    except Exception:  # noqa: BLE001 — non-JSON body
        return False


# What each table must have for the app to work, and which SQL file provides it.
# We probe only the migration-added columns (the ones most likely missing on an
# older schema); the base table check is the 404 case.
#   (table, columns-to-probe, SQL-if-table-missing, SQL-if-column-missing)
_SCHEMA_CHECKS = (
    (_TABLE, "company_key,poster_role",
     "supabase/layoff_posts.sql", "supabase/companies.sql"),
    (_COMPANIES_TABLE, "in_location,in_location_posts",
     "supabase/companies.sql", "supabase/companies.sql"),
)


def schema_status() -> dict:
    """Best-effort check that the Supabase tables have the columns the app needs.

    Returns ``{"checked": bool, "ok": bool, "problems": [str, ...]}`` and never
    raises. When Supabase isn't configured, is paused/unreachable, or fails in an
    unexpected way, returns ``checked=False`` so callers stay quiet — those states
    have their own, more specific UX and shouldn't also trigger a schema nag.
    """
    if not (config.SUPABASE_URL and config.SUPABASE_SERVICE_KEY):
        return {"checked": False, "ok": True, "problems": []}
    problems: list[str] = []
    for table, sel, base_sql, migration_sql in _SCHEMA_CHECKS:
        try:
            resp = httpx.get(f"{_base()}/{table}",
                             params={"select": sel, "limit": "1"},
                             headers=_headers(), timeout=15)
        except httpx.RequestError:
            return {"checked": False, "ok": True, "problems": []}  # offline
        if resp.status_code < 300:
            continue
        if resp.status_code in _UNREACHABLE_STATUS:
            return {"checked": False, "ok": True, "problems": []}  # paused/down
        if _is_missing_column(resp):
            problems.append(
                f"`{table}` is missing a required column — run **`{migration_sql}`** "
                "in the Supabase SQL editor.")
        elif _table_absent(resp):
            problems.append(
                f"`{table}` table not found — run **`{base_sql}`** in the Supabase "
                "SQL editor.")
        # Any other error (auth, transient): stay quiet rather than cry wolf.
    return {"checked": True, "ok": not problems, "problems": problems}
