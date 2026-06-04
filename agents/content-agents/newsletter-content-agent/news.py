"""
modules/news.py
---------------
Content research layer. Fetches recent articles from NewsAPI, removes
duplicates, and selects the top N most relevant / recent articles.
"""

import re
import requests
from datetime import datetime

NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"


class NewsAPIError(Exception):
    """Raised when NewsAPI returns an error or is unreachable."""


def _normalize_title(title: str) -> str:
    """Lower-case, strip punctuation/whitespace for duplicate detection."""
    if not title:
        return ""
    title = title.lower()
    title = re.sub(r"[^a-z0-9 ]+", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def _clean_article(article: dict) -> dict:
    """Project the NewsAPI payload into the fields we actually use."""
    source = article.get("source") or {}
    return {
        "title": (article.get("title") or "").strip(),
        "description": (article.get("description") or "").strip(),
        "content": (article.get("content") or "").strip(),
        "url": article.get("url") or "",
        "source": source.get("name") or "Unknown",
        "published_at": article.get("publishedAt") or "",
        "image": article.get("urlToImage") or "",
    }


def fetch_articles(topic: str, api_key: str, page_size: int = 30,
                   language: str = "en", sort_by: str = "publishedAt") -> list:
    """
    Query NewsAPI for `topic`. Returns a list of cleaned article dicts.
    Raises NewsAPIError on failure.
    """
    if not api_key:
        raise NewsAPIError("Missing NewsAPI key. Add it in Settings.")
    if not topic or not topic.strip():
        raise NewsAPIError("Please provide a newsletter topic.")

    params = {
        "q": topic.strip(),
        "language": language,
        "sortBy": sort_by,
        "pageSize": min(max(page_size, 1), 100),
        "apiKey": api_key,
    }

    try:
        resp = requests.get(NEWSAPI_ENDPOINT, params=params, timeout=20)
    except requests.RequestException as exc:
        raise NewsAPIError(f"Could not reach NewsAPI: {exc}") from exc

    if resp.status_code == 401:
        raise NewsAPIError("NewsAPI rejected the key (401). Check it in Settings.")
    if resp.status_code == 429:
        raise NewsAPIError("NewsAPI rate limit reached (429). Try again later.")

    try:
        data = resp.json()
    except ValueError as exc:
        raise NewsAPIError("NewsAPI returned an invalid response.") from exc

    if data.get("status") != "ok":
        raise NewsAPIError(data.get("message", "Unknown NewsAPI error."))

    articles = [_clean_article(a) for a in data.get("articles", [])]
    # Drop NewsAPI's removed/empty placeholders.
    articles = [
        a for a in articles
        if a["title"] and a["title"].lower() != "[removed]"
    ]
    return articles


def deduplicate(articles: list) -> list:
    """Remove duplicates by normalized title and by URL."""
    seen_titles, seen_urls, unique = set(), set(), []
    for art in articles:
        norm = _normalize_title(art["title"])
        url = art["url"]
        if norm in seen_titles or (url and url in seen_urls):
            continue
        seen_titles.add(norm)
        if url:
            seen_urls.add(url)
        unique.append(art)
    return unique


def _published_key(article: dict):
    """Sort key: most recent first; unknown dates sink to the bottom."""
    raw = article.get("published_at") or ""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.min


def select_top(articles: list, count: int = 5) -> list:
    """
    Deduplicate, prefer articles with real body text, sort by recency,
    and return the top `count`.
    """
    unique = deduplicate(articles)
    # Articles with description/content first — they make better summaries.
    with_body = [a for a in unique if a["description"] or a["content"]]
    without_body = [a for a in unique if not (a["description"] or a["content"])]
    with_body.sort(key=_published_key, reverse=True)
    without_body.sort(key=_published_key, reverse=True)
    ordered = with_body + without_body
    return ordered[:count]


def research(topic: str, api_key: str, count: int = 5) -> list:
    """One-shot helper: fetch -> dedupe -> top N."""
    raw = fetch_articles(topic, api_key)
    return select_top(raw, count=count)
