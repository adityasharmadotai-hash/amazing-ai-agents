"""High-level AI insights across all analyzed emails."""
import os

from openai import OpenAI


def quick_stats(emails: list[dict]) -> dict:
    """Pure-Python counts for the dashboard cards (no AI cost)."""
    return {
        "total": len(emails),
        "high": sum(e["priority"] == "High" for e in emails),
        "medium": sum(e["priority"] == "Medium" for e in emails),
        "low": sum(e["priority"] == "Low" for e in emails),
        "pending": sum(e["status"] == "Pending" for e in emails),
        "completed": sum(e["status"] == "Completed" for e in emails),
    }


def top_urgent(emails: list[dict], limit: int = 5) -> list[dict]:
    """The most urgent open items."""
    return [
        e for e in emails
        if e["priority"] == "High" and e["status"] == "Pending"
    ][:limit]


def daily_summary(emails: list[dict]) -> str:
    """One paragraph AI overview of the whole inbox."""
    if not emails:
        return "No emails analyzed yet."

    lines = [
        f"- [{e['priority']}] {e['subject']} — {e['action_item']}"
        for e in emails[:40]
    ]
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content":
             "You are a chief-of-staff. Write a short, motivating morning "
             "briefing (4-6 sentences) covering the most urgent items, any "
             "likely missed follow-ups, and recommended next actions."},
            {"role": "user", "content": "\n".join(lines)},
        ],
        temperature=0.4,
    )
    return resp.choices[0].message.content.strip()
