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


def _parse_locations(raw: str) -> list[str]:
    """Split target locations on pipe / semicolon / newline ONLY.

    Unlike `_parse_list`, this does NOT split on commas, so a place name that
    contains a comma — "San Francisco, California" — is kept as a single
    location instead of being torn into "San Francisco" and "California".
    """
    for sep in ("|", "\n", ";"):
        raw = raw.replace(sep, "\x00")
    return [s.strip() for s in raw.split("\x00") if s.strip()]


# ── Immutable constants ──────────────────────────────────────────────────────
_US_ALIASES = {"united states", "usa", "us", "u.s.", "u.s.a.", "america"}
_UNKNOWN_LOC = {"", "unknown", "none", "n/a", "null", "remote", "worldwide", "global"}

# All LinkedIn discovery providers. Gemini is excluded from "all"/merge mode
# because Google Search grounding cannot reach individual LinkedIn posts (it
# returns 0) — but it stays selectable explicitly for anyone who wants it.
_ALL_PROVIDERS = ("serpapi", "apify", "perplexity", "gemini")

# Default query set — BROAD layoff coverage for BOTH company/event announcements
# AND laid-off individuals. Deliberately does NOT require "open to work" (that
# gate was excluding the large majority of layoff posts). Each line is one search
# per provider (SerpAPI paginates it, Apify expands its OR-variants, Perplexity
# runs it as one search), so more lines = more coverage but more cost. Override
# via LINKEDIN_QUERIES; trim lines to cut cost.
_DEFAULT_QUERIES = [
    # Individuals: laid off AND job-seeking (the classic recruiting lead).
    '("laid off" OR "impacted by the layoffs" OR "let go" OR "lost my job" OR '
    '"role was eliminated") ("open to work" OR "seeking new" OR "new opportunities")',
    # Individuals via hashtags.
    '#opentowork (#layoff OR #layoffs OR "laid off" OR "let go")',
    # Broad individual layoff mentions — NO open-to-work gate (captures people who
    # just announce they were laid off without the exact phrase).
    '("laid off" OR "impacted by layoffs" OR "affected by the layoffs" OR '
    '"part of the layoffs" OR "recently laid off" OR "just got laid off")',
    # Company / event announcements (names the company doing the layoffs).
    '(#layoffs OR #layoff OR "layoffs at" OR "laying off" OR "reduction in force" '
    'OR "workforce reduction" OR "cutting jobs" OR "job cuts")',
    # Reorg / RIF phrasing companies and employees use.
    '("reduction in force" OR "we had to let go" OR "difficult decision to reduce" '
    'OR "position was eliminated" OR "no longer with" OR "restructuring")',
]


def refresh() -> None:
    """(Re)read every setting from os.environ. Called at import and after the
    Settings page changes a key. Mutating module globals in place means other
    modules that did `from . import config` see the new values immediately."""
    global GEMINI_API_KEY, SERPAPI_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY
    global WIZA_API_KEY, NEWSAPI_KEY
    global LINKEDIN_SOURCE, APIFY_TOKEN, APIFY_ACTOR, APIFY_DATE_FILTER
    global ENRICH_LOCATION, APIFY_PROFILE_ACTOR
    global PERPLEXITY_API_KEY, PERPLEXITY_COST_PER_SEARCH
    global APIFY_POST_COST_PER_1K, APIFY_PROFILE_COST_PER_1K
    global GEMINI_IN_COST_PER_1M, GEMINI_OUT_COST_PER_1M, SERPAPI_COST_PER_SEARCH
    global GEMINI_MODEL, LINKEDIN_RECENCY, LINKEDIN_RECENCY_DAYS, LINKEDIN_RESULTS_PER_Q
    global SCAN_INTERVAL_HOURS
    global TARGET_LOCATIONS, _LOCATIONS_LOWER, LOCATION_INCLUDE_UNKNOWN
    global LOCATION_IN_SEARCH
    global LINKEDIN_QUERIES, APIFY_MAX_KEYWORD_VARIANTS

    # Required
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

    # Optional integrations
    WIZA_API_KEY = os.getenv("WIZA_API_KEY", "")
    NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

    # LinkedIn backend. Default "all" = merge every provider you have a key for
    # (SerpAPI + Apify + Perplexity), run concurrently and dedupe. May also be a
    # single provider name or a comma/space list. See active_sources().
    LINKEDIN_SOURCE = os.getenv("LINKEDIN_SOURCE", "all").strip().lower()
    APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
    APIFY_ACTOR = os.getenv("APIFY_ACTOR",
                            "apimaestro/linkedin-posts-search-scraper-no-cookies")
    APIFY_DATE_FILTER = os.getenv("APIFY_DATE_FILTER", "")
    ENRICH_LOCATION = _bool("ENRICH_LOCATION", True)
    APIFY_PROFILE_ACTOR = os.getenv("APIFY_PROFILE_ACTOR",
                                    "apimaestro/linkedin-profile-detail")

    # Perplexity web-search backend (uses the /search endpoint — no model param)
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

    # Cost-estimate rates (USD)
    APIFY_POST_COST_PER_1K = _float("APIFY_POST_COST_PER_1K", 3.0)
    APIFY_PROFILE_COST_PER_1K = _float("APIFY_PROFILE_COST_PER_1K", 5.0)
    GEMINI_IN_COST_PER_1M = _float("GEMINI_IN_COST_PER_1M", 0.30)
    GEMINI_OUT_COST_PER_1M = _float("GEMINI_OUT_COST_PER_1M", 2.50)
    SERPAPI_COST_PER_SEARCH = _float("SERPAPI_COST_PER_SEARCH", 0.01)
    # Perplexity Sonar bills per request + tokens; a per-search estimate keeps the
    # dashboard simple. Override PERPLEXITY_COST_PER_SEARCH to match your plan.
    PERPLEXITY_COST_PER_SEARCH = _float("PERPLEXITY_COST_PER_SEARCH", 0.006)

    # Tuning knobs
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    # Recency: LINKEDIN_RECENCY_DAYS is the primary, user-facing control (default
    # 3 = only posts from the last 3 days). When > 0 the SerpAPI backend uses an
    # exact N-day Google date range; the Apify/Perplexity backends map it to the
    # nearest bucket (24h/week/month/year). The legacy single-letter
    # LINKEDIN_RECENCY (d/w/m/y) is only a fallback when LINKEDIN_RECENCY_DAYS=0.
    LINKEDIN_RECENCY_DAYS = _int("LINKEDIN_RECENCY_DAYS", 3)
    LINKEDIN_RECENCY = os.getenv("LINKEDIN_RECENCY", "w")
    # Higher default than before (was 20) — coverage is the goal now. Each unit is
    # one more result pulled per query per provider (higher = more cost).
    LINKEDIN_RESULTS_PER_Q = _int("LINKEDIN_RESULTS_PER_Q", 30)
    # Apify: max number of distinct keyword searches to run per scan (each is one
    # paid actor run). Variants are pulled from all queries, deduped, then capped
    # here. Higher = more coverage, more cost.
    APIFY_MAX_KEYWORD_VARIANTS = _int("APIFY_MAX_KEYWORD_VARIANTS", 8)
    SCAN_INTERVAL_HOURS = _int("SCAN_INTERVAL_HOURS", 4)

    # Target locations (blank = worldwide). Cities/regions are allowed
    # ("San Francisco, California"), so we split on pipe/semicolon/newline only —
    # NOT commas (those belong inside a place name). Default is San Francisco.
    _loc_raw = os.getenv("TARGET_LOCATIONS", "").strip()
    if _loc_raw:
        TARGET_LOCATIONS = _parse_locations(_loc_raw)
    else:
        TARGET_LOCATIONS = ["San Francisco, California"]
    _LOCATIONS_LOWER = [c.lower() for c in TARGET_LOCATIONS]
    LOCATION_INCLUDE_UNKNOWN = _bool("LOCATION_INCLUDE_UNKNOWN", True)
    # Whether to add the target location to the SEARCH query. OFF (default) keeps
    # the search broad and applies location only as a filter — far more results.
    # ON forces the location words into every query (precise, but few results,
    # since most posts don't spell out the person's city in the indexed text).
    LOCATION_IN_SEARCH = _bool("LOCATION_IN_SEARCH", False)

    # Queries (one per line / pipe-separated; commas are NOT separators)
    raw = os.getenv("LINKEDIN_QUERIES", "").strip().replace("\n", "|")
    LINKEDIN_QUERIES = [q.strip() for q in raw.split("|") if q.strip()] or list(_DEFAULT_QUERIES)


# Compute all settings now, at import time.
refresh()


# US states / territories — used to decide whether a city/region target (e.g.
# "San Francisco, California") is US-based, so SerpAPI can geo-bias to the US.
_US_STATE_HINTS = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine",
    "maryland", "massachusetts", "michigan", "minnesota", "mississippi",
    "missouri", "montana", "nebraska", "nevada", "new hampshire", "new jersey",
    "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina",
    "south dakota", "tennessee", "texas", "utah", "vermont", "virginia",
    "washington", "west virginia", "wisconsin", "wyoming",
}


def _locations_are_us() -> bool:
    """True if every configured target location is US-based (alias or US state)."""
    if not _LOCATIONS_LOWER:
        return False
    for loc in _LOCATIONS_LOWER:
        if loc in _US_ALIASES:
            continue
        if any(state in loc for state in _US_STATE_HINTS):
            continue
        return False
    return True


def active_sources() -> list[str]:
    """The LinkedIn provider(s) a scan should run, resolved from LINKEDIN_SOURCE.

    - "all"/"merge"/blank -> every provider we have a key for (Gemini excluded:
      it returns 0). Falls back to ["serpapi"] if no key is set.
    - otherwise a single name or a comma/space-separated list, validated against
      the known providers.
    """
    src = LINKEDIN_SOURCE.strip().lower()
    if src in ("all", "merge", "", "auto"):
        out = []
        if SERPAPI_KEY:
            out.append("serpapi")
        if APIFY_TOKEN:
            out.append("apify")
        if PERPLEXITY_API_KEY:
            out.append("perplexity")
        return out or ["serpapi"]
    names = [s for s in src.replace(",", " ").split() if s]
    picked = [n for n in names if n in _ALL_PROVIDERS]
    return picked or ["serpapi"]


def _loc_match_terms(loc_lower: str) -> list[str]:
    """Terms that count as a match for one target location.

    Supports city/region entries, not just countries. For "san francisco,
    california" we match the whole string OR the primary component before the
    first comma ("san francisco"), so a record whose location reads "San
    Francisco Bay Area" or "San Francisco, CA, United States" still matches
    despite the differing formatting. Short fragments (<3 chars) are dropped to
    avoid spurious substring hits.
    """
    primary = loc_lower.split(",")[0].strip()
    terms = {loc_lower, primary}
    return [t for t in terms if len(t) >= 3]


def location_ok(rec: dict) -> bool:
    """True if a record's location matches the target locations (or if no
    location filter is configured, i.e. worldwide). Matches at country, state,
    or city granularity (see `_loc_match_terms`)."""
    if not _LOCATIONS_LOWER:
        return True
    # US-alias targets ("United States", "USA", …) are satisfied by the is_us
    # flag. City/state targets are NOT — they must actually appear in the text.
    if rec.get("is_us") and any(c in _US_ALIASES for c in _LOCATIONS_LOWER):
        return True
    hay = " ".join(str(rec.get(k) or "") for k in ("country", "location")).lower()
    for c in _LOCATIONS_LOWER:
        if any(term in hay for term in _loc_match_terms(c)):
            return True
    # Benefit of the doubt: unknown/unstated country passes when enabled.
    if LOCATION_INCLUDE_UNKNOWN:
        country = (rec.get("country") or "").strip().lower()
        if country in _UNKNOWN_LOC:
            return True
    return False


def location_query() -> str:
    """A search fragment that biases the LinkedIn query toward the target
    locations, e.g. `("San Francisco" OR "New York")`. Empty when:
      - LOCATION_IN_SEARCH is OFF (default — location is a filter, not a search
        term, which keeps recall high), or
      - searching worldwide, or
      - the US as a whole is the only target (serp_geo() already geo-biases, and
        we don't want to force the literal words "United States" into posts)."""
    if not LOCATION_IN_SEARCH:
        return ""
    if not _LOCATIONS_LOWER or all(c in _US_ALIASES for c in _LOCATIONS_LOWER):
        return ""
    terms: list[str] = []
    for loc in TARGET_LOCATIONS:
        primary = loc.split(",")[0].strip()
        if primary:
            terms.append(f'"{primary}"')
    terms = list(dict.fromkeys(terms))  # de-dupe, preserve order
    return "(" + " OR ".join(terms) + ")" if terms else ""


def serp_geo() -> tuple[str | None, str | None]:
    """Google (gl, hl) bias for SerpAPI — bias to the US when every target
    location is US-based (a US alias OR a US state/city like "San Francisco,
    California"); otherwise search worldwide."""
    if _locations_are_us():
        return "us", "en"
    return None, None


def missing_required() -> list[str]:
    """Return the names of required env vars that are unset (source-aware)."""
    required = {
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_SERVICE_KEY": SUPABASE_SERVICE_KEY,
    }
    sources = active_sources()
    single = sources[0] if len(sources) == 1 else None
    if single == "apify":
        required["APIFY_TOKEN"] = APIFY_TOKEN
    elif single == "perplexity":
        required["PERPLEXITY_API_KEY"] = PERPLEXITY_API_KEY
    elif single == "serpapi":
        required["SERPAPI_KEY"] = SERPAPI_KEY
    # single == "gemini" needs no extra key (reuses GEMINI_API_KEY).
    # Merge/"all" mode needs at least one search-provider key — flag it if none.
    missing = [k for k, v in required.items() if not v]
    if single is None and not (SERPAPI_KEY or APIFY_TOKEN or PERPLEXITY_API_KEY):
        missing.append("a LinkedIn provider key (SERPAPI_KEY, APIFY_TOKEN, or "
                       "PERPLEXITY_API_KEY)")
    return missing
