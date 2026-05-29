"""
modules/scheduler.py
--------------------
Background scheduler for automatic news fetching and digest generation.
Uses threading with schedule library (no external daemon needed).
"""
from __future__ import annotations
import threading
import time
from datetime import datetime, timedelta
from typing import Callable

try:
    import schedule
    SCHEDULE_OK = True
except ImportError:
    SCHEDULE_OK = False


_scheduler_thread: threading.Thread | None = None
_stop_event = threading.Event()
_jobs: list[dict] = []


def _run_scheduler():
    """Background thread that runs scheduled jobs."""
    while not _stop_event.is_set():
        if SCHEDULE_OK:
            schedule.run_pending()
        time.sleep(30)  # check every 30 seconds


def start_scheduler():
    """Start the background scheduler thread."""
    global _scheduler_thread
    if _scheduler_thread and _scheduler_thread.is_alive():
        return
    _stop_event.clear()
    _scheduler_thread = threading.Thread(target=_run_scheduler, daemon=True)
    _scheduler_thread.start()


def stop_scheduler():
    _stop_event.set()


def schedule_daily_digest(fetch_fn: Callable, time_str: str = "06:00"):
    """Schedule a daily digest at a given UTC time (HH:MM)."""
    if not SCHEDULE_OK:
        return False
    schedule.clear("daily_digest")
    schedule.every().day.at(time_str).do(fetch_fn).tag("daily_digest")
    start_scheduler()
    return True


def schedule_hourly_fetch(fetch_fn: Callable):
    """Schedule an hourly news fetch."""
    if not SCHEDULE_OK:
        return False
    schedule.clear("hourly_fetch")
    schedule.every().hour.do(fetch_fn).tag("hourly_fetch")
    start_scheduler()
    return True


def get_next_run(time_str: str = "06:00") -> str:
    """Calculate the next scheduled run time."""
    now = datetime.now()
    h, m = map(int, time_str.split(":"))
    next_run = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(days=1)
    return next_run.strftime("%Y-%m-%d %H:%M:%S")


def is_running() -> bool:
    return _scheduler_thread is not None and _scheduler_thread.is_alive()


def run_now_async(fn: Callable) -> threading.Thread:
    """Run a function in a background thread immediately."""
    t = threading.Thread(target=fn, daemon=True)
    t.start()
    return t
