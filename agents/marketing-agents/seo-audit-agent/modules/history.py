"""
history.py — Persist each live scan so the score-trend chart survives restarts.

Stores one entry per (url, day) in data/scan_history.json. Re-scanning the same
day overwrites that day's entry rather than piling up dozens of points.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_FILE = os.path.join(_DATA_DIR, "scan_history.json")
_MAX = 90  # keep ~3 months per site


def _load() -> dict:
    try:
        with open(_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def record(url: str, audit: dict, when: datetime | None = None) -> None:
    """Append/replace today's snapshot for this url."""
    when = when or datetime.now()
    day = when.strftime("%Y-%m-%d")
    data = _load()
    entries = data.get(url, [])
    snapshot = {
        "date": day,
        "overall": audit.get("overall_score", 0),
        "categories": {c: audit.get(c, {}).get("score", 0)
                       for c in ("meta", "headings", "keywords", "technical", "images", "links")},
    }
    entries = [e for e in entries if e.get("date") != day]
    entries.append(snapshot)
    entries.sort(key=lambda e: e["date"])
    data[url] = entries[-_MAX:]
    _save(data)


def series(url: str) -> list:
    """List of {date, overall, categories} oldest→newest for this url."""
    return _load().get(url, [])


def overall_points(url: str) -> list:
    """Just the overall scores, for the trend sparkline/area chart."""
    return [e["overall"] for e in series(url)]
