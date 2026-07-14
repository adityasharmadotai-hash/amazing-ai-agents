"""Central config — reads settings from the environment.

All env-derived values are computed inside `refresh()`, which is called once at
import and again whenever the Settings page changes a key (see
`st_common.apply_overrides`). This avoids `importlib.reload`, which is unsafe
under Streamlit's rerun model and was corrupting the `agent` package import.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "y"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _parse_list(raw: str) -> list[str]:
    """Split a comma / pipe / newline separated string into a clean list."""
    for sep in ("|", "\n", ";"):
        raw = raw.replace(sep, ",")
    return [s.strip() for s in raw.split(",") if s.strip()]


# ── Immutable constants ──────────────────────────────────────────────────────
_US_ALIASES = {"united states", "usa", "us", "u.s.", "u.s.a.", "america"}
_UNKNOWN_LOC = {"", "unknown", "none", "n/a", "null", "remote", "worldwide", "global"}

# Target job titles — only individuals whose role maps to one of these are kept.
# Override via TARGET_TITLES (comma / pipe / newline separated) to retarget the
# app at a different talent pool (e.g. data scientists, designers).
_DEFAULT_TITLES = [
    "Software Engineer", "Software Developer", "Senior Software Engineer",
    "Staff Software Engineer", "Principal Software Engineer",
    "Lead Software Engineer", "Full Stack Developer", "Frontend Developer",
    "Backend Developer", "Web Developer", "Mobile App Developer",
    "Android Developer", "iOS Developer", "Desktop Application Developer",
    "Application Developer", "Embedded Software Engineer", "Firmware Engineer",
    "Systems Engineer", "Platform Engineer", "Site Reliability Engineer",
    "DevOps Engineer", "Cloud Engineer", "Cloud Architect",
    "Infrastructure Engineer", "Build Engineer", "Release Engineer",
    "Automation Engineer", "QA Engineer", "Software Test Engineer",
    "Test Automation Engineer", "Performance Test Engineer", "Security Engineer",
    "Application Security Engineer", "Cybersecurity Engineer",
    "Solutions Architect", "Technical Architect",
]

# Default query set — BROAD nets, not per-title. The Gemini extractor reads the
# full post + headline and maps the role to a TARGET_TITLE; the filter enforces
# location + title. Override via LINKEDIN_QUERIES (one per line / pipe-separated).
_DEFAULT_QUERIES = [
    '"open to work" "software engineer" (laid off OR "impacted by the layoffs" OR layoff)',
    '"open to work" (developer OR engineer) "laid off" (software OR tech)',
    '"impacted by the layoffs" ("software engineer" OR "software developer" OR developer)',
    '"recently laid off" "open to work" (software OR engineer OR developer)',
    '#opentowork #layoff (software OR engineer OR developer)',
    '"open to work" "full stack" (laid off OR layoff OR "impacted by the layoffs")',
    '"open to work" (devops OR "site reliability" OR cloud OR platform OR infrastructure) engineer (laid off OR layoff)',
    '"open to work" (qa OR test OR "quality assurance" OR security) engineer (laid off OR layoff)',
    '"open to work" (android OR ios OR mobile OR frontend OR backend) developer (laid off OR layoff)',
    '"open to work" (embedded OR firmware OR systems OR automation OR architect) (laid off OR layoff)',
]


def refresh() -> None:
    """(Re)read every setting from os.environ. Called at import and after the
    Settings page changes a key. Mutating module globals in place means other
    modules that did `from . import config` see the new values immediately."""
    global GEMINI_API_KEY, SERPAPI_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY
    global WIZA_API_KEY, NEWSAPI_KEY
    global LINKEDIN_SOURCE, APIFY_TOKEN, APIFY_ACTOR, APIFY_DATE_FILTER
    global ENRICH_LOCATION, APIFY_PROFILE_ACTOR
    global APIFY_POST_COST_PER_1K, APIFY_PROFILE_COST_PER_1K
    global GEMINI_IN_COST_PER_1M, GEMINI_OUT_COST_PER_1M, SERPAPI_COST_PER_SEARCH
    global GEMINI_MODEL, LINKEDIN_RECENCY, LINKEDIN_RESULTS_PER_Q
    global LAYOFF_US_ONLY, SCAN_INTERVAL_HOURS
    global TARGET_TITLES, _TITLES_LOWER
    global TARGET_LOCATIONS, _LOCATIONS_LOWER, LOCATION_INCLUDE_UNKNOWN
    global LINKEDIN_QUERIES

    # Required
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

    # Optional integrations
    WIZA_API_KEY = os.getenv("WIZA_API_KEY", "")
    NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

    # LinkedIn backend
    LINKEDIN_SOURCE = os.getenv("LINKEDIN_SOURCE", "serpapi").strip().lower()
    APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
    APIFY_ACTOR = os.getenv("APIFY_ACTOR",
                            "apimaestro/linkedin-posts-search-scraper-no-cookies")
    APIFY_DATE_FILTER = os.getenv("APIFY_DATE_FILTER", "")
    ENRICH_LOCATION = _bool("ENRICH_LOCATION", True)
    APIFY_PROFILE_ACTOR = os.getenv("APIFY_PROFILE_ACTOR",
                                    "apimaestro/linkedin-profile-detail")

    # Cost-estimate rates (USD)
    APIFY_POST_COST_PER_1K = _float("APIFY_POST_COST_PER_1K", 3.0)
    APIFY_PROFILE_COST_PER_1K = _float("APIFY_PROFILE_COST_PER_1K", 5.0)
    GEMINI_IN_COST_PER_1M = _float("GEMINI_IN_COST_PER_1M", 0.30)
    GEMINI_OUT_COST_PER_1M = _float("GEMINI_OUT_COST_PER_1M", 2.50)
    SERPAPI_COST_PER_SEARCH = _float("SERPAPI_COST_PER_SEARCH", 0.01)

    # Tuning knobs
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    LINKEDIN_RECENCY = os.getenv("LINKEDIN_RECENCY", "w")
    LINKEDIN_RESULTS_PER_Q = _int("LINKEDIN_RESULTS_PER_Q", 20)
    LAYOFF_US_ONLY = _bool("LAYOFF_US_ONLY", False)
    SCAN_INTERVAL_HOURS = _int("SCAN_INTERVAL_HOURS", 4)

    # Target titles
    _titles_raw = os.getenv("TARGET_TITLES", "").strip()
    TARGET_TITLES = _parse_list(_titles_raw) if _titles_raw else list(_DEFAULT_TITLES)
    _TITLES_LOWER = {t.lower() for t in TARGET_TITLES}

    # Target locations (blank = worldwide; falls back to US when LAYOFF_US_ONLY)
    _loc_raw = os.getenv("TARGET_LOCATIONS", "").strip()
    if _loc_raw:
        TARGET_LOCATIONS = _parse_list(_loc_raw)
    elif LAYOFF_US_ONLY:
        TARGET_LOCATIONS = ["United States"]
    else:
        TARGET_LOCATIONS = []
    _LOCATIONS_LOWER = [c.lower() for c in TARGET_LOCATIONS]
    LOCATION_INCLUDE_UNKNOWN = _bool("LOCATION_INCLUDE_UNKNOWN", True)

    # Queries (one per line / pipe-separated; commas are NOT separators)
    raw = os.getenv("LINKEDIN_QUERIES", "").strip().replace("\n", "|")
    LINKEDIN_QUERIES = [q.strip() for q in raw.split("|") if q.strip()] or list(_DEFAULT_QUERIES)


# Compute all settings now, at import time.
refresh()


def is_target_title(title: str | None) -> bool:
    return bool(title) and title.strip().lower() in _TITLES_LOWER


def location_ok(rec: dict) -> bool:
    """True if a record's location matches the target locations (or if no
    location filter is configured, i.e. worldwide)."""
    if not _LOCATIONS_LOWER:
        return True
    if rec.get("is_us") and any(c in _US_ALIASES for c in _LOCATIONS_LOWER):
        return True
    hay = " ".join(str(rec.get(k) or "") for k in ("country", "location")).lower()
    if any(c in hay for c in _LOCATIONS_LOWER):
        return True
    # Benefit of the doubt: unknown/unstated country passes when enabled.
    if LOCATION_INCLUDE_UNKNOWN:
        country = (rec.get("country") or "").strip().lower()
        if country in _UNKNOWN_LOC:
            return True
    return False


def serp_geo() -> tuple[str | None, str | None]:
    """Google (gl, hl) bias for SerpAPI — only bias to the US when the US is the
    sole target location; otherwise search worldwide."""
    if _LOCATIONS_LOWER and all(c in _US_ALIASES for c in _LOCATIONS_LOWER):
        return "us", "en"
    return None, None


def missing_required() -> list[str]:
    """Return the names of required env vars that are unset (source-aware)."""
    required = {
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_SERVICE_KEY": SUPABASE_SERVICE_KEY,
    }
    if LINKEDIN_SOURCE == "apify":
        required["APIFY_TOKEN"] = APIFY_TOKEN
    else:
        required["SERPAPI_KEY"] = SERPAPI_KEY
    return [k for k, v in required.items() if not v]
