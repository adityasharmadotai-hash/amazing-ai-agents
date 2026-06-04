"""
Automation / scheduling engine.

Schedules describe a recurring job: "every Week, build an AI Newsletter on
topic X in Thought-Leadership mode". This module computes next-run times,
detects which schedules are due, and runs the end-to-end pipeline
(collect → research → generate → save draft) for a due schedule.

Streamlit has no always-on background worker, so the design is pull-based:
whenever the app loads (or the user clicks "Run due schedules"), we check for
due jobs and execute them. ``next_run`` is advanced after each run. This keeps
the system deterministic and dependency-free while still being "automatic".
"""

from __future__ import annotations

from datetime import datetime, timedelta

from modules import database as db
from modules.ai_research import research
from modules.content_sources import collect_all
from modules.llm import LLMClient
from modules.newsletter_generator import generate_newsletter

FREQ_DELTA = {
    "Daily": timedelta(days=1),
    "Weekly": timedelta(weeks=1),
    "Monthly": timedelta(days=30),
}


def compute_next_run(frequency: str, from_dt: datetime | None = None) -> str:
    base = from_dt or datetime.utcnow()
    return (base + FREQ_DELTA.get(frequency, timedelta(weeks=1))).isoformat(timespec="seconds")


def due_schedules(now: datetime | None = None) -> list[dict]:
    now = now or datetime.utcnow()
    due = []
    for s in db.list_schedules():
        if not s.get("active"):
            continue
        nxt = s.get("next_run")
        if not nxt:
            due.append(s)
            continue
        try:
            if datetime.fromisoformat(nxt) <= now:
                due.append(s)
        except ValueError:
            due.append(s)
    return due


def run_schedule(schedule: dict, llm: LLMClient) -> dict:
    """Execute the full pipeline for one schedule and persist a draft."""
    topic = schedule.get("topic") or "Industry News"
    industry = schedule.get("industry") or "General Technology"

    # Gather matching active sources (by topic/industry, else all active)
    all_sources = db.list_sources(active_only=True)
    sources = [
        s for s in all_sources
        if (not s.get("topic") or s["topic"] == topic)
        or (not s.get("industry") or s["industry"] == industry)
    ] or all_sources

    items = collect_all(sources)
    for it in items:
        db.upsert_content_item(it)
    for s in sources:
        db.mark_source_fetched(s["id"])

    research_data = research(items, topic, llm)
    newsletter = generate_newsletter(
        topic=topic,
        industry=industry,
        style=schedule.get("style") or "AI Newsletter",
        writing_mode=schedule.get("writing_mode") or "Professional",
        research_data=research_data,
        llm=llm,
        references=research_data.get("ranked_items", [])[:12],
    )
    newsletter["status"] = "draft"
    news_id = db.save_newsletter(newsletter)

    now = datetime.utcnow()
    db.update_schedule(schedule["id"], {
        "last_run": now.isoformat(timespec="seconds"),
        "next_run": compute_next_run(schedule.get("frequency", "Weekly"), now),
    })
    db.log_event("schedule_run", {"schedule_id": schedule["id"], "newsletter_id": news_id})
    return {"newsletter_id": news_id, "title": newsletter.get("title"), "items": len(items)}


def run_due(llm: LLMClient) -> list[dict]:
    """Run every due schedule. Returns a list of run summaries."""
    results = []
    for sched in due_schedules():
        try:
            results.append(run_schedule(sched, llm))
        except Exception as exc:
            db.log_event("schedule_error", {"schedule_id": sched.get("id"), "error": str(exc)})
    return results
