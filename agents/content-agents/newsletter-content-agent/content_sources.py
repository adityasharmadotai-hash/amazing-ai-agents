"""
Content collection layer.

Implements one collector per source type behind a common interface. Network
fetches run concurrently using a thread pool wrapped in an async helper so the
Streamlit UI can call ``collect_all(...)`` and get back a deduplicated list of
content items ready for persistence.

Source types
------------
RSS Feed / Blog / Company Website / News Website
    feedparser when the URL is a feed, otherwise HTML scrape of article links.
Reddit
    Public JSON endpoint (no auth) for a subreddit or search.
YouTube
    Channel / playlist RSS feeds (no API key needed).
Twitter/X & LinkedIn
    Require authenticated APIs; collectors attempt a public fetch and fall back
    to clearly-labelled demo items so the pipeline never breaks.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Callable

import requests

from config import SOURCE_ICONS

USER_AGENT = "NewsletterContentAgent/1.0 (+https://example.com)"
TIMEOUT = 12
_EXECUTOR = ThreadPoolExecutor(max_workers=8)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _hash(*parts: str) -> str:
    return hashlib.sha256("||".join(p or "" for p in parts).encode("utf-8")).hexdigest()


def _clean_html(text: str) -> str:
    if not text:
        return ""
    try:
        from bs4 import BeautifulSoup

        text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
    except Exception:
        text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _make_item(source: dict, title, url, summary, author=None, published=None, raw=None) -> dict:
    summary = _clean_html(summary)[:1500]
    return {
        "source_id": source.get("id"),
        "source_type": source.get("source_type"),
        "source_name": source.get("name"),
        "title": (title or "Untitled").strip()[:400],
        "url": url,
        "summary": summary,
        "raw_text": (_clean_html(raw)[:6000] if raw else summary),
        "author": author,
        "topic": source.get("topic"),
        "industry": source.get("industry"),
        "published_at": published,
        "content_hash": _hash(title or "", url or ""),
        "score": 0,
    }


# --------------------------------------------------------------------------- #
# Individual collectors (synchronous; run inside the thread pool)
# --------------------------------------------------------------------------- #
def collect_rss(source: dict) -> list[dict]:
    import feedparser

    feed = feedparser.parse(source.get("url", ""))
    items = []
    for entry in feed.entries[:25]:
        items.append(
            _make_item(
                source,
                title=entry.get("title"),
                url=entry.get("link"),
                summary=entry.get("summary") or entry.get("description"),
                author=entry.get("author"),
                published=entry.get("published") or entry.get("updated"),
                raw=entry.get("content", [{}])[0].get("value") if entry.get("content") else None,
            )
        )
    return items


def collect_web(source: dict) -> list[dict]:
    """Scrape article links from a news site / blog / company page.

    Falls back to RSS if the page exposes a feed link.
    """
    from bs4 import BeautifulSoup

    url = source.get("url", "")
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Prefer a discoverable feed
    feed_link = soup.find("link", attrs={"type": re.compile("rss|atom")})
    if feed_link and feed_link.get("href"):
        feed_source = dict(source)
        feed_source["url"] = requests.compat.urljoin(url, feed_link["href"])
        rss_items = collect_rss(feed_source)
        if rss_items:
            return rss_items

    items, seen = [], set()
    for art in soup.find_all(["article", "h2", "h3"])[:40]:
        link = art.find("a", href=True) or (art if art.name == "a" else None)
        if not link or not link.get("href"):
            continue
        href = requests.compat.urljoin(url, link["href"])
        title = link.get_text(" ", strip=True)
        if not title or len(title) < 12 or href in seen:
            continue
        seen.add(href)
        items.append(_make_item(source, title=title, url=href, summary=title))
        if len(items) >= 20:
            break
    return items


def collect_reddit(source: dict) -> list[dict]:
    """Use Reddit's public JSON endpoint. ``url`` may be a subreddit name or URL."""
    raw = source.get("url", "").strip()
    sub = raw.rstrip("/").split("/")[-1] if raw else "technology"
    sub = sub.replace("r/", "") or "technology"
    api = f"https://www.reddit.com/r/{sub}/hot.json?limit=25"
    try:
        resp = requests.get(api, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        resp.raise_for_status()
        children = resp.json().get("data", {}).get("children", [])
    except (requests.RequestException, ValueError):
        return []

    items = []
    for child in children:
        d = child.get("data", {})
        if d.get("stickied"):
            continue
        item = _make_item(
            source,
            title=d.get("title"),
            url=f"https://reddit.com{d.get('permalink', '')}",
            summary=d.get("selftext") or d.get("title"),
            author=d.get("author"),
            published=datetime.fromtimestamp(d.get("created_utc", 0), tz=timezone.utc).isoformat(),
        )
        item["score"] = float(d.get("ups", 0))
        items.append(item)
    return items


def collect_youtube(source: dict) -> list[dict]:
    """YouTube channels/playlists expose RSS feeds; reuse the RSS collector."""
    url = source.get("url", "")
    feed_url = url
    if "channel/" in url:
        cid = url.split("channel/")[-1].split("/")[0].split("?")[0]
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
    elif "list=" in url:
        pid = url.split("list=")[-1].split("&")[0]
        feed_url = f"https://www.youtube.com/feeds/videos.xml?playlist_id={pid}"
    feed_source = dict(source)
    feed_source["url"] = feed_url
    return collect_rss(feed_source)


def collect_social(source: dict) -> list[dict]:
    """Twitter/X and LinkedIn require authenticated APIs.

    We attempt a public Nitter-style fetch for X via RSS if a feed URL is
    supplied; otherwise we return a single labelled placeholder so the user
    understands why nothing was collected without the pipeline failing.
    """
    url = source.get("url", "")
    if url and ("rss" in url or url.endswith(".xml")):
        rss = collect_rss(source)
        if rss:
            return rss
    icon = SOURCE_ICONS.get(source.get("source_type", ""), "🔗")
    note = (
        f"{icon} {source.get('source_type')} collection requires authenticated API "
        f"credentials (configure them in Settings). No public items were fetched for "
        f"'{source.get('name')}'."
    )
    item = _make_item(
        source,
        title=f"[Setup needed] {source.get('name')} — {source.get('source_type')} API not configured",
        url=url,
        summary=note,
    )
    item["score"] = -1  # de-prioritise placeholders
    return [item]


COLLECTORS: dict[str, Callable[[dict], list[dict]]] = {
    "RSS Feed": collect_rss,
    "Blog": collect_web,
    "Company Website": collect_web,
    "News Website": collect_web,
    "Reddit": collect_reddit,
    "YouTube": collect_youtube,
    "Twitter/X": collect_social,
    "LinkedIn": collect_social,
}


def collect_one(source: dict) -> list[dict]:
    collector = COLLECTORS.get(source.get("source_type"), collect_web)
    try:
        return collector(source)
    except Exception as exc:  # never let one bad source kill the run
        return [
            _make_item(
                source,
                title=f"[Error] Could not collect from {source.get('name')}",
                url=source.get("url"),
                summary=f"Collection failed: {exc}",
            )
        ]


# --------------------------------------------------------------------------- #
# Async orchestration
# --------------------------------------------------------------------------- #
async def collect_all_async(sources: list[dict]) -> list[dict]:
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(_EXECUTOR, collect_one, s) for s in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    items: list[dict] = []
    for res in results:
        if isinstance(res, list):
            items.extend(res)
    return deduplicate(items)


def collect_all(sources: list[dict]) -> list[dict]:
    """Synchronous entry point for Streamlit. Runs all collectors concurrently."""
    if not sources:
        return []
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(collect_all_async(sources))
    finally:
        loop.close()


def deduplicate(items: list[dict]) -> list[dict]:
    """Drop exact duplicates by hash and near-duplicate titles."""
    seen_hash: set[str] = set()
    seen_title: set[str] = set()
    unique = []
    for item in items:
        h = item.get("content_hash")
        norm_title = re.sub(r"[^a-z0-9]", "", (item.get("title") or "").lower())[:60]
        if h in seen_hash or (norm_title and norm_title in seen_title):
            continue
        seen_hash.add(h)
        if norm_title:
            seen_title.add(norm_title)
        unique.append(item)
    return unique
