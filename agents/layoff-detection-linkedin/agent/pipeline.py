"""Orchestrates one full scan: collect -> extract -> store."""
from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from . import enrich_location, extract, store, usage
from .sources import linkedin, news

log = logging.getLogger(__name__)

_UNKNOWN = {"", "unknown", "none", "n/a"}

# Only one scan may run at a time — scans are expensive and share a global
# usage meter, so overlapping runs would corrupt cost accounting.
_scan_lock = threading.Lock()


def _collect() -> list[dict]:
    """Run both sources concurrently and merge their raw candidates."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        li_future = pool.submit(linkedin.search_linkedin_posts)
        news_future = pool.submit(news.search_news)
        return li_future.result() + news_future.result()


def process_candidate(c: dict) -> dict | None:
    """Extract a record, then resolve unknown location via profile scrape."""
    rec = extract.extract_record(c["text"], c["url"])
    if not rec:
        return None
    rec["source"] = c.get("source", "linkedin")
    # Only spend a profile lookup when the post didn't reveal a country and the
    # role is a target one (no point locating a non-software person).
    country = (rec.get("country") or "").strip().lower()
    if (country in _UNKNOWN and not extract.config.location_ok(rec)
            and c.get("profile_url") and rec.get("is_individual")
            and extract.config.is_target_title(rec.get("role_category"))):
        loc = enrich_location.resolve_country(c["profile_url"])
        if loc:
            rec["country"] = loc.get("country") or rec.get("country")
            rec["location"] = loc.get("location") or rec.get("location")
            rec["is_us"] = loc.get("is_us", rec.get("is_us"))
    return rec


def run_scan() -> dict[str, Any]:
    """Full scan. Returns a summary dict (incl. cost) for the dashboard / logs.

    If a scan is already running, returns immediately with status 'busy'
    instead of starting a second, concurrent (and cost-corrupting) scan.
    """
    if not _scan_lock.acquire(blocking=False):
        log.info("Scan requested but one is already running — skipping.")
        return {"status": "busy", "message": "A scan is already running."}
    try:
        return _run_scan_locked()
    finally:
        _scan_lock.release()


def _run_scan_locked() -> dict[str, Any]:
    usage.start_scan()
    before = len(store.list_records(limit=1000))

    log.info("▶ Scan started — collecting posts from LinkedIn + News…")
    candidates = _collect()
    log.info("Collected %d candidate posts. Extracting with AI + resolving "
             "locations…", len(candidates))

    records: list[dict] = []
    # Extraction is LLM-bound; a small thread pool keeps latency down.
    with ThreadPoolExecutor(max_workers=5) as pool:
        for rec in pool.map(process_candidate, candidates):
            if rec:
                records.append(rec)
    log.info("Found %d layoff posts; applying US + software-title filter…",
             len(records))

    # Keep only qualified leads: US-based individuals in a target software role.
    relevant = [r for r in records if extract.is_relevant(r)]
    for r in relevant:
        log.info("  ✓ %s — %s (%s)", r.get("person_name") or "?",
                 r.get("role_category"), r.get("location") or "US")
    stored = store.upsert_records(relevant)
    after = len(store.list_records(limit=1000))
    log.info("Stored %d qualified leads (%d new). Scan complete.",
             stored, max(0, after - before))

    meter = usage.finish_scan(extra={
        "examined": len(candidates),
        "qualified": len(relevant),
        "new_leads": max(0, after - before),
    })
    summary = {
        "candidates": len(candidates),
        "layoff_records": len(records),
        "relevant_us_swe": len(relevant),
        "new_leads": max(0, after - before),
        "stored": stored,
        "cost": meter["cost"],
        "usage": meter["counts"],
    }
    log.info("Scan complete: %s", summary)
    return summary


def analyze_url(url: str) -> dict[str, Any] | None:
    """Analyze a single pasted LinkedIn post URL and store it."""
    candidate = linkedin.fetch_single(url)
    if not candidate:
        return None
    rec = process_candidate(candidate)
    if rec and extract.is_relevant(rec):
        store.upsert_records([rec])
    return rec
