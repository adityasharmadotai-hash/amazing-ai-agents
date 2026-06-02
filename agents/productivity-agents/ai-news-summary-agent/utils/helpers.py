"""Reusable helper functions used across services."""
from __future__ import annotations

import asyncio
import base64
import functools
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Coroutine, Iterable, TypeVar

from utils.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Async helpers
# ---------------------------------------------------------------------------
def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Run an async coroutine from sync (Streamlit) code safely.

    Streamlit runs each script execution in a thread that may or may not
    already have a running event loop; this helper handles both cases.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Rare in Streamlit but handle gracefully with a fresh loop in a thread.
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(coro)).result()
    return asyncio.run(coro)


async def gather_limited(
    tasks: Iterable[Coroutine[Any, Any, T]], limit: int = 5
) -> list[T]:
    """Run coroutines with bounded concurrency."""
    semaphore = asyncio.Semaphore(limit)

    async def _wrap(c: Coroutine[Any, Any, T]) -> T:
        async with semaphore:
            return await c

    return await asyncio.gather(*[_wrap(t) for t in tasks])


# ---------------------------------------------------------------------------
# Retry decorator (handles transient API failures)
# ---------------------------------------------------------------------------
def retry(
    attempts: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for i in range(attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:  # noqa: BLE001
                    last_exc = exc
                    delay = base_delay * (2**i)
                    logger.warning(
                        "Attempt %s/%s for %s failed: %s. Retrying in %.1fs",
                        i + 1, attempts, func.__name__, exc, delay,
                    )
                    time.sleep(delay)
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Text / email parsing helpers
# ---------------------------------------------------------------------------
def decode_b64url(data: str) -> str:
    """Decode Gmail's base64url body payloads to UTF-8 text."""
    if not data:
        return ""
    padded = data + "=" * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return ""


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    text = _TAG_RE.sub(" ", text or "")
    return _WS_RE.sub(" ", text).strip()


def truncate(text: str, max_chars: int = 4000) -> str:
    text = text or ""
    return text if len(text) <= max_chars else text[:max_chars] + " …[truncated]"


def parse_header_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError):
        return None


_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def extract_email_address(from_header: str | None) -> str:
    if not from_header:
        return ""
    match = _EMAIL_RE.search(from_header)
    return match.group(0).lower() if match else from_header.strip().lower()


def extract_display_name(from_header: str | None) -> str:
    if not from_header:
        return ""
    name = re.sub(r"<[^>]+>", "", from_header).strip().strip('"')
    return name or extract_email_address(from_header)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
