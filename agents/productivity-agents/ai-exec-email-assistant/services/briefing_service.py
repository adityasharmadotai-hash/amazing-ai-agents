"""Daily executive briefing orchestration (inbox-focused)."""
from __future__ import annotations

from datetime import datetime

from database.models import Email, save_briefing
from services.ai_service import AIService
from services.gmail_service import GmailService
from utils.helpers import run_async
from utils.logging_config import get_logger

logger = get_logger(__name__)


def _emails_block(emails: list[Email]) -> str:
    if not emails:
        return ""
    lines = []
    for e in emails:
        reason = f" — {e.ai_summary}" if e.ai_summary else ""
        lines.append(f"- {e.sender}: {e.subject}{reason}")
    return "\n".join(lines)


class BriefingService:
    def __init__(self, gmail: GmailService, ai: AIService):
        self.gmail = gmail
        self.ai = ai

    def generate(self, owner: str = "", classify_limit: int = 20) -> str:
        """Build and persist a daily executive briefing from the inbox."""
        today = datetime.now().strftime("%A, %d %B %Y")

        inbox = self.gmail.read_inbox(max_results=classify_limit)
        important: list[Email] = []
        followups: list[Email] = []
        if inbox:
            results = run_async(self.ai.classify_batch(inbox))
            for e in inbox:
                r = results.get(e.id, {})
                e.ai_summary = r.get("reason", "")
                e.priority_score = float(r.get("priority_score", 0) or 0)
                e.needs_followup = bool(r.get("needs_followup"))
                if r.get("is_important"):
                    important.append(e)
                if e.needs_followup:
                    followups.append(e)
            important.sort(key=lambda x: x.priority_score, reverse=True)

        content = self.ai.executive_briefing(
            owner=owner,
            today=today,
            important_emails=_emails_block(important[:8]),
            followup_emails=_emails_block(followups[:8]),
        )
        save_briefing(datetime.now().strftime("%Y-%m-%d"), content)
        return content
