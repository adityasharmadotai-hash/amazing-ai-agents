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
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    """Fetch results for one query, paginating until we have
    LINKEDIN_RESULTS_PER_Q of them.

    Google serves only ~10 organic results per page for a `site:` query (it
    ignores a large `num`), so to get more we must page with `start`. Each page
    is a separate SerpAPI search (and cost), so the number of pages is bounded
    by LINKEDIN_RESULTS_PER_Q — e.g. 20 -> 2 pages, 10 -> 1 page.
    """
    from .. import usage
    loc = config.location_query()
    q = f'site:linkedin.com/posts {query}'
    if loc:
        q = f"{q} {loc}"          # bias toward the target city/region
    gl, hl = config.serp_geo()
    tbs = _recency_tbs()
    want = max(1, config.LINKEDIN_RESULTS_PER_Q)
    pages = (want + 9) // 10       # ceil(want / 10)
    out: list[dict] = []
    for p in range(pages):
        params = {
            "engine": "google",
            "q": q,
            "num": 10,
            "start": p * 10,
            "api_key": config.SERPAPI_KEY,
            "tbs": tbs,  # last-N-days range, or qdr:<d/w/m/y> fallback
        }
        if gl:
            params["gl"] = gl
            params["hl"] = hl
        try:
            resp = httpx.get(_SERPAPI, params=params, timeout=30)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            log.warning("SerpAPI query failed (%s, page %d): %s", query, p, exc)
            break
        usage.add("serpapi_searches", 1)
        batch = resp.json().get("organic_results", []) or []
        out.extend(batch)
        if len(batch) < 10:        # no further pages available
            break
    return out[:want]


def _serpapi_search() -> list[dict]:
    """SerpAPI backend: run every query, dedupe by URL."""
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
    log.info("SerpAPI LinkedIn: %d unique candidate posts", len(out))
    return out


def _provider_search(name: str):
    """Return the zero-arg search function for a provider name (or None)."""
    if name == "serpapi":
        return _serpapi_search
    if name == "apify":
        from . import apify_linkedin
        return apify_linkedin.search_linkedin_posts
    if name == "perplexity":
        from . import perplexity_search
        return perplexity_search.search_linkedin_posts
    if name == "gemini":
        from . import gemini_search
        return gemini_search.search_linkedin_posts
    return None


def _norm_url(u: str | None) -> str:
    """Normalize a post URL for cross-provider dedup (drop query/fragment/case)."""
    if not u:
        return ""
    p = urlsplit(u.strip())
    return f"{p.scheme.lower()}://{p.netloc.lower()}{p.path.rstrip('/')}"


def search_linkedin_posts() -> list[dict]:
    """Discover candidate posts from the active provider(s).

    Resolves LINKEDIN_SOURCE via config.active_sources(): a single provider, or —
    in "all"/merge mode — every provider with a key, run concurrently and merged.
    Results are deduped across providers by normalized URL (keeping the richest
    text on collision). Each candidate:
    {"url", "text", "source": "linkedin", "profile_url"}.
    """
    sources = config.active_sources()
    results: list[dict] = []
    if len(sources) == 1:
        fn = _provider_search(sources[0])
        results = fn() if fn else []
    else:
        fns = {s: _provider_search(s) for s in sources}
        with ThreadPoolExecutor(max_workers=max(2, len(sources))) as pool:
            futs = {pool.submit(fn): s for s, fn in fns.items() if fn}
            for fut in as_completed(futs):
                s = futs[fut]
                try:
                    got = fut.result() or []
                    results.extend(got)
                    log.info("Provider %s -> %d candidate(s)", s, len(got))
                except Exception as exc:  # noqa: BLE001 — one bad provider is OK
                    log.warning("Provider %s failed: %s", s, exc)

    best: dict[str, dict] = {}
    for r in results:
        key = _norm_url(r.get("url"))
        if not key:
            continue
        cur = best.get(key)
        if cur is None or len(r.get("text") or "") > len(cur.get("text") or ""):
            best[key] = r
    out = list(best.values())
    log.info("LinkedIn (%s): %d unique candidate post(s) from %d raw",
             "+".join(sources), len(out), len(results))
    return out


def fetch_single(url: str) -> dict | None:
    """Fetch one specific post URL (for the 'Analyze a URL' box).

    Uses the first active provider (config.active_sources()); in merge mode that
    is the first available of serpapi/apify/perplexity.
    """
    name = config.active_sources()[0]
    if name == "apify":
        from . import apify_linkedin
        return apify_linkedin.fetch_single(url)
    if name == "gemini":
        from . import gemini_search
        return gemini_search.fetch_single(url)
    if name == "perplexity":
        from . import perplexity_search
        return perplexity_search.fetch_single(url)

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
