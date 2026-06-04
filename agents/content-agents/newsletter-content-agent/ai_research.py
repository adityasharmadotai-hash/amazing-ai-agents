"""
AI research layer.

Takes a pool of collected content items for a topic and produces the analytical
building blocks a newsletter needs:

* trending ranking (heuristic + recency, optionally LLM re-ranked)
* key insights
* extracted statistics / data points
* concise per-cluster summaries

All LLM calls degrade gracefully: when no API key is present, deterministic
heuristic versions are returned so the pipeline always yields usable output.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone

from modules.llm import LLMClient

_STOPWORDS = set(
    "the a an and or but of to in on for with at by from as is are was were be been "
    "this that these those it its their our your you we they he she his her i how what "
    "why when where which who whom new now top best via amp".split()
)


# --------------------------------------------------------------------------- #
# Heuristic trending score
# --------------------------------------------------------------------------- #
def _recency_weight(published: str | None) -> float:
    if not published:
        return 0.5
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            dt = datetime.strptime(published[:31], fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - dt).total_seconds() / 86400
            return max(0.1, 1.0 - min(age_days, 30) / 30)
        except (ValueError, TypeError):
            continue
    return 0.5


def score_trending(items: list[dict]) -> list[dict]:
    """Assign a composite trend score and return items sorted high→low."""
    if not items:
        return []
    # term frequency across the corpus → topical density
    corpus = Counter()
    for it in items:
        for w in re.findall(r"[a-z]{4,}", (it.get("title", "") + " " + it.get("summary", "")).lower()):
            if w not in _STOPWORDS:
                corpus[w] += 1

    scored = []
    for it in items:
        base = float(it.get("score", 0) or 0)
        recency = _recency_weight(it.get("published_at"))
        text = (it.get("title", "") + " " + it.get("summary", "")).lower()
        density = sum(corpus[w] for w in set(re.findall(r"[a-z]{4,}", text)) if w not in _STOPWORDS)
        composite = (recency * 5) + (density * 0.15) + (base * 0.05)
        if base < 0:  # placeholder / error item
            composite = -1
        it = dict(it)
        it["trend_score"] = round(composite, 2)
        scored.append(it)
    scored.sort(key=lambda x: x["trend_score"], reverse=True)
    return scored


def trending_topics(items: list[dict], top_n: int = 8) -> list[tuple[str, int]]:
    """Extract the most common multi-word-ish keywords as trending topics."""
    counter = Counter()
    for it in items:
        for w in re.findall(r"[A-Za-z]{4,}", it.get("title", "")):
            wl = w.lower()
            if wl not in _STOPWORDS:
                counter[w.title()] += 1
    return counter.most_common(top_n)


# --------------------------------------------------------------------------- #
# LLM-powered analysis
# --------------------------------------------------------------------------- #
def _format_items_for_prompt(items: list[dict], limit: int = 20) -> str:
    lines = []
    for i, it in enumerate(items[:limit], 1):
        lines.append(
            f"{i}. {it.get('title')} "
            f"[{it.get('source_name')} / {it.get('source_type')}]\n"
            f"   {(it.get('summary') or '')[:300]}"
        )
    return "\n".join(lines)


def research(items: list[dict], topic: str, llm: LLMClient) -> dict:
    """Return {'insights', 'statistics', 'summary', 'clusters'} for the topic."""
    items = [it for it in score_trending(items) if it.get("trend_score", 0) >= 0]
    if not items:
        return {"insights": [], "statistics": [], "summary": "", "clusters": []}

    if not llm.available:
        return _heuristic_research(items, topic)

    system = (
        "You are a sharp newsletter research analyst. You read a batch of recent "
        "content items and distil the signal: the genuinely important developments, "
        "the hard numbers, and a crisp synthesis. Be specific and avoid fluff."
    )
    user = (
        f"Topic: {topic}\n\n"
        f"Here are {min(len(items), 20)} recent content items:\n\n"
        f"{_format_items_for_prompt(items)}\n\n"
        "Analyse them and return JSON with this exact shape:\n"
        "{\n"
        '  "summary": "2-3 sentence synthesis of what is happening in this space",\n'
        '  "insights": ["5-7 specific, non-obvious key insights"],\n'
        '  "statistics": ["important numbers/stats mentioned, each with brief context"],\n'
        '  "clusters": [{"theme": "...", "item_indices": [1,2], "takeaway": "..."}]\n'
        "}"
    )
    try:
        data = llm.complete_json(system, user, temperature=0.4)
        data.setdefault("insights", [])
        data.setdefault("statistics", [])
        data.setdefault("summary", "")
        data.setdefault("clusters", [])
        data["ranked_items"] = items
        return data
    except Exception:
        return _heuristic_research(items, topic)


def _heuristic_research(items: list[dict], topic: str) -> dict:
    """Deterministic fallback used when the LLM is unavailable."""
    stats = []
    stat_pattern = re.compile(r"(\$?\d[\d,\.]*\s?(?:%|percent|million|billion|x|k|M|B)?)", re.I)
    for it in items[:30]:
        for match in stat_pattern.findall(it.get("summary", "") or ""):
            if any(c.isdigit() for c in match) and len(match) > 1:
                stats.append(f"{match.strip()} — {it.get('title')[:80]}")
        if len(stats) >= 8:
            break

    insights = [f"{it.get('title')}" for it in items[:6]]
    summary = (
        f"This edition tracks {len(items)} recent items on {topic}. "
        f"The most prominent thread is '{items[0].get('title')}'."
    )
    return {
        "summary": summary,
        "insights": insights,
        "statistics": stats[:8],
        "clusters": [],
        "ranked_items": items,
    }
