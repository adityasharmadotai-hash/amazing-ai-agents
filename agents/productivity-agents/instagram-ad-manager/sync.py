#!/usr/bin/env python3
"""
sync.py — background sync for the Instagram AI Ad Manager.

Streamlit cannot run autonomous jobs, so this standalone script does the periodic
work: pull Meta Ads data + leads, run Gemini analysis, generate recommendations,
save AI history, refresh notifications, and update the SQLite database. The
Streamlit app then just displays the latest synchronized data.

Run it from GitHub Actions (preferred), cron, or Windows Task Scheduler:

    python sync.py                 # live Meta sync + AI (uses env vars)
    python sync.py --days 30       # shorter window
    python sync.py --no-ai         # data only, skip Gemini
    python sync.py --sample        # seed the demo dataset (no Meta needed)

Environment variables (or a .env file):
    GEMINI_API_KEY, META_ACCESS_TOKEN, META_AD_ACCOUNT_ID
    ADMANAGER_DB_PATH   (optional) — shared/persistent SQLite path
"""

from __future__ import annotations

import argparse
import os
import sys

# Load .env if python-dotenv is available (optional convenience).
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules import config, sync_service  # noqa: E402

log = config.get_logger("admanager.cli")


def main() -> int:
    parser = argparse.ArgumentParser(description="Background sync for the Instagram AI Ad Manager.")
    parser.add_argument("--days", type=int, default=config.DEFAULT_SYNC_DAYS,
                        help="History window to pull (default: %(default)s).")
    parser.add_argument("--no-ai", action="store_true", help="Skip the Gemini AI stage.")
    parser.add_argument("--sample", action="store_true",
                        help="Seed the demo dataset instead of pulling from Meta.")
    parser.add_argument("--source", default="scheduled",
                        help="Label recorded in the sync log (default: %(default)s).")
    parser.add_argument("--force-recs", action="store_true",
                        help="Generate recommendations even if today already has some.")
    args = parser.parse_args()

    log.info("Starting sync (source=%s, days=%d, ai=%s, sample=%s)",
             args.source, args.days, not args.no_ai, args.sample)

    result = sync_service.run_sync(
        days=args.days, source=args.source, run_ai=not args.no_ai,
        use_sample=args.sample, force_recs=args.force_recs,
    )

    for m in result.get("messages", []):
        log.info("• %s", m)

    if result.get("ok"):
        log.info("Sync finished with status: %s", result["status"])
        return 0
    log.error("Sync failed: %s", result.get("error", "unknown error"))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
