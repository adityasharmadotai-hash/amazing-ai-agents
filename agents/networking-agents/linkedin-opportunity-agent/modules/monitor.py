"""
monitor.py — LinkedIn ingestion + the scan/analysis pipeline.

LinkedIn does not offer a public posts API and scraping it with raw credentials
violates their Terms of Service and is unreliable. This module therefore exposes
a **pluggable source interface** plus a built-in sample/simulation source so the
product is fully functional out of the box and on Streamlit Cloud.

To wire in real data, implement `fetch_posts()` against a compliant provider
(an official partner API, an authorised export, or a data vendor) and register
it via `set_source()`. Everything downstream — detection, scoring, outreach,
analytics — runs identically on whatever posts are ingested.
"""

from __future__ import annotations

import asyncio
import hashlib
import random
from datetime import datetime, timedelta, timezone

from . import ai, database as db, detector
from .samples import SAMPLE_POSTS

# ── Source registry ──────────────────────────────────────────────────────────────
_SOURCE = None  # callable(keywords, industries, limit) -> list[post dict]


def set_source(fn) -> None:
    """Register a custom post source. Signature: fn(keywords, industries, limit)."""
    global _SOURCE
    _SOURCE = fn


def _external_id(text: str, author: str) -> str:
    return hashlib.sha1(f"{author}|{text}".encode("utf-8")).hexdigest()[:16]


def _sample_source(keywords: list[str], industries: list[str], limit: int) -> list[dict]:
    """Built-in simulation source. Returns a fresh batch of realistic posts,
    lightly biased toward the user's configured keywords/industries."""
    bank = list(SAMPLE_POSTS)
    random.shuffle(bank)

    def relevance(p: dict) -> int:
        low = (p["text"] + " " + p.get("industry", "")).lower()
        score = sum(1 for k in keywords if k and k.lower() in low)
        score += sum(1 for i in industries if i and i.lower() in low)
        return score

    bank.sort(key=relevance, reverse=True)
    selected = bank[:limit]

    now = datetime.now(timezone.utc)
    posts = []
    for p in selected:
        posts.append(
            {
                # Stable id per (author, text) so the same sample is never
                # ingested twice across repeated scans.
                "external_id": _external_id(p["text"], p["author_name"]),
                "author_name": p["author_name"],
                "author_headline": p.get("author_headline", ""),
                "company": p.get("company", ""),
                "url": p.get("url", "https://www.linkedin.com/feed/"),
                "text": p["text"],
                "industry": p.get("industry", ""),
                "posted_at": (now - timedelta(hours=random.randint(1, 72))).isoformat(),
            }
        )
    return posts


def fetch_posts(keywords: list[str], industries: list[str], limit: int = 12) -> list[dict]:
    """Fetch new posts from the active source (custom if registered, else sample)."""
    source = _SOURCE or _sample_source
    return source(keywords, industries, limit)


def ingest_manual_post(
    text: str, author_name: str = "Manual entry", author_headline: str = "",
    company: str = "", industry: str = "", url: str = "",
) -> bool:
    """Add a single hand-pasted post to the queue. Returns True if newly added."""
    post = {
        "external_id": _external_id(text, author_name),
        "author_name": author_name or "Manual entry",
        "author_headline": author_headline,
        "company": company,
        "url": url or "https://www.linkedin.com/feed/",
        "text": text,
        "industry": industry,
        "posted_at": datetime.now(timezone.utc).isoformat(),
    }
    return db.upsert_post(post)


# ── Async analysis of many posts ─────────────────────────────────────────────────
async def _ai_analyze_many(posts: list[dict], keywords: list[str], industries: list[str]):
    """Analyse posts concurrently with Claude. Returns list of (post, result|None).

    A bounded semaphore keeps concurrency sane; any per-post failure falls back to
    the deterministic engine rather than dropping the post.
    """
    sem = asyncio.Semaphore(5)

    async def one(post):
        system, user = detector.build_ai_prompt(post, keywords, industries)
        async with sem:
            try:
                text = await ai.complete_async(system, user, max_tokens=700)
                data = ai.parse_json(text)
                result = detector.normalise_ai_response(data, post)
            except Exception:
                result = detector.fallback_analyze(post, keywords, industries)
        return post, result

    return await asyncio.gather(*(one(p) for p in posts))


def _analyze_all(posts: list[dict], keywords: list[str], industries: list[str]):
    """Analyse a batch, using async Claude calls when configured, else sync rules."""
    if ai.is_configured():
        try:
            return asyncio.run(_ai_analyze_many(posts, keywords, industries))
        except RuntimeError:
            # Already inside an event loop (rare in Streamlit) — fall back to serial.
            return [(p, detector.analyze_post(p, keywords, industries)) for p in posts]
    return [(p, detector.fallback_analyze(p, keywords, industries)) for p in posts]


# ── Top-level scan ───────────────────────────────────────────────────────────────
def run_scan(keywords: list[str], industries: list[str], limit: int = 12) -> dict:
    """Fetch new posts, analyse them, and persist any opportunities found.

    Returns a summary dict: {fetched, analyzed, opportunities, high, medium, low,
    engine}.
    """
    fetched = fetch_posts(keywords, industries, limit)
    new_count = 0
    for post in fetched:
        if db.upsert_post(post):
            new_count += 1

    pending = db.get_unprocessed_posts()
    results = _analyze_all(pending, keywords, industries)

    found = high = medium = low = 0
    for post, result in results:
        db.mark_post_processed(post["external_id"])
        if not result:
            continue
        if db.opportunity_exists(post["external_id"]):
            continue
        opp = {
            "post_external_id": post["external_id"],
            "person_name": post.get("author_name"),
            "person_headline": post.get("author_headline"),
            "company": post.get("company"),
            "profile_url": post.get("url"),
            "post_url": post.get("url"),
            "post_text": post.get("text"),
            **result,
        }
        db.add_opportunity(opp)
        found += 1
        if result["score_label"] == "High":
            high += 1
        elif result["score_label"] == "Medium":
            medium += 1
        else:
            low += 1

    return {
        "fetched": new_count,
        "analyzed": len(results),
        "opportunities": found,
        "high": high,
        "medium": medium,
        "low": low,
        "engine": "Claude" if ai.is_configured() else "Keyword fallback",
    }
