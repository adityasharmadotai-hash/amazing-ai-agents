"""Turn raw source snippets into structured layoff records via the LLM."""
from __future__ import annotations

import logging
import re
import threading
from typing import Any
from urllib.parse import unquote, urlparse

from . import config, llm

log = logging.getLogger(__name__)

# Last LLM/API error seen during extraction — surfaced by the pipeline so the UI
# can tell the user "your Gemini key/model is failing" instead of a silent 0.
_err_lock = threading.Lock()
_last_error: str | None = None


def reset_error() -> None:
    global _last_error
    with _err_lock:
        _last_error = None


def last_error() -> str | None:
    with _err_lock:
        return _last_error


def slug_text(url: str) -> str:
    """Recover human-readable keywords from a URL slug.

    SerpAPI only gives a thin snippet, but the URL itself is rich — e.g.
    '.../posts/jane_i-was-impacted-by-the-layoffs-across-xbox-share-7479...'
    yields 'i was impacted by the layoffs across xbox'. Feeding this to the
    LLM alongside the snippet recovers company / role / open-to-work signal
    that the snippet alone often misses.
    """
    try:
        path = unquote(urlparse(url).path)
    except Exception:  # noqa: BLE001
        return ""
    seg = path.rstrip("/").split("/")[-1]
    # LinkedIn: 'authorhandle_the-post-text-slug' -> keep text after first '_'
    if "_" in seg:
        seg = seg.split("_", 1)[1]
    # drop LinkedIn activity/share id tails and any long digit runs / hashes
    seg = re.sub(r"-(activity|share|ugcPost)-\d+.*$", "", seg)
    seg = re.sub(r"\.\w{2,5}$", "", seg)          # strip .html/.cms extensions
    seg = re.sub(r"\b\d{6,}\b", " ", seg)          # strip long numeric ids
    words = re.split(r"[-_]+", seg)
    words = [w for w in words if w and not w.isdigit()]
    return " ".join(words)

_SYSTEM = """You are a precise information-extraction engine for a recruitment \
team that tracks layoffs. You are given the text of a social/news post. \
Decide whether it describes a real layoff event or a person affected by one, \
then extract structured fields. Never invent facts — use null when unknown. \
Respond ONLY with a JSON object matching the requested schema."""

_USER_TEMPLATE = """Analyze the post below.

Return JSON with exactly these keys:
- is_layoff (boolean): true only if this describes an actual layoff or someone \
laid off / "open to work" because of one.
- is_individual (boolean): true if the post is by/about a specific laid-off \
PERSON (a potential recruiting candidate), false if it is company news, \
commentary, or an opinion piece.
- company (string|null): the company that conducted the layoff.
- person_name (string|null): the affected individual, if the poster IS the \
laid-off person.
- role_hint (string|null): the raw job title / function mentioned.
- role_category (string|null): map role_hint to the SINGLE closest title from \
the TARGET TITLES list below. Use the exact string from the list. If the role \
does not clearly match one of the target titles, return null.
- country (string|null): the person's country, normalized (e.g. "United \
States", "India", "Germany"). Infer from location, "based in", or context.
- is_us (boolean): true only if the person is based in the United States.
- headcount (integer|null): number of people laid off, if stated.
- location (string|null): city/state if stated.
- event_date (string|null): ISO date (YYYY-MM-DD) of the layoff if inferable.
- open_to_work (boolean): true if the person signals they are job-seeking \
(e.g. "#opentowork", "open to work", "looking for", "seeking new").
- summary (string): one neutral sentence (max 30 words).
- confidence (number): 0.0-1.0.

TARGET TITLES (role_category must be one of these exact strings, or null):
{titles}

Use BOTH the snippet and the URL-derived keywords below — the keywords often \
name the company/role even when the snippet is thin.

POST SOURCE URL: {url}
URL KEYWORDS: {slug}
POST TEXT:
\"\"\"
{text}
\"\"\"
"""

def extract_record(text: str, url: str) -> dict[str, Any] | None:
    """Return a structured record, or None if the text isn't a layoff signal."""
    slug = slug_text(url)
    if not (text and text.strip()) and not slug:
        return None
    try:
        data = llm.complete_json(
            _SYSTEM,
            _USER_TEMPLATE.format(url=url, slug=slug or "(none)",
                                  text=(text or "")[:6000],
                                  titles=", ".join(config.TARGET_TITLES)),
        )
    except Exception as exc:  # noqa: BLE001 — one bad post shouldn't kill a scan
        global _last_error
        with _err_lock:
            _last_error = str(exc)
        log.warning("extraction failed for %s: %s", url, exc)
        return None

    if not isinstance(data, dict) or not data.get("is_layoff"):
        return None

    data["source_url"] = url
    return data


def is_relevant(rec: dict[str, Any]) -> bool:
    """A record is a qualified recruiting lead if it is a laid-off individual in
    a target location. When REQUIRE_TARGET_TITLE is on, the role must also map to
    one of the TARGET_TITLES; otherwise any role qualifies (capture-everyone)."""
    if not rec:
        return False
    if not rec.get("is_individual"):
        return False
    if not config.location_ok(rec):
        return False
    if not config.REQUIRE_TARGET_TITLE:
        return True
    # trust the model's role_category, but re-validate against the canonical list
    return config.is_target_title(rec.get("role_category"))
