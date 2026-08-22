"""Strict location normalization & resolution (agent/config.py, agent/extract.py)."""
from __future__ import annotations

import pytest

from agent import config, extract


@pytest.fixture
def sf_targets(monkeypatch):
    """Force the SF / California target config regardless of the environment."""
    monkeypatch.setattr(config, "TARGET_LOCATIONS",
                        ["San Francisco, California", "California"])
    monkeypatch.setattr(config, "_LOCATIONS_LOWER",
                        ["san francisco, california", "california"])
    return config


# ── Alias expansion ──────────────────────────────────────────────────────────
def test_sf_alias_group_present(sf_targets):
    terms = config._loc_match_terms("san francisco, california")
    for alias in ("san francisco", "sf", "bay area", "silicon valley",
                  "palo alto", "mountain view", "sunnyvale", "san jose"):
        assert alias in terms, f"{alias!r} missing from SF match terms"


def test_target_location_aliases_deduped(sf_targets):
    aliases = config.target_location_aliases()
    assert len(aliases) == len(set(aliases))          # no dupes
    assert "palo alto" in aliases and "bay area" in aliases


@pytest.mark.parametrize("place", [
    "Palo Alto", "Mountain View, CA", "San Jose", "Sunnyvale",
    "San Francisco Bay Area", "Silicon Valley",
])
def test_bay_area_cities_match_sf_target(sf_targets, place):
    rec = {"location": place, "country": "United States", "is_us": True}
    assert config.location_ok(rec) is True


def test_sf_alias_matches_on_word_boundary(sf_targets, monkeypatch):
    monkeypatch.setattr(config, "LOCATION_INCLUDE_UNKNOWN", False)
    # "SF" as a standalone token qualifies…
    assert config.location_ok({"location": "SF", "country": "USA"}) is True
    # …but must not false-match inside an unrelated word.
    assert config.location_ok({"location": "Misfit Labs, Berlin",
                               "country": "Germany"}) is False


# ── Hard rejection when LOCATION_INCLUDE_UNKNOWN=false ────────────────────────
def test_unknown_location_rejected_in_strict_mode(sf_targets, monkeypatch):
    monkeypatch.setattr(config, "LOCATION_INCLUDE_UNKNOWN", False)
    rec = {"location": "", "country": "", "is_us": False}
    assert config.location_ok(rec) is False


def test_elsewhere_rejected_in_strict_mode(sf_targets, monkeypatch):
    monkeypatch.setattr(config, "LOCATION_INCLUDE_UNKNOWN", False)
    rec = {"location": "Austin, TX", "country": "United States", "is_us": True}
    assert config.location_ok(rec) is False


def test_unknown_allowed_when_include_unknown(sf_targets, monkeypatch):
    monkeypatch.setattr(config, "LOCATION_INCLUDE_UNKNOWN", True)
    rec = {"location": "", "country": "unknown", "is_us": False}
    assert config.location_ok(rec) is True


# ── is_target_location verdict is authoritative ──────────────────────────────
def test_target_flag_true_qualifies(sf_targets, monkeypatch):
    monkeypatch.setattr(config, "LOCATION_INCLUDE_UNKNOWN", False)
    rec = {"is_target_location": True, "location": "", "country": ""}
    assert config.location_ok(rec) is True


def test_target_flag_false_blocks_unknown_benefit(sf_targets, monkeypatch):
    # Even in loose mode, an explicit "not target location" is a hard no.
    monkeypatch.setattr(config, "LOCATION_INCLUDE_UNKNOWN", True)
    rec = {"is_target_location": False, "location": "", "country": "unknown"}
    assert config.location_ok(rec) is False


# ── Extractor coercion + prompt ──────────────────────────────────────────────
@pytest.mark.parametrize("raw,expected", [
    (True, True), (False, False), ("true", True), ("No", False),
    ("1", True), ("0", False), (None, None), ("maybe", None), (5, None),
])
def test_coerce_target_flag(raw, expected):
    assert extract._coerce_target_flag(raw) is expected


def test_prompt_lists_target_aliases(sf_targets):
    desc = extract._target_desc()
    assert "palo alto" in desc and "san francisco" in desc


def test_extract_record_sets_target_flag(sf_targets, monkeypatch):
    fake = {"is_layoff": True, "is_target_location": "true", "company": "ACME"}
    monkeypatch.setattr(extract.llm, "complete_json", lambda s, u: fake)
    rec = extract.extract_record("laid off at ACME in SF", "https://x/posts/a_b")
    assert rec["is_target_location"] is True          # coerced from "true"
    assert rec["source_url"] == "https://x/posts/a_b"


def test_extract_record_missing_flag_is_none(sf_targets, monkeypatch):
    fake = {"is_layoff": True, "company": "ACME"}     # no is_target_location key
    monkeypatch.setattr(extract.llm, "complete_json", lambda s, u: fake)
    rec = extract.extract_record("laid off", "https://x/posts/a_b")
    assert rec["is_target_location"] is None
