"""Resolve a person's country from their LinkedIn profile (Apify).

When a post doesn't state where the laid-off person is, we scrape their public
profile via `apimaestro/linkedin-profile-detail` to get their location, then
decide US / not-US. Cached per profile URL so repeated posts cost one lookup.
"""
from __future__ import annotations

import logging
import re

import httpx

from . import config
from .sources.apify_linkedin import _first

log = logging.getLogger(__name__)

_API = "https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"
_cache: dict[str, dict | None] = {}

_US_TOKENS = ("united states", "usa", "u.s.a", "u.s.", "united states of america")
_US_STATES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine",
    "maryland", "massachusetts", "michigan", "minnesota", "mississippi",
    "missouri", "montana", "nebraska", "nevada", "new hampshire", "new jersey",
    "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina",
    "south dakota", "tennessee", "texas", "utah", "vermont", "virginia",
    "washington", "west virginia", "wisconsin", "wyoming",
    "washington dc", "district of columbia",
}


def looks_us(location: str | None) -> bool:
    if not location:
        return False
    t = location.lower()
    if any(tok in t for tok in _US_TOKENS):
        return True
    return any(re.search(rf"\b{re.escape(s)}\b", t) for s in _US_STATES)


def _handle(profile_url: str) -> str:
    """Extract the LinkedIn vanity handle from a profile URL.

    The `linkedin-profile-detail` actor's `username` input wants the bare
    handle (e.g. 'jane-doe'), not the full 'https://linkedin.com/in/jane-doe'
    URL. Falls back to the trimmed input if no '/in/<handle>' is found (it may
    already be a bare handle).
    """
    m = re.search(r"/in/([^/?#]+)", profile_url)
    return m.group(1) if m else profile_url.strip().strip("/")


def _run_profile(username: str) -> list[dict]:
    url = _API.format(actor=config.APIFY_PROFILE_ACTOR.replace("/", "~"))
    headers = {"Authorization": f"Bearer {config.APIFY_TOKEN}",
               "Content-Type": "application/json"}
    # A profile that takes longer than this isn't worth blocking the whole scan
    # for — the lead is simply kept with an unknown location. 120s (the old
    # value) let a single slow profile stall a worker for two minutes.
    try:
        resp = httpx.post(url, json={"username": username}, headers=headers, timeout=45)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.warning("Profile scrape failed for %s: %s", username, exc)
        return []
    data = resp.json()
    items = data if isinstance(data, list) else data.get("items", [])
    from . import usage
    usage.add("apify_profiles", 1)
    return items


def resolve_country(profile_url: str) -> dict | None:
    """Return {"country", "location", "is_us"} or None if unresolved."""
    if not (config.ENRICH_LOCATION and config.APIFY_TOKEN and profile_url):
        return None
    if profile_url in _cache:
        return _cache[profile_url]

    items = _run_profile(_handle(profile_url))
    result = None
    if items:
        it = items[0]
        loc = _first(it, "basic_info.location", "location", "geo", default={})
        if isinstance(loc, dict):
            country = str(loc.get("country") or "")
            code = str(loc.get("country_code") or "")
            full = str(loc.get("full") or loc.get("city") or "")
        else:                                   # plain string location
            country, code, full = "", "", str(loc)
        loc_text = " ".join(x for x in (full, country) if x)
        if loc_text.strip() or code:
            is_us = code.upper() == "US" or looks_us(loc_text)
            result = {
                "country": country or ("United States" if is_us else None),
                "location": full,
                "is_us": is_us,
            }
    _cache[profile_url] = result
    return result
