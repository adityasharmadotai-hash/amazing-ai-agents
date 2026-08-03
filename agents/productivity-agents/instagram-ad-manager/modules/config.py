"""
config.py — shared constants and logging for the Instagram AI Ad Manager.

Central place for the app name, model id, default windows, and a logger factory
used across the modules and the background sync script.
"""

from __future__ import annotations

import logging
import os
import sys

APP_NAME = "Instagram AI Ad Manager"
APP_TAGLINE = "Premium AI Marketing Assistant"
GEMINI_MODEL = "gemini-2.5-pro"

# Default look-back window (days) for syncs and analytics.
DEFAULT_SYNC_DAYS = 70

# Benchmarks used by the deterministic health score (recruiting lead-gen).
BENCHMARKS = {
    "ctr": 1.5,          # %  — a healthy Instagram lead-ad CTR
    "cpl": 25.0,         # $  — target cost per lead
    "conversion": 6.0,   # %  — click → lead
    "quality_rate": 40.0,  # % — leads marked Qualified/Interview/Hired
}

_BASE = "admanager"
_LOG_CONFIGURED = False


def get_logger(name: str = _BASE) -> logging.Logger:
    """
    Return a configured logger. Handlers live on the shared `admanager` parent so
    every child (`admanager.sync`, `admanager.db`, …) emits through them.
    """
    global _LOG_CONFIGURED
    base = logging.getLogger(_BASE)
    if not _LOG_CONFIGURED:
        base.setLevel(logging.INFO)
        base.propagate = False  # don't double-log through the root logger
        fmt = logging.Formatter("%(asctime)s  %(levelname)-7s %(name)s: %(message)s", "%H:%M:%S")

        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        base.addHandler(sh)

        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            fh = logging.FileHandler(os.path.join(data_dir, "admanager.log"), encoding="utf-8")
            fh.setFormatter(fmt)
            base.addHandler(fh)
        except Exception:
            pass  # file logging is optional (read-only filesystems, etc.)

        _LOG_CONFIGURED = True

    if name == _BASE or name.startswith(_BASE + "."):
        return logging.getLogger(name)
    return logging.getLogger(f"{_BASE}.{name}")
