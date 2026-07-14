"""Wiza enrichment — turn a captured poster into a reach-out lead.

This is the recruitment hand-off: given a LinkedIn profile/post, Wiza returns
work email + verified contact so a recruiter can act with one click.

Wiza's individual-reveal API is ASYNCHRONOUS: the POST only *queues* a job and
returns `is_complete: false` with no contact data. You must then poll
`GET /individual_reveals/{id}` until `is_complete: true` before the email/name
fields are populated. This module does that polling.
"""
from __future__ import annotations

import logging
import time

import httpx

from . import config

log = logging.getLogger(__name__)

_WIZA = "https://wiza.co/api"


def _fields(data: dict) -> dict:
    """Pull the contact fields out of a completed reveal (defensively — Wiza has
    used a few field names over time)."""
    return {
        "email": data.get("email") or data.get("work_email"),
        "full_name": data.get("name") or data.get("full_name"),
        "title": data.get("title") or data.get("job_title"),
        "company": data.get("company") or data.get("company_name"),
    }


def enrich_profile(linkedin_url: str, max_wait: int = 40, interval: float = 3.0) -> dict:
    """Reveal a LinkedIn profile's work email via Wiza.

    Returns one of:
      {"status": "ok", "email", "full_name", "title", "company", "raw"}
      {"status": "pending", "message", "reveal_id", "raw"}   # still processing
      {"status": "no_api_key" | "error", "message"}

    Never raises — a failed enrichment returns a status the UI can show.
    `max_wait` caps how long we poll (seconds); `interval` is the poll gap.
    """
    if not config.WIZA_API_KEY:
        return {"status": "no_api_key",
                "message": "WIZA_API_KEY not set — add it to enable enrichment."}

    headers = {"Authorization": f"Bearer {config.WIZA_API_KEY}",
               "Content-Type": "application/json"}
    payload = {"individual_reveal": {"profile_url": linkedin_url},
               "enrichment_level": "full"}

    # 1) Queue the reveal.
    try:
        resp = httpx.post(f"{_WIZA}/individual_reveals", json=payload,
                          headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json().get("data", {}) or {}
    except httpx.HTTPError as exc:
        log.warning("Wiza reveal create failed: %s", exc)
        return {"status": "error", "message": str(exc)}

    reveal_id = data.get("id")

    # 2) Poll until the reveal completes (or we hit max_wait).
    deadline = time.monotonic() + max_wait
    while not data.get("is_complete") and reveal_id and time.monotonic() < deadline:
        time.sleep(interval)
        try:
            r = httpx.get(f"{_WIZA}/individual_reveals/{reveal_id}",
                          headers=headers, timeout=30)
            r.raise_for_status()
            data = r.json().get("data", {}) or {}
        except httpx.HTTPError as exc:
            log.warning("Wiza reveal poll failed: %s", exc)
            return {"status": "error", "message": str(exc)}

    # 3) Still not done — tell the UI it can retry (the credit is already spent,
    #    so a later re-check with the same id would return the result).
    if not data.get("is_complete"):
        return {"status": "pending", "reveal_id": reveal_id, "raw": data,
                "message": f"Wiza is still processing this profile (id {reveal_id}). "
                           "Try again in a few seconds."}

    return {"status": "ok", **_fields(data), "raw": data}
