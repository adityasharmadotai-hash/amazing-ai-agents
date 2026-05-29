"""
modules/fetcher.py
------------------
Multi-source news fetching: RSS feeds, NewsAPI.org, Google News RSS,
Reddit (JSON API), Hacker News (public API).
All sources return the same normalised article dict.
"""
from __future__ import annotations
import asyncio
import hashlib
import html
import re
import time
from datetime import datetime, timezone
from typing import Any

import requests
from bs4 import BeautifulSoup

try:
    import feedparser
    FP_OK = True
except ImportError:
    FP_OK = False


# ── Normalised article schema ─────────────────────────────────────────────────

def _make_id(url: str, title: str) -> str:
    return hashlib.md5(f"{url}{title}".encode()).hexdigest()[:16]


def _clean(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:1000]


def _article(
    title: str,
    url: str,
    source: str,
    published: str = "",
    summary: str = "",
    full_text: str = "",
    image_url: str = "",
    topics: list | None = None,
) -> dict:
    return {
        "id": _make_id(url, title),
        "title": _clean(title)[:200],
        "source": source,
        "url": url,
        "published": published or datetime.now(timezone.utc).isoformat(),
        "summary": _clean(summary)[:500],
        "full_text": _clean(full_text)[:2000],
        "image_url": image_url,
        "topics": topics or [],
        "sentiment": "neutral",
        "signal_score": 0.0,
        "is_duplicate": False,
    }


# ── RSS / Atom feeds ──────────────────────────────────────────────────────────

RSS_FEEDS: dict[str, str] = {
    "TechCrunch": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Reuters Tech": "https://feeds.reuters.com/reuters/technologyNews",
    "BBC News": "https://feeds.bbci.co.uk/news/rss.xml",
    "BBC Tech": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "Hacker News": "https://hnrss.org/frontpage",
    "MIT Tech Review": "https://www.technologyreview.com/feed/",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "Wired": "https://www.wired.com/feed/rss",
    "Forbes Tech": "https://www.forbes.com/innovation/feed2",
    "VentureBeat": "https://venturebeat.com/feed/",
    "Bloomberg Tech": "https://feeds.bloomberg.com/technology/news.rss",
    "CNBC Tech": "https://www.cnbc.com/id/19854910/device/rss/rss.html",
    "Financial Times": "https://www.ft.com/?format=rss",
    "Nature": "https://www.nature.com/nature.rss",
    "Science Daily": "https://www.sciencedaily.com/rss/top/technology.xml",
    "Reddit WorldNews": "https://www.reddit.com/r/worldnews/.rss",
    "Reddit Technology": "https://www.reddit.com/r/technology/.rss",
    "Reddit Business": "https://www.reddit.com/r/business/.rss",
    "Seeking Alpha": "https://seekingalpha.com/market_currents.xml",
}

GOOGLE_NEWS_TOPICS: dict[str, str] = {
    "Technology": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB",
    "Business": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
    "Science": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNR1p0TlRFU0FtVnVHZ0pWVXlnQVAB",
    "Health": "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtVnVLQUFQAQ",
    "World": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB",
    "Finance": "https://news.google.com/rss/headlines/section/topic/BUSINESS",
}


def fetch_rss_feed(name: str, url: str, max_items: int = 15) -> list[dict]:
    """Fetch and parse a single RSS feed."""
    if not FP_OK:
        return []
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:max_items]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            if not title or not link:
                continue
            # Published date
            pub = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
                except Exception:
                    pub = ""
            # Summary/description
            summary = entry.get("summary", entry.get("description", ""))
            # Image
            image = ""
            if hasattr(entry, "media_content") and entry.media_content:
                image = entry.media_content[0].get("url", "")
            elif hasattr(entry, "enclosures") and entry.enclosures:
                image = entry.enclosures[0].get("href", "")

            articles.append(_article(
                title=title, url=link, source=name,
                published=pub, summary=summary, image_url=image,
            ))
        return articles
    except Exception:
        return []


def fetch_all_rss(selected_sources: list[str] | None = None, max_per_feed: int = 12) -> list[dict]:
    """Fetch from all RSS feeds (or selected subset)."""
    feeds = RSS_FEEDS
    if selected_sources:
        feeds = {k: v for k, v in RSS_FEEDS.items() if k in selected_sources}

    articles = []
    for name, url in feeds.items():
        articles.extend(fetch_rss_feed(name, url, max_per_feed))
        time.sleep(0.1)  # polite rate limiting
    return articles


def fetch_google_news(topics: list[str] | None = None, max_per: int = 15) -> list[dict]:
    """Fetch Google News RSS for selected topics."""
    if not FP_OK:
        return []
    selected = {k: v for k, v in GOOGLE_NEWS_TOPICS.items()
                if not topics or k in topics}
    articles = []
    for topic, url in selected.items():
        feed_articles = fetch_rss_feed(f"Google News ({topic})", url, max_per)
        for a in feed_articles:
            a["topics"] = [topic]
        articles.extend(feed_articles)
        time.sleep(0.15)
    return articles


# ── NewsAPI.org ───────────────────────────────────────────────────────────────

def fetch_newsapi(
    api_key: str,
    keywords: list[str] | None = None,
    topics: list[str] | None = None,
    country: str = "us",
    max_results: int = 50,
) -> list[dict]:
    """Fetch from NewsAPI.org (free tier: 100 req/day)."""
    if not api_key:
        return []
    try:
        query = " OR ".join((keywords or []) + (topics or []))[:500] or "technology"
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "apiKey": api_key,
            "pageSize": min(max_results, 100),
            "sortBy": "publishedAt",
            "language": "en",
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        articles = []
        for item in data.get("articles", []):
            title = item.get("title", "") or ""
            if title in ("[Removed]", "") or not item.get("url"):
                continue
            articles.append(_article(
                title=title,
                url=item.get("url", ""),
                source=item.get("source", {}).get("name", "NewsAPI"),
                published=item.get("publishedAt", ""),
                summary=item.get("description", "") or "",
                full_text=item.get("content", "") or "",
                image_url=item.get("urlToImage", "") or "",
            ))
        return articles
    except Exception:
        return []


# ── Hacker News ───────────────────────────────────────────────────────────────

def fetch_hacker_news(max_items: int = 30) -> list[dict]:
    """Fetch HN top stories via the public Firebase API."""
    try:
        r = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json", timeout=8
        )
        story_ids = r.json()[:max_items]
        articles = []
        for sid in story_ids[:20]:  # limit to avoid slow fetches
            try:
                sr = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=5
                )
                item = sr.json()
                if not item or item.get("type") != "story":
                    continue
                url = item.get("url", f"https://news.ycombinator.com/item?id={sid}")
                articles.append(_article(
                    title=item.get("title", ""),
                    url=url,
                    source="Hacker News",
                    published=datetime.fromtimestamp(
                        item.get("time", 0), tz=timezone.utc
                    ).isoformat(),
                    summary=f"Score: {item.get('score',0)} · {item.get('descendants',0)} comments",
                    topics=["Technology"],
                ))
            except Exception:
                continue
        return articles
    except Exception:
        return []


# ── Reddit ────────────────────────────────────────────────────────────────────

REDDIT_SUBS: dict[str, list[str]] = {
    "Technology": ["technology", "tech"],
    "AI": ["MachineLearning", "artificial", "ChatGPT"],
    "Business": ["business", "investing", "economics"],
    "Science": ["science", "spacex", "space"],
    "Finance": ["finance", "stocks", "wallstreetbets"],
    "World News": ["worldnews", "news"],
}


def fetch_reddit(topics: list[str] | None = None, max_per: int = 10) -> list[dict]:
    """Fetch from Reddit JSON API (no auth required for public posts)."""
    headers = {"User-Agent": "NewsAgent/1.0 (research tool)"}
    articles = []
    selected = REDDIT_SUBS
    if topics:
        selected = {k: v for k, v in REDDIT_SUBS.items() if k in topics}

    for topic, subs in list(selected.items())[:3]:  # limit subs
        sub = subs[0]
        try:
            r = requests.get(
                f"https://www.reddit.com/r/{sub}/hot.json?limit={max_per}",
                headers=headers, timeout=8,
            )
            data = r.json()
            for post in data.get("data", {}).get("children", []):
                p = post.get("data", {})
                title = p.get("title", "")
                url = p.get("url", "")
                if not title or not url:
                    continue
                articles.append(_article(
                    title=title,
                    url=url if url.startswith("http") else f"https://reddit.com{url}",
                    source=f"Reddit r/{sub}",
                    published=datetime.fromtimestamp(
                        p.get("created_utc", 0), tz=timezone.utc
                    ).isoformat(),
                    summary=f"Score: {p.get('score',0)} · {p.get('num_comments',0)} comments · {p.get('selftext','')[:200]}",
                    topics=[topic],
                ))
            time.sleep(0.5)  # Reddit rate limit
        except Exception:
            continue
    return articles


# ── Keyword search via Google News RSS ───────────────────────────────────────

def fetch_keyword_news(keywords: list[str], max_per: int = 10) -> list[dict]:
    """Fetch Google News RSS for specific keywords."""
    if not FP_OK or not keywords:
        return []
    articles = []
    for kw in keywords[:5]:  # limit to 5 keywords
        url = f"https://news.google.com/rss/search?q={requests.utils.quote(kw)}&hl=en"
        feed_articles = fetch_rss_feed(f"Google ({kw})", url, max_per)
        articles.extend(feed_articles)
        time.sleep(0.2)
    return articles


# ── Company news via Google News ─────────────────────────────────────────────

def fetch_company_news(companies: list[str], max_per: int = 8) -> list[dict]:
    """Fetch news for specific companies."""
    if not FP_OK or not companies:
        return []
    articles = []
    for company in companies[:5]:
        url = f"https://news.google.com/rss/search?q={requests.utils.quote(company)}+stock+news&hl=en"
        feed_articles = fetch_rss_feed(f"{company} News", url, max_per)
        for a in feed_articles:
            if company not in a.get("topics", []):
                a["topics"].append(company)
        articles.extend(feed_articles)
        time.sleep(0.2)
    return articles


# ── Orchestrator ──────────────────────────────────────────────────────────────

def fetch_all_news(
    prefs: dict,
    newsapi_key: str = "",
    include_hn: bool = True,
    include_reddit: bool = True,
    max_total: int = 200,
) -> list[dict]:
    """
    Master fetch function — pulls from all configured sources.
    Returns deduplicated list of raw articles.
    """
    topics = prefs.get("topics", [])
    keywords = prefs.get("keywords", [])
    companies = prefs.get("companies", [])
    sources = prefs.get("sources", [])

    all_articles: list[dict] = []

    # 1. RSS feeds
    rss = fetch_all_rss(selected_sources=sources if sources else None, max_per_feed=12)
    all_articles.extend(rss)

    # 2. Google News by topic
    gn = fetch_google_news(topics=topics, max_per=12)
    all_articles.extend(gn)

    # 3. Keyword search
    if keywords:
        kw_articles = fetch_keyword_news(keywords, max_per=8)
        all_articles.extend(kw_articles)

    # 4. Company news
    if companies:
        co_articles = fetch_company_news(companies, max_per=8)
        all_articles.extend(co_articles)

    # 5. NewsAPI
    if newsapi_key:
        na = fetch_newsapi(newsapi_key, keywords=keywords, topics=topics)
        all_articles.extend(na)

    # 6. Hacker News
    if include_hn:
        hn = fetch_hacker_news(max_items=20)
        all_articles.extend(hn)

    # 7. Reddit
    if include_reddit:
        rd = fetch_reddit(topics=topics, max_per=8)
        all_articles.extend(rd)

    # Deduplicate by ID
    seen: set = set()
    unique = []
    for a in all_articles:
        if a["id"] not in seen:
            seen.add(a["id"])
            unique.append(a)

    return unique[:max_total]
