"""
src/insights.py
---------------
Generates the higher-level "what should I do with my day" intelligence:

  * a daily inbox summary
  * the top urgent emails
  * likely missed follow-ups
  * recommended next actions

It works off the rows already stored in SQLite, so it costs exactly one OpenAI
call regardless of inbox size.
"""

from __future__ import annotations

import json
from typing import Optional

from openai import OpenAI

import config
from src import database

INSIGHTS_PROMPT = """You are a chief-of-staff reviewing a person's analyzed inbox.
Given the JSON list of emails (each with sender, subject, summary, action_item,
priority, due_date, status), respond with ONLY a JSON object with these keys:

  "daily_summary":      2-3 sentences describing the state of the inbox today
  "top_urgent":         array of up to 5 strings, each "Sender — short reason"
  "missed_followups":   array of strings for items that look overdue or stale
  "recommended_actions": array of up to 5 short imperative next steps

Be specific and concise. If a section has nothing, return an empty array.
"""


class InsightsEngine:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or config.OPENAI_API_KEY)
        self.model = model or config.OPENAI_MODEL

    def generate(self) -> dict:
        emails = database.get_all_emails()
        if not emails:
            return {
                "daily_summary": "No emails analyzed yet. Run a scan to get started.",
                "top_urgent": [],
                "missed_followups": [],
                "recommended_actions": [],
            }

        compact = [
            {
                "sender": e["sender"],
                "subject": e["subject"],
                "summary": e["summary"],
                "action_item": e["action_item"],
                "priority": e["priority"],
                "due_date": e["due_date"],
                "status": e["status"],
            }
            for e in emails[:60]  # cap context size
        ]

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": INSIGHTS_PROMPT},
                    {"role": "user", "content": json.dumps(compact)},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as exc:  # noqa: BLE001
            return {
                "daily_summary": f"Could not generate insights: {exc}",
                "top_urgent": [],
                "missed_followups": [],
                "recommended_actions": [],
            }
