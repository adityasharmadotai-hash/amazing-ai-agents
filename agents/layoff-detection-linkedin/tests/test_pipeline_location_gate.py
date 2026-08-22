"""The scan hard-drops non-target-location posts in strict mode (agent/pipeline.py)."""
from __future__ import annotations

import pytest

from agent import config, pipeline


@pytest.fixture
def sf_targets(monkeypatch):
    monkeypatch.setattr(config, "TARGET_LOCATIONS",
                        ["San Francisco, California", "California"])
    monkeypatch.setattr(config, "_LOCATIONS_LOWER",
                        ["san francisco, california", "california"])
    monkeypatch.setattr(config, "EXPANSION_ENABLED", False)


def _stub_scan(monkeypatch, records):
    """Wire run_scan's collaborators to canned data; capture what gets stored."""
    stored: dict = {"rows": None}

    candidates = [{"url": r["source_url"], "text": "t", "source": "linkedin"}
                  for r in records]
    monkeypatch.setattr(pipeline, "_collect", lambda: candidates)
    # Map each candidate URL back to its prepared record.
    by_url = {r["source_url"]: r for r in records}
    monkeypatch.setattr(pipeline, "process_candidate",
                        lambda c: by_url.get(c["url"]))

    monkeypatch.setattr(pipeline.store, "list_records", lambda limit=1000: [])

    def fake_upsert(rows):
        stored["rows"] = rows
        return len(rows)
    monkeypatch.setattr(pipeline.store, "upsert_records", fake_upsert)

    monkeypatch.setattr(pipeline.companies, "rebuild", lambda: 0)
    monkeypatch.setattr(pipeline.usage, "start_scan", lambda: None)
    monkeypatch.setattr(pipeline.usage, "finish_scan",
                        lambda extra=None: {"cost": {}, "counts": {}})
    monkeypatch.setattr(pipeline.extract, "last_error", lambda: None)
    return stored


def test_strict_mode_drops_non_target_posts(sf_targets, monkeypatch):
    monkeypatch.setattr(config, "LOCATION_INCLUDE_UNKNOWN", False)
    records = [
        {"source_url": "u1", "company": "SF Co", "location": "San Francisco, CA",
         "is_us": True, "is_target_location": True},
        {"source_url": "u2", "company": "Palo Co", "location": "Palo Alto",
         "is_us": True},
        {"source_url": "u3", "company": "TX Co", "location": "Austin, TX",
         "is_us": True, "is_target_location": False},          # elsewhere -> drop
        {"source_url": "u4", "company": "Ghost Co", "location": "", "country": "",
         "is_us": False},                                      # unknown -> drop
    ]
    stored = _stub_scan(monkeypatch, records)
    summary = pipeline.run_scan()

    kept = {r["source_url"] for r in stored["rows"]}
    assert kept == {"u1", "u2"}                                # only verified SF
    assert summary["discovery"]["location_dropped"] == 2


def test_loose_mode_keeps_unknown(sf_targets, monkeypatch):
    monkeypatch.setattr(config, "LOCATION_INCLUDE_UNKNOWN", True)
    records = [
        {"source_url": "u1", "company": "SF Co", "location": "San Francisco",
         "is_us": True},
        {"source_url": "u2", "company": "Ghost Co", "location": "",
         "country": "unknown", "is_us": False},
    ]
    stored = _stub_scan(monkeypatch, records)
    pipeline.run_scan()
    kept = {r["source_url"] for r in stored["rows"]}
    assert kept == {"u1", "u2"}                                # nothing dropped
