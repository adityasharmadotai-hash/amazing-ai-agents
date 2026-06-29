"""Display formatting helpers."""

from __future__ import annotations


def format_duration(milliseconds: float) -> str:
    """Format a millisecond duration for human display."""
    if milliseconds < 1:
        return f"{milliseconds * 1000:.0f} µs"
    if milliseconds < 1000:
        return f"{milliseconds:.1f} ms"
    return f"{milliseconds / 1000:.2f} s"


def human_bytes(num: int) -> str:
    """Format a byte count as a human-readable string."""
    size = float(num)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def truncate_text(text: str, max_length: int = 120) -> str:
    if text is None:
        return ""
    return text if len(text) <= max_length else text[: max_length - 1] + "…"
