"""Background scheduler — runs run_scan() every SCAN_INTERVAL_HOURS (default 4).

Run standalone:  python scheduler.py
Or let app.py start it in-process (see app.py lifespan).
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

from agent import config
from agent.pipeline import run_scan

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("scheduler")


def _job() -> None:
    try:
        run_scan()
    except Exception:  # noqa: BLE001 — a failed scan must not kill the scheduler
        log.exception("Scheduled scan failed")


def attach(scheduler: BackgroundScheduler) -> None:
    """Register the recurring job on an existing scheduler (used by app.py)."""
    scheduler.add_job(_job, "interval", hours=config.SCAN_INTERVAL_HOURS,
                      id="layoff_scan", replace_existing=True, max_instances=1)


if __name__ == "__main__":
    missing = config.missing_required()
    if missing:
        log.warning("Missing required env vars: %s (scans will error).", ", ".join(missing))
    sched = BlockingScheduler()
    sched.add_job(_job, "interval", hours=config.SCAN_INTERVAL_HOURS,
                  id="layoff_scan", next_run_time=None)
    log.info("Scheduler started — scanning every %sh. Ctrl-C to stop.",
             config.SCAN_INTERVAL_HOURS)
    _job()  # run once immediately on boot
    sched.start()
