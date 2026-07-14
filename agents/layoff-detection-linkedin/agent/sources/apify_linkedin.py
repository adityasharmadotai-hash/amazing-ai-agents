"""LinkedIn post discovery via Apify (paid, real LinkedIn scrape).

Uses the `apimaestro/linkedin-posts-search-scraper-no-cookies` actor, which
returns FULL post text + author headline (job title) — far richer than the
Google-indexed snippets SerpAPI gives, and it reaches posts Google never
indexed. Output shape matches the SerpAPI source: {"url", "text", "source"}.

The actor's exact output field names aren't publicly documented, so extraction
is defensive (tries several likely keys). Run `python scripts/apify_dump.py`
once to see the real shape and, if needed, tighten _first() below.
"""
from __future__ import annotations

import logging

import httpx

from .. import config

log = logging.getLogger(__name__)

_API = "https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"

# LINKEDIN_RECENCY (d/w/m/y) -> actor date_filter value
_DATE_MAP = {"d": "past-24h", "w": "past-week", "m": "past-month", "y": "past-year"}


def _actor_path() -> str:
    # API wants the '/' in the actor id replaced by '~'
    return config.APIFY_ACTOR.replace("/", "~")


def _date_filter() -> str:
    if config.APIFY_DATE_FILTER:
        return config.APIFY_DATE_FILTER
    return _DATE_MAP.get(config.LINKEDIN_RECENCY, "past-week")


def _first(d: dict, *keys, default=""):
    """Return the first present, non-empty value among keys (supports a.b nesting)."""
    for k in keys:
        cur = d
        ok = True
        for part in k.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur:
            return cur
    return default


def _run_actor(payload: dict) -> list[dict]:
    url = _API.format(actor=_actor_path())
    headers = {"Authorization": f"Bearer {config.APIFY_TOKEN}",
               "Content-Type": "application/json"}
    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=180)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.warning("Apify actor run failed: %s", exc)
        return []
    data = resp.json()
    items = data if isinstance(data, list) else data.get("items", [])
    from .. import usage
    usage.add("apify_posts", len(items))
    return items


def _to_candidate(item: dict) -> dict | None:
    url = _first(item, "url", "post_url", "postUrl", "share_url", "shareUrl",
                 "link", "full_urn", "urn")
    text = _first(item, "text", "content", "post_text", "postText", "commentary",
                  "description")
    # author headline carries the job title — critical for the role filter
    author = _first(item, "author.name", "authorName", "author_name",
                    "author.full_name", "actor.name", default="")
    if isinstance(author, dict):
        author = _first(author, "name", "full_name", default="")
    headline = _first(item, "author.headline", "authorHeadline", "author_headline",
                      "author.occupation", "actor.description", default="")
    if not (url and (text or headline)):
        return None
    profile_url = _first(item, "author.profile_url", "author.profileUrl",
                         "authorProfileUrl", "author.url", default="")
    if isinstance(profile_url, dict):
        profile_url = ""
    blob = " | ".join(filter(None, [str(author), str(headline), str(text)]))
    return {"url": str(url), "text": blob, "source": "linkedin",
            "profile_url": str(profile_url), "author_name": str(author)}


def search_linkedin_posts() -> list[dict]:
    """Run every configured query through the Apify actor; dedupe by URL."""
    seen: set[str] = set()
    out: list[dict] = []
    for query in config.LINKEDIN_QUERIES:
        payload = {
            "keyword": query,
            "sort_type": "date_posted",
            "date_filter": _date_filter(),
            "limit": config.LINKEDIN_RESULTS_PER_Q,
            "total_posts": config.LINKEDIN_RESULTS_PER_Q,
        }
        for item in _run_actor(payload):
            cand = _to_candidate(item)
            if not cand or cand["url"] in seen:
                continue
            seen.add(cand["url"])
            out.append(cand)
    log.info("Apify LinkedIn: %d unique candidate posts", len(out))
    return out


def fetch_single(url: str) -> dict | None:
    """Best-effort single-URL fetch (for the 'Analyze a URL' box)."""
    payload = {"post_url": url, "keyword": "", "limit": 1, "total_posts": 1}
    for item in _run_actor(payload):
        cand = _to_candidate(item)
        if cand:
            cand["url"] = url
            return cand
    return None
