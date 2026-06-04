"""
Analytics aggregation.

Pure read-side computations over the database that feed the dashboard:
source usage, trending topics, newsletter throughput/history and aggregate
engagement predictions. No external dependencies — everything is computed
from the SQLite tables so the dashboard is always available.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from modules import database as db
from modules.ai_research import trending_topics


def overview_metrics() -> dict:
    sources = db.list_sources()
    newsletters = db.list_newsletters()
    content = db.content_count()
    drafts = [n for n in newsletters if n.get("status") == "draft"]
    sent = [n for n in newsletters if n.get("status") == "sent"]
    avg_eng = (
        round(sum(n.get("engagement_score", 0) for n in newsletters) / len(newsletters), 1)
        if newsletters else 0
    )
    return {
        "total_sources": len(sources),
        "active_sources": len([s for s in sources if s.get("active")]),
        "total_content": content,
        "total_newsletters": len(newsletters),
        "drafts": len(drafts),
        "sent": len(sent),
        "avg_engagement": avg_eng,
    }


def source_usage() -> list[tuple[str, int]]:
    """Count content items grouped by source type."""
    items = db.query_content(limit=5000)
    counter = Counter(it.get("source_type", "Unknown") for it in items)
    return counter.most_common()


def trending() -> list[tuple[str, int]]:
    items = db.query_content(limit=1000)
    return trending_topics(items, top_n=10)


def newsletters_over_time(days: int = 30) -> list[tuple[str, int]]:
    """Daily count of created newsletters across the window."""
    newsletters = db.list_newsletters()
    cutoff = datetime.utcnow() - timedelta(days=days)
    buckets: Counter = Counter()
    for n in newsletters:
        try:
            created = datetime.fromisoformat(n["created_at"])
        except (ValueError, KeyError, TypeError):
            continue
        if created >= cutoff:
            buckets[created.strftime("%Y-%m-%d")] += 1
    out = []
    for i in range(days, -1, -1):
        day = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        out.append((day, buckets.get(day, 0)))
    return out


def engagement_by_style() -> list[tuple[str, float]]:
    newsletters = db.list_newsletters()
    grouped: dict[str, list[float]] = {}
    for n in newsletters:
        grouped.setdefault(n.get("style", "Unknown"), []).append(n.get("engagement_score", 0))
    return sorted(
        [(style, round(sum(v) / len(v), 1)) for style, v in grouped.items() if v],
        key=lambda x: x[1],
        reverse=True,
    )
