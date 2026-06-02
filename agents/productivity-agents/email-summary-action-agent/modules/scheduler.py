"""Daily automation with APScheduler."""
import asyncio

from apscheduler.schedulers.background import BackgroundScheduler

from . import analyzer, database, gmail_client, sheets_client


def run_pipeline(mode: str = "last_24h", sheet_name: str = "Email Action Items"):
    """Fetch -> skip seen -> analyze -> store -> push to Sheet."""
    database.init_db()
    service = gmail_client.get_gmail_service()
    emails = gmail_client.fetch_emails(service, mode=mode)

    fresh = [e for e in emails if not database.already_processed(e["email_id"])]
    if not fresh:
        return []

    analyzed = asyncio.run(analyzer.analyze_batch(fresh))
    for record in analyzed:
        database.save_email(record)

    try:
        ws = sheets_client.get_sheet(sheet_name)
        sheets_client.append_rows(ws, analyzed)
    except Exception as exc:  # keep local data even if Sheets fails
        print(f"[scheduler] Sheets sync skipped: {exc}")
    return analyzed


def start_daily(hour: int = 7, minute: int = 0):
    """Start a background job that runs every morning at HH:MM."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_pipeline, "cron", hour=hour, minute=minute)
    scheduler.start()
    return scheduler


if __name__ == "__main__":
    # Run the pipeline once from the command line.
    results = run_pipeline()
    print(f"Analyzed {len(results)} new emails.")
