"""LinkedIn layoff-post discovery via SerpAPI (Google-indexed posts).

Coverage caveat: this only surfaces LinkedIn posts Google has publicly indexed
— good volume, not every post, and slightly delayed (LinkedIn login-walls a
lot). To get real-time exhaustive hashtag-feed coverage, swap ONLY
`search_linkedin_posts()` for a paid scraper (Apify / Bright Data); the rest of
the pipeline is identical.
"""
from __future__ import annotations

import logging
import re
from datetime import date, timedelta
from urllib.parse import urlsplit

import httpx

from .. import config

log = logging.getLogger(__name__)

_SERPAPI = "https://serpapi.com/search.json"


def _recency_tbs() -> str:
    """Google `tbs` recency filter. Prefer an exact N-day custom date range
    (LINKEDIN_RECENCY_DAYS), falling back to the qdr:<d/w/m/y> shorthand."""
    days = config.LINKEDIN_RECENCY_DAYS
    if days and days > 0:
        cd_max = date.today()
        cd_min = cd_max - timedelta(days=days)
        return f"cdr:1,cd_min:{cd_min:%m/%d/%Y},cd_max:{cd_max:%m/%d/%Y}"
    return f"qdr:{config.LINKEDIN_RECENCY}"


def _profile_url_from_post(post_url: str) -> str:
    """Derive the author's profile URL from a LinkedIn post URL.

    Post URLs look like '.../posts/<author-handle>_<slug>-activity-<id>' — the
    segment before the first '_' is the author's public handle, so
    'https://www.linkedin.com/in/<handle>' is their profile. This lets the
    SerpAPI backend feed the profile-based location lookup the same way the
    Apify backend does. Returns '' when the URL isn't a recognizable post URL.
    """
    try:
        path = urlsplit(post_url).path
    except Exception:  # noqa: BLE001
        return ""
    m = re.search(r"/posts/([^/_]+)_", path)
    if not m:
        return ""
    return f"https://www.linkedin.com/in/{m.group(1)}"


def _fetch(query: str) -> list[dict]:
    loc = config.location_query()
    q = f'site:linkedin.com/posts {query}'
    if loc:
        q = f"{q} {loc}"          # bias toward the target city/region
    params = {
        "engine": "google",
        "q": q,
        "num": config.LINKEDIN_RESULTS_PER_Q,
        "api_key": config.SERPAPI_KEY,
        "tbs": _recency_tbs(),  # last-N-days range, or qdr:<d/w/m/y> fallback
    }
    gl, hl = config.serp_geo()
    if gl:
        params["gl"] = gl
        params["hl"] = hl
    try:
        resp = httpx.get(_SERPAPI, params=params, timeout=30)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.warning("SerpAPI query failed (%s): %s", query, exc)
        return []
    from .. import usage
    usage.add("serpapi_searches", 1)
    return resp.json().get("organic_results", []) or []


def search_linkedin_posts() -> list[dict]:
    """Run every configured query and return de-duplicated raw candidates.

    Dispatches to the Apify backend when LINKEDIN_SOURCE=apify, else SerpAPI.
    Each candidate: {"url", "text", "source": "linkedin"}.
    """
    if config.LINKEDIN_SOURCE == "apify":
        from . import apify_linkedin
        return apify_linkedin.search_linkedin_posts()

    seen: set[str] = set()
    out: list[dict] = []
    for query in config.LINKEDIN_QUERIES:
        for r in _fetch(query):
            url = r.get("link")
            if not url or url in seen:
                continue
            seen.add(url)
            text = " ".join(filter(None, [r.get("title"), r.get("snippet")]))
            out.append({"url": url, "text": text, "source": "linkedin",
                        "profile_url": _profile_url_from_post(url)})
    log.info("LinkedIn: %d unique candidate posts", len(out))
    return out


def fetch_single(url: str) -> dict | None:
    """Fetch one specific post URL (for the 'Analyze a URL' box)."""
    if config.LINKEDIN_SOURCE == "apify":
        from . import apify_linkedin
        return apify_linkedin.fetch_single(url)

    params = {
        "engine": "google",
        "q": url,
        "api_key": config.SERPAPI_KEY,
    }
    try:
        resp = httpx.get(_SERPAPI, params=params, timeout=30)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.warning("SerpAPI single fetch failed: %s", exc)
        return None
    profile_url = _profile_url_from_post(url)
    for r in resp.json().get("organic_results", []) or []:
        if r.get("link") == url or url in (r.get("link") or ""):
            text = " ".join(filter(None, [r.get("title"), r.get("snippet")]))
            return {"url": url, "text": text, "source": "linkedin",
                    "profile_url": profile_url}
    # Fall back to whatever the top result described.
    results = resp.json().get("organic_results", [])
    if results:
        r = results[0]
        text = " ".join(filter(None, [r.get("title"), r.get("snippet")]))
        return {"url": url, "text": text, "source": "linkedin",
                "profile_url": profile_url}
    return None
