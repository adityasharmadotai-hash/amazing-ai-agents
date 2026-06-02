"""AI analysis of a single email using OpenAI."""
import asyncio
import json
import os

from openai import AsyncOpenAI, OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """You are an executive email assistant.
For the email you receive, return STRICT JSON with these keys:
- "summary": one or two sentences, plain and concise.
- "action_item": the single required action for the user, or "No action needed".
- "priority": exactly one of "High", "Medium", "Low".
- "due_date": an ISO date (YYYY-MM-DD) if a deadline is mentioned, else "".

Priority rules:
- High  = requires immediate response or action.
- Medium = can be addressed within a few days.
- Low   = promotions, newsletters, notifications, FYI emails.
Return ONLY the JSON object, nothing else.
"""


def _user_prompt(email: dict) -> str:
    return (
        f"From: {email.get('sender')}\n"
        f"Subject: {email.get('subject')}\n"
        f"Date: {email.get('date')}\n\n"
        f"Body:\n{email.get('body', '')}"
    )


def _safe_parse(content: str) -> dict:
    """Parse the model's JSON, falling back gracefully on failure."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {
            "summary": content[:200],
            "action_item": "Review manually",
            "priority": "Medium",
            "due_date": "",
        }
    priority = str(data.get("priority", "Medium")).title()
    if priority not in {"High", "Medium", "Low"}:
        priority = "Medium"
    return {
        "summary": data.get("summary", "").strip(),
        "action_item": data.get("action_item", "").strip(),
        "priority": priority,
        "due_date": data.get("due_date", "").strip(),
    }


def analyze_email(email: dict) -> dict:
    """Synchronous analysis of one email."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _user_prompt(email)},
        ],
        temperature=0.2,
    )
    result = _safe_parse(resp.choices[0].message.content)
    return {**email, **result, "status": "Pending"}


async def _analyze_one(client: AsyncOpenAI, email: dict) -> dict:
    resp = await client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _user_prompt(email)},
        ],
        temperature=0.2,
    )
    result = _safe_parse(resp.choices[0].message.content)
    return {**email, **result, "status": "Pending"}


async def analyze_batch(emails: list[dict]) -> list[dict]:
    """Analyze many emails concurrently — much faster for a full inbox."""
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    tasks = [_analyze_one(client, e) for e in emails]
    return await asyncio.gather(*tasks)
