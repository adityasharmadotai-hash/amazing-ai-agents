"""Analytics service — computes inbox-health and engagement metrics.

Works off the locally cached emails (plus a live `is:sent` pull for response
time) so the dashboard renders fast without re-hitting Gmail constantly.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from database.models import Email, get_cached_emails, get_top_contacts
from services.gmail_service import GmailService
from utils.helpers import now_utc
from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class InboxAnalytics:
    total_cached: int = 0
    unread_count: int = 0
    starred_count: int = 0
    important_count: int = 0
    followup_count: int = 0
    health_score: int = 0  # 0-100
    health_label: str = "Unknown"
    avg_response_hours: Optional[float] = None
    followup_rate: float = 0.0
    volume_by_day: dict[str, int] = field(default_factory=dict)
    top_contacts: list[dict] = field(default_factory=list)


def _compute_health(unread: int, total: int, followups: int) -> tuple[int, str]:
    if total == 0:
        return 100, "Inbox Zero"
    unread_ratio = unread / total
    followup_ratio = followups / total
    score = 100 - int(unread_ratio * 55) - int(followup_ratio * 35)
    score = max(0, min(100, score))
    label = (
        "Excellent" if score >= 80 else
        "Good" if score >= 60 else
        "Needs Attention" if score >= 40 else
        "Overloaded"
    )
    return score, label


class AnalyticsService:
    def __init__(self, gmail: Optional[GmailService] = None):
        self.gmail = gmail

    def _response_time_hours(self, sample: int = 25) -> Optional[float]:
        """Estimate average reply latency by matching sent replies to received."""
        if not self.gmail:
            return None
        try:
            sent = self.gmail.search("in:sent", max_results=sample)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not fetch sent mail for response time: %s", exc)
            return None
        received = {e.thread_id: e for e in get_cached_emails(limit=300)}
        deltas: list[float] = []
        for s in sent:
            orig = received.get(s.thread_id)
            if orig and orig.received_at and s.received_at and s.received_at > orig.received_at:
                deltas.append((s.received_at - orig.received_at).total_seconds() / 3600)
        return round(sum(deltas) / len(deltas), 1) if deltas else None

    def compute(self) -> InboxAnalytics:
        emails = get_cached_emails(limit=500)
        total = len(emails)
        unread = sum(1 for e in emails if e.is_unread)
        starred = sum(1 for e in emails if e.is_starred)
        important = sum(1 for e in emails if e.is_important)
        followups = sum(1 for e in emails if e.needs_followup)

        score, label = _compute_health(unread, total, followups)

        volume: Counter[str] = Counter()
        for e in emails:
            if e.received_at:
                volume[e.received_at.strftime("%Y-%m-%d")] += 1
        volume_sorted = dict(sorted(volume.items())[-14:])  # last 14 days

        return InboxAnalytics(
            total_cached=total,
            unread_count=unread,
            starred_count=starred,
            important_count=important,
            followup_count=followups,
            health_score=score,
            health_label=label,
            avg_response_hours=self._response_time_hours(),
            followup_rate=round(followups / total, 3) if total else 0.0,
            volume_by_day=volume_sorted,
            top_contacts=get_top_contacts(limit=10),
        )
