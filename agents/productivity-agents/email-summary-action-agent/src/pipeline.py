"""
src/pipeline.py
---------------
The orchestrator. One function, `run_pipeline`, ties everything together:

    Gmail  ->  AI analysis  ->  SQLite  ->  Google Sheet

This is what both the dashboard button and the daily scheduler call. Keeping the
flow in one place means the UI and the cron job can never drift apart.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import config
from src import database, settings
from src.ai_analyzer import AIAnalyzer
from src.gmail_client import GmailClient, get_credentials
from src.sheets_client import SheetsClient


def run_pipeline(
    max_emails: int = config.DEFAULT_MAX_EMAILS,
    label: str = config.DEFAULT_LABEL,
    unread_only: bool = False,
    last_hours: Optional[int] = None,
    push_to_sheet: bool = True,
) -> dict:
    """Run a full scan. Returns a small report dict for the UI / logs."""
    database.init_db()
    creds = get_credentials()

    # 1. Fetch
    gmail = GmailClient(creds)
    emails = gmail.fetch_emails(
        max_results=max_emails,
        label=label,
        unread_only=unread_only,
        last_hours=last_hours,
    )

    # 2. Skip anything we have already analyzed (cheap dedupe before paying OpenAI)
    fresh = [e for e in emails if not database.email_exists(e["id"])]
    if not fresh:
        return {"fetched": len(emails), "new": 0, "written_to_sheet": 0}

    # 3. Analyze concurrently (key + model come from the Settings page / .env)
    api_key = settings.get_openai_key()
    if not api_key:
        raise RuntimeError(
            "No OpenAI API key configured. Open the ⚙️ Settings page to add one "
            "(or set OPENAI_API_KEY in your .env)."
        )
    analyzer = AIAnalyzer(api_key=api_key, model=settings.get_model())
    analyzed = asyncio.run(analyzer.analyze_many(fresh))

    # 4. Persist locally
    saved = []
    for record in analyzed:
        record["status"] = "Pending"
        if database.insert_email(record):
            saved.append(record)

    # 5. Mirror to Google Sheet
    written = 0
    if push_to_sheet and saved:
        sheets = SheetsClient(creds)
        written = sheets.append_rows(saved)

    database.set_meta("last_run", _now())
    return {"fetched": len(emails), "new": len(saved), "written_to_sheet": written}


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    # Allows: `python -m src.pipeline` from cron / Task Scheduler / GitHub Actions
    report = run_pipeline(last_hours=24)
    print(f"Daily run complete: {report}")
