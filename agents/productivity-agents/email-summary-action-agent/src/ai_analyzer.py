"""
src/ai_analyzer.py
------------------
Turns a raw email into structured intelligence using the OpenAI API.

For each email we ask the model to return strict JSON with:
  * summary      -> one or two sentences
  * action_item  -> the concrete next step (or "None")
  * priority     -> High / Medium / Low (rules baked into the prompt)
  * due_date     -> ISO date if one is mentioned, else ""

Async support is provided via `analyze_many`, which fans out requests
concurrently so a 25-email inbox is analyzed in seconds, not minutes.
"""

from __future__ import annotations

import asyncio
import json
from typing import Optional

from openai import AsyncOpenAI, OpenAI

import config

SYSTEM_PROMPT = """You are an executive assistant that triages email.
For the email you are given, respond with ONLY a JSON object (no markdown,
no backticks) with exactly these keys:

  "summary":     a 1-2 sentence plain-English summary
  "action_item": the single concrete action required, or "None"
  "priority":    one of "High", "Medium", "Low"
  "due_date":    an ISO date (YYYY-MM-DD) if a deadline is mentioned, else ""

Priority rules (follow strictly):
  High   = requires an immediate response or action (deadlines, urgent asks,
           anything blocking the recipient or a customer)
  Medium = can be addressed within a few days (requests with no urgency,
           scheduling, reviews)
  Low    = promotions, newsletters, notifications, receipts, FYI emails
"""


def _build_user_prompt(email: dict) -> str:
    body = (email.get("body") or email.get("snippet") or "")[:6000]
    return (
        f"From: {email.get('sender', 'Unknown')}\n"
        f"Subject: {email.get('subject', '')}\n"
        f"Date: {email.get('date', '')}\n\n"
        f"Body:\n{body}"
    )


def _safe_parse(content: str) -> dict:
    """Parse model output defensively, stripping stray code fences."""
    cleaned = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "summary": cleaned[:300] or "Could not analyze.",
            "action_item": "None",
            "priority": "Low",
            "due_date": "",
        }

    # Normalize / validate
    priority = str(data.get("priority", "Low")).title()
    if priority not in config.PRIORITIES:
        priority = "Low"
    return {
        "summary": str(data.get("summary", "")).strip(),
        "action_item": str(data.get("action_item", "None")).strip() or "None",
        "priority": priority,
        "due_date": str(data.get("due_date", "")).strip(),
    }


class AIAnalyzer:
    """Synchronous + asynchronous OpenAI email analysis."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        key = api_key or config.OPENAI_API_KEY
        if not key:
            raise ValueError("OPENAI_API_KEY is not set. Add it to your .env file.")
        self.model = model or config.OPENAI_MODEL
        self.client = OpenAI(api_key=key)
        self.async_client = AsyncOpenAI(api_key=key)

    def analyze(self, email: dict) -> dict:
        """Analyze a single email (blocking)."""
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_prompt(email)},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            return _safe_parse(resp.choices[0].message.content)
        except Exception as exc:  # noqa: BLE001
            return {
                "summary": f"Analysis failed: {exc}",
                "action_item": "None",
                "priority": "Low",
                "due_date": "",
            }

    async def _analyze_async(self, email: dict, sem: asyncio.Semaphore) -> dict:
        async with sem:
            try:
                resp = await self.async_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": _build_user_prompt(email)},
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"},
                )
                return _safe_parse(resp.choices[0].message.content)
            except Exception as exc:  # noqa: BLE001
                return {
                    "summary": f"Analysis failed: {exc}",
                    "action_item": "None",
                    "priority": "Low",
                    "due_date": "",
                }

    async def analyze_many(self, emails: list[dict], concurrency: int = 5) -> list[dict]:
        """Analyze many emails concurrently and merge results back in."""
        sem = asyncio.Semaphore(concurrency)
        analyses = await asyncio.gather(*[self._analyze_async(e, sem) for e in emails])
        return [{**email, **analysis} for email, analysis in zip(emails, analyses)]
