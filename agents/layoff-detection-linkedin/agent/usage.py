"""Credit / cost tracking for scans.

Counts every paid API call made during a scan (Apify post scrapes, Apify
profile scrapes, Gemini calls + tokens, SerpAPI searches), estimates the USD
cost from the rates in config, and appends each scan to a local JSON log so the
dashboard can show per-scan and cumulative spend.

Thread-safe: the extraction pool calls add() concurrently. A scan is bracketed
by start_scan()/finish_scan(); outside a scan, add() is a no-op.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime

from . import config

_lock = threading.Lock()
_LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "usage_log.json")

_KEYS = ("apify_posts", "apify_profiles", "gemini_calls",
         "gemini_in_tokens", "gemini_out_tokens", "serpapi_searches",
         "perplexity_searches")

_current: dict | None = None


def start_scan() -> None:
    global _current
    with _lock:
        _current = {k: 0 for k in _KEYS}


def add(key: str, n: int = 1) -> None:
    with _lock:
        if _current is not None and key in _current:
            _current[key] += n


def cost_of(counts: dict) -> dict:
    apify = (counts.get("apify_posts", 0) / 1000 * config.APIFY_POST_COST_PER_1K
             + counts.get("apify_profiles", 0) / 1000 * config.APIFY_PROFILE_COST_PER_1K)
    gemini = (counts.get("gemini_in_tokens", 0) / 1e6 * config.GEMINI_IN_COST_PER_1M
              + counts.get("gemini_out_tokens", 0) / 1e6 * config.GEMINI_OUT_COST_PER_1M)
    serp = counts.get("serpapi_searches", 0) * config.SERPAPI_COST_PER_SEARCH
    pplx = counts.get("perplexity_searches", 0) * config.PERPLEXITY_COST_PER_SEARCH
    return {"apify": round(apify, 4), "gemini": round(gemini, 4),
            "serpapi": round(serp, 4), "perplexity": round(pplx, 4),
            "total": round(apify + gemini + serp + pplx, 4)}


def _read_log() -> list[dict]:
    try:
        with open(_LOG, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def finish_scan(extra: dict | None = None) -> dict:
    """Snapshot the current scan, cost it, append to the log, return the record."""
    global _current
    with _lock:
        counts = dict(_current or {k: 0 for k in _KEYS})
        _current = None
    record = {"at": datetime.now().astimezone().isoformat(timespec="seconds"),
              "counts": counts, "cost": cost_of(counts)}
    if extra:
        record.update(extra)
    log = _read_log()
    log.append(record)
    with _lock:
        with open(_LOG, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2)
    return record


def totals() -> dict:
    """Cumulative counts + cost across every logged scan."""
    log = _read_log()
    agg = {k: 0 for k in _KEYS}
    for r in log:
        for k in _KEYS:
            agg[k] += r.get("counts", {}).get(k, 0)
    return {"scans": len(log), "counts": agg, "cost": cost_of(agg),
            "last": log[-1] if log else None}


def reset() -> None:
    """Wipe the local scan-history / spend log."""
    global _current
    with _lock:
        _current = None
        try:
            os.remove(_LOG)
        except FileNotFoundError:
            pass


def recent(limit: int = 25) -> list[dict]:
    """Recent scans, newest first, slimmed for the history table."""
    log = _read_log()
    out = []
    for r in reversed(log[-limit:]):
        out.append({
            "at": r.get("at"),
            "examined": r.get("examined"),
            "qualified": r.get("qualified"),
            "new_leads": r.get("new_leads"),
            "cost": (r.get("cost") or {}).get("total"),
        })
    return out
