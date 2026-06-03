"""
src/scheduler.py
----------------
Standalone daily automation.

Two ways to run it:

  1. As a long-lived process (uses the `schedule` library):
         python -m src.scheduler
     It will wake up every morning at the configured time and run the pipeline.

  2. As a one-shot for cron / GitHub Actions / Windows Task Scheduler:
         python -m src.pipeline
     (let the OS handle the timing — usually the more robust choice)
"""

from __future__ import annotations

import os
import time

import schedule

from src.pipeline import run_pipeline

RUN_AT = os.getenv("DAILY_RUN_TIME", "08:00")  # 24h local time


def job() -> None:
    print("[scheduler] running daily pipeline...")
    report = run_pipeline(last_hours=24)
    print(f"[scheduler] done: {report}")


def main() -> None:
    schedule.every().day.at(RUN_AT).do(job)
    print(f"[scheduler] started. Will run every day at {RUN_AT}. Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
