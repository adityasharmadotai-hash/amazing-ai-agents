"""Centralised logging configuration.

Logs are written both to stderr (for Streamlit's console) and to a rotating
file under the configured ``log_dir``. The application logs questions, generated
SQL, execution times, errors and database metadata as required.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

_CONFIGURED = False

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(log_dir: str = "logs", level: str = "INFO") -> None:
    """Configure root logging once for the whole application.

    Safe to call multiple times — only the first call takes effect.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    os.makedirs(log_dir, exist_ok=True)
    log_level = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(log_level)

    formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT)

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(log_level)
    root.addHandler(console)

    # Rotating file handler
    file_path = os.path.join(log_dir, "app.log")
    file_handler = RotatingFileHandler(
        file_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    root.addHandler(file_handler)

    # Tame noisy third-party loggers.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a module-level logger, configuring logging on first use."""
    if not _CONFIGURED:
        configure_logging()
    return logging.getLogger(name if name else "ai_db_analyst")
