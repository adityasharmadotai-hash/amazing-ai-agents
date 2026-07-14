"""Wiza enrichment — turn a captured poster into a reach-out lead.

This is the recruitment hand-off: given a LinkedIn profile/post, Wiza returns
work email + verified contact so a recruiter can act with one click.
"""
from __future__ import annotations

import logging

import httpx

from . import config

log = logging.getLogger(__name__)

_WIZA = "https://wiza.co/api"


def enrich_profile(linkedin_url: str) -> dict:
    """Return {"status", "email", "full_name", "title", "company", "raw"}.

    Never raises — a failed enrichment returns a status the UI can show.
    """
    if not config.WIZA_API_KEY:
        return {"status": "no_api_key",
                "message": "WIZA_API_KEY not set — add it to enable enrichment."}

    headers = {"Authorization": f"Bearer {config.WIZA_API_KEY}",
               "Content-Type": "application/json"}
    payload = {"individual_reveal": {"profile_url": linkedin_url}, "enrichment_level": "full"}
    try:
        resp = httpx.post(f"{_WIZA}/individual_reveals", json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json().get("data", {})
    except httpx.HTTPError as exc:
        log.warning("Wiza enrichment failed: %s", exc)
        return {"status": "error", "message": str(exc)}

    return {
        "status": "ok",
        "email": data.get("email"),
        "full_name": data.get("name"),
        "title": data.get("title"),
        "company": data.get("company"),
        "raw": data,
    }
