"""AI service powered by the OpenAI API.

Provides summarisation, classification, drafting, tone rewriting, meeting
briefs, executive briefings and voice-intent routing. Includes async batch
classification for fast inbox triage.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from openai import AsyncOpenAI, OpenAI

from config.settings import get_settings
from database.models import Email
from prompts import templates as P
from utils.helpers import gather_limited, retry, truncate
from utils.logging_config import get_logger

logger = get_logger(__name__)


class AIServiceError(Exception):
    pass


def _format_emails(emails: list[Email], max_body: int = 600) -> str:
    blocks = []
    for i, e in enumerate(emails, 1):
        when = e.received_at.strftime("%Y-%m-%d %H:%M") if e.received_at else "?"
        blocks.append(
            f"[{i}] From: {e.sender} <{e.sender_email}> | {when}\n"
            f"Subject: {e.subject}\n"
            f"Body: {truncate(e.body or e.snippet, max_body)}"
        )
    return "\n\n".join(blocks)


def _safe_json(text: str) -> dict[str, Any]:
    """Parse JSON, stripping any accidental code fences."""
    cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Attempt to locate the first JSON object.
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                pass
        logger.warning("Failed to parse JSON from model output.")
        return {}


class AIService:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.has_openai:
            raise AIServiceError("OPENAI_API_KEY is not configured.")
        self._client = OpenAI(api_key=self.settings.openai_api_key)
        self._aclient = AsyncOpenAI(api_key=self.settings.openai_api_key)

    # ------------------------------------------------------------------
    # Low-level completion helpers
    # ------------------------------------------------------------------
    @retry(attempts=3, base_delay=2.0)
    def _chat(self, system: str, user: str, *, model: Optional[str] = None,
              json_mode: bool = False, temperature: Optional[float] = None) -> str:
        kwargs: dict[str, Any] = {
            "model": model or self.settings.openai_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.settings.openai_temperature if temperature is None else temperature,
            "max_tokens": self.settings.openai_max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = self._client.chat.completions.create(**kwargs)
        return (resp.choices[0].message.content or "").strip()

    async def _achat(self, system: str, user: str, *, model: Optional[str] = None,
                     json_mode: bool = False) -> str:
        kwargs: dict[str, Any] = {
            "model": model or self.settings.openai_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.settings.openai_temperature,
            "max_tokens": self.settings.openai_max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = await self._aclient.chat.completions.create(**kwargs)
        return (resp.choices[0].message.content or "").strip()

    # ------------------------------------------------------------------
    # Summarisation
    # ------------------------------------------------------------------
    def summarize_inbox(self, emails: list[Email]) -> str:
        if not emails:
            return "_Inbox is empty — nothing to summarise._"
        prompt = P.INBOX_SUMMARY.format(count=len(emails), emails=_format_emails(emails))
        return self._chat(P.SYSTEM_ASSISTANT, prompt)

    def daily_digest(self, emails: list[Email]) -> str:
        if not emails:
            return "_No emails for today's digest._"
        return self._chat(P.SYSTEM_ASSISTANT, P.DAILY_DIGEST.format(emails=_format_emails(emails)))

    def weekly_summary(self, emails: list[Email]) -> str:
        if not emails:
            return "_No emails for this week._"
        return self._chat(
            P.SYSTEM_ASSISTANT,
            P.WEEKLY_SUMMARY.format(emails=_format_emails(emails)),
            model=self.settings.openai_reasoning_model,
        )

    # ------------------------------------------------------------------
    # Classification (sync single + async batch)
    # ------------------------------------------------------------------
    def classify_email(self, email: Email) -> dict[str, Any]:
        prompt = P.CLASSIFY_EMAIL.format(
            sender=email.sender, subject=email.subject,
            body=truncate(email.body or email.snippet, 1500),
        )
        return _safe_json(self._chat(P.SYSTEM_ASSISTANT, prompt, json_mode=True))

    async def _aclassify(self, email: Email) -> tuple[str, dict[str, Any]]:
        prompt = P.CLASSIFY_EMAIL.format(
            sender=email.sender, subject=email.subject,
            body=truncate(email.body or email.snippet, 1500),
        )
        result = _safe_json(await self._achat(P.SYSTEM_ASSISTANT, prompt, json_mode=True))
        return email.id, result

    async def classify_batch(self, emails: list[Email], concurrency: int = 5
                             ) -> dict[str, dict[str, Any]]:
        """Classify many emails concurrently. Returns {email_id: result}."""
        results = await gather_limited([self._aclassify(e) for e in emails], limit=concurrency)
        return dict(results)

    # ------------------------------------------------------------------
    # Follow-up
    # ------------------------------------------------------------------
    def suggest_followup(self, email: Email, tone: str = "professional") -> str:
        prompt = P.SUGGEST_FOLLOWUP.format(
            tone=P.TONE_GUIDE.get(tone, tone), sender=email.sender,
            subject=email.subject, body=truncate(email.body or email.snippet, 2000),
        )
        return self._chat(P.SYSTEM_DRAFTER, prompt)

    # ------------------------------------------------------------------
    # Drafting
    # ------------------------------------------------------------------
    def generate_draft(self, instructions: str, tone: str = "professional") -> dict[str, str]:
        prompt = P.GENERATE_DRAFT.format(
            tone=P.TONE_GUIDE.get(tone, tone), instructions=instructions
        )
        data = _safe_json(self._chat(P.SYSTEM_DRAFTER, prompt, json_mode=True))
        return {"subject": data.get("subject", "(no subject)"), "body": data.get("body", "")}

    def reply_with_context(self, thread: list[Email], tone: str = "professional",
                           instructions: str = "") -> str:
        thread_text = _format_emails(thread, max_body=1200)
        prompt = P.REPLY_WITH_CONTEXT.format(
            tone=P.TONE_GUIDE.get(tone, tone),
            instructions=instructions or "(none)",
            thread=thread_text,
        )
        return self._chat(P.SYSTEM_DRAFTER, prompt)

    def rewrite_tone(self, original: str, tone: str) -> str:
        prompt = P.REWRITE_TONE.format(tone=P.TONE_GUIDE.get(tone, tone), original=original)
        return self._chat(P.SYSTEM_DRAFTER, prompt)

    # ------------------------------------------------------------------
    # Meeting brief
    # ------------------------------------------------------------------
    def meeting_brief(self, title: str, when: str, attendees: list[str],
                      email_context: str) -> str:
        prompt = P.MEETING_BRIEF.format(
            title=title, when=when,
            attendees=", ".join(attendees) or "(none listed)",
            email_context=truncate(email_context, 4000) or "(no prior email context found)",
        )
        return self._chat(P.SYSTEM_ASSISTANT, prompt, model=self.settings.openai_reasoning_model)

    # ------------------------------------------------------------------
    # Executive briefing
    # ------------------------------------------------------------------
    def executive_briefing(self, owner: str, today: str, important_emails: str,
                           followup_emails: str, meetings: str) -> str:
        prompt = P.EXECUTIVE_BRIEFING.format(
            owner=owner or "the executive", today=today,
            important_emails=important_emails or "(none)",
            followup_emails=followup_emails or "(none)",
            meetings=meetings or "(none)",
        )
        return self._chat(
            P.SYSTEM_ASSISTANT, prompt, model=self.settings.openai_reasoning_model
        )

    # ------------------------------------------------------------------
    # Voice intent routing
    # ------------------------------------------------------------------
    def route_voice_intent(self, transcript: str) -> dict[str, Any]:
        prompt = P.VOICE_INTENT.format(transcript=transcript)
        data = _safe_json(self._chat(P.SYSTEM_ASSISTANT, prompt, json_mode=True, temperature=0.0))
        if "intent" not in data:
            data = {"intent": "unknown", "params": {}, "spoken_response": "Sorry, I didn't catch that."}
        data.setdefault("params", {})
        data.setdefault("spoken_response", "")
        return data
