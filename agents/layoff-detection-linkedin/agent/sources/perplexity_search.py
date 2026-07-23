"""LinkedIn layoff-post discovery via Perplexity's Search API.

Uses Perplexity's dedicated `/search` endpoint (NOT chat completions): it runs a
live web search and returns the actual result pages as structured
{title, url, snippet, date} objects — real, current URLs with no scraper and no
LLM-formatting step to go wrong. It's the cheapest, most direct Perplexity
backend for this job.

We bias the search to individual LinkedIn posts with a `site:linkedin.com/posts`
query, restrict results to a country via the API's `country` parameter (US by
default — see `_country_code()`), and constrain freshness with
`search_recency_filter`. Output shape matches every other backend, so the rest of
the pipeline is untouched: {"url", "text", "source": "linkedin", "profile_url"}.

Requires PERPLEXITY_API_KEY.
"""
from __future__ import annotations

import logging
import re

import httpx

from .. import config
from .linkedin import _profile_url_from_post

log = logging.getLogger(__name__)

_API = "https://api.perplexity.ai/search"

# Keep only individual post/activity URLs (drops company pages, articles, etc.).
_POST_URL_RE = re.compile(r"linkedin\.com/(?:posts|feed/update)/", re.I)


def _recency_days() -> int:
    days = config.LINKEDIN_RECENCY_DAYS
    if days and days > 0:
        return days
    return {"d": 1, "w": 7, "m": 30, "y": 365}.get(config.LINKEDIN_RECENCY, 7)


def _search_recency_filter() -> str:
    """Map the N-day window to Perplexity's recency bucket (day/week/month/year)."""
    d = _recency_days()
    if d <= 1:
        return "day"
    if d <= 7:
        return "week"
    if d <= 31:
        return "month"
    return "year"


def _country_code() -> str | None:
    """ISO-3166 alpha-2 country to bias the search to, or None for worldwide.

    Reuses serp_geo(): when every target location is US-based (e.g. the default
    "San Francisco, California"), restrict the search to the US so no
    other-country posts come back. Worldwide targets don't set a country (the
    city itself is applied as a downstream location filter).
    """
    gl, _ = config.serp_geo()
    return gl.upper() if gl else None


def _build_query(query: str) -> str:
    """`site:`-scope the query to individual LinkedIn posts, plus any city terms."""
    q = f"site:linkedin.com/posts {query}"
    loc = config.location_query()
    if loc:
        q = f"{q} {loc}"
    return q


def _post(payload: dict) -> dict:
    """One Perplexity /search request. Returns the parsed body ({} on failure)."""
    headers = {"Authorization": f"Bearer {config.PERPLEXITY_API_KEY}",
               "Content-Type": "application/json"}
    try:
        resp = httpx.post(_API, json=payload, headers=headers, timeout=90)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.warning("Perplexity search request failed: %s", exc)
        return {}
    from .. import usage
    usage.add("perplexity_searches", 1)
    try:
        return resp.json()
    except ValueError:
        log.warning("Perplexity returned a non-JSON response body.")
        return {}


def _search_payload(query: str) -> dict:
    payload = {
        "query": _build_query(query),
        "max_results": max(1, config.LINKEDIN_RESULTS_PER_Q),
        "max_tokens_per_page": 256,
        "search_recency_filter": _search_recency_filter(),
    }
    country = _country_code()
    if country:
        payload["country"] = country      # e.g. "US" — no other-country posts
    return payload


def _candidates_from_results(body: dict) -> list[dict]:
    """Turn the API's `results` list into candidates, keeping only post URLs."""
    out: list[dict] = []
    for r in body.get("results") or []:
        if not isinstance(r, dict):
            continue
        url = str(r.get("url") or "").strip()
        if not _POST_URL_RE.search(url):
            continue
        text = " ".join(filter(None, [str(r.get("title") or "").strip(),
                                      str(r.get("snippet") or "").strip()]))
        out.append({"url": url, "text": text})
    return out


def search_linkedin_posts() -> list[dict]:
    """Run every configured query through Perplexity /search; dedupe by URL."""
    if not config.PERPLEXITY_API_KEY:
        log.warning("Perplexity source selected but PERPLEXITY_API_KEY is unset.")
        return []
    country = _country_code()
    seen: set[str] = set()
    out: list[dict] = []
    for query in config.LINKEDIN_QUERIES:
        body = _post(_search_payload(query))
        cands = _candidates_from_results(body)
        log.info("Perplexity search %r (country=%s) -> %d candidate(s)",
                 query[:50], country or "worldwide", len(cands))
        for c in cands:
            url = c["url"]
            if url in seen:
                continue
            seen.add(url)
            out.append({"url": url, "text": c["text"], "source": "linkedin",
                        "profile_url": _profile_url_from_post(url)})
    if not out:
        log.warning("Perplexity search returned 0 posts. Try a wider recency "
                    "window (LINKEDIN_RECENCY_DAYS), a simpler query, or turn off "
                    "the US-only country filter if you want worldwide results.")
    log.info("Perplexity LinkedIn: %d unique candidate post(s)", len(out))
    return out


def fetch_single(url: str) -> dict | None:
    """Best-effort single-URL fetch (for the 'Analyze a URL' box).

    Searches for the URL and returns the matching result's title+snippet; falls
    back to a bare candidate (the extractor can still mine the URL slug).
    """
    if not config.PERPLEXITY_API_KEY:
        return None
    body = _post({"query": url, "max_results": 5, "max_tokens_per_page": 256})
    text = ""
    for r in body.get("results") or []:
        if isinstance(r, dict) and str(r.get("url") or "").rstrip("/") == url.rstrip("/"):
            text = " ".join(filter(None, [str(r.get("title") or "").strip(),
                                          str(r.get("snippet") or "").strip()]))
            break
    return {"url": url, "text": text, "source": "linkedin",
            "profile_url": _profile_url_from_post(url)}
