"""Supabase persistence via PostgREST (raw httpx).

We talk to PostgREST directly instead of the supabase-py client because the
client bundled an older gotrue/postgrest that rejects the new `sb_secret_` /
`sb_publishable_` API-key format with a misleading "Invalid API key". Raw REST
accepts the new keys and needs no extra dependency.
"""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx

from . import config

log = logging.getLogger(__name__)

_TABLE = "layoff_posts"


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


_FIELDS = ("source_url", "source", "company", "person_name", "role_hint",
           "role_category", "country", "is_us", "headcount", "location",
           "event_date", "open_to_work", "is_qualified", "summary", "confidence")


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
        raise RuntimeError(f"Supabase upsert failed {resp.status_code}: {resp.text[:200]}")
    log.info("Stored %d layoff records", len(rows))
    return len(rows)


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
    # keep the newest (rows are ordered created_at desc).
    seen: set = set()
    out = []
    for r in rows:
        name = (r.get("person_name") or "").strip().lower()
        key = (name, r.get("role_category"))
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
