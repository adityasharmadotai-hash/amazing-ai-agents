"""News layoff-announcement discovery via NewsAPI.org.

Optional: if NEWSAPI_KEY is unset the source is skipped cleanly and the
LinkedIn source still runs.
"""
from __future__ import annotations

import logging

import httpx

from .. import config

log = logging.getLogger(__name__)

_NEWSAPI = "https://newsapi.org/v2/everything"

_QUERY = '(layoffs OR "laid off" OR "job cuts" OR "workforce reduction")'


def search_news() -> list[dict]:
    """Return raw news candidates: {"url", "text", "source": "news"}."""
    if not config.NEWSAPI_KEY:
        log.info("News source skipped (NEWSAPI_KEY unset).")
        return []

    params = {
        "q": _QUERY,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 50,
        "apiKey": config.NEWSAPI_KEY,
    }
    try:
        resp = httpx.get(_NEWSAPI, params=params, timeout=30)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.warning("NewsAPI query failed: %s", exc)
        return []

    out: list[dict] = []
    for a in resp.json().get("articles", []) or []:
        url = a.get("url")
        if not url:
            continue
        text = " ".join(filter(None, [a.get("title"), a.get("description"), a.get("content")]))
        out.append({"url": url, "text": text, "source": "news"})
    log.info("News: %d candidate articles", len(out))
    return out
