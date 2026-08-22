"""Central config — reads settings from the environment.

All env-derived values are computed inside `refresh()`, which is called once at
import and again whenever the Settings page changes a key (see
`st_common.apply_overrides`). This avoids `importlib.reload`, which is unsafe
under Streamlit's rerun model and was corrupting the `agent` package import.
"""
from __future__ import annotations

import os
import re
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

# Alias expansion for target locations. When a configured target location's full
# string OR its primary component (before the first comma) matches a key here,
# every listed alias ALSO counts as an in-location match — and the aliases are
# shown to the extractor so it can set `is_target_location` correctly. This keeps
# a "San Francisco" target from dropping nearby Bay Area / Silicon Valley posts
# (Palo Alto, San Jose, …) that never literally spell out "San Francisco".
LOCATION_ALIASES: dict[str, list[str]] = {
    "san francisco": [
        "san francisco", "sf", "bay area", "san francisco bay area",
        "silicon valley", "palo alto", "mountain view", "sunnyvale", "san jose",
    ],
}

# All LinkedIn discovery providers. Gemini is excluded from "all"/merge mode
# because Google Search grounding cannot reach individual LinkedIn posts (it
# returns 0) — but it stays selectable explicitly for anyone who wants it.
_ALL_PROVIDERS = ("serpapi", "apify", "perplexity", "gemini")

# Query dictionary — MANY phrases, each searched INDEPENDENTLY (never combined
# into one boolean query). Grouped for clarity; flattened into the default
# LINKEDIN_QUERIES below. Employee language is where small/unknown startups
# surface (the extractor pulls the employer name out of the post). Override the
# active set via LINKEDIN_QUERIES; trim it to cut cost.
QUERY_DICTIONARY: dict[str, list[str]] = {
    "employee": [
        '"today was my last day"', '"my last day at"', '"my final day"',
        '"my role was eliminated"', '"my position was eliminated"',
        '"I got laid off"', '"I was laid off"', '"unfortunately I was laid off"',
        '"affected by the layoffs"', '"impacted by the layoffs"',
        '"impacted by layoffs"', '"part of the layoffs"',
        '"looking for new opportunities"', '"open to work"',
        # Conversational phrasings that thin snippets often use — the `*` is a
        # Google in-phrase wildcard (SerpAPI backend), so "my time at * has come
        # to an end" matches "my time at ACME has come to an end". Other backends
        # treat it literally, which is harmless.
        '"my time at * has come to an end"',
        '"affected by the workforce reduction"',
        '"leaving * earlier than expected"',
        '"impacted along with many talented colleagues"',
    ],
    "company": [
        '"layoffs"', '"laying off"', '"layoffs at"', '"downsizing"',
        '"restructuring"', '"reduction in force"', '"workforce reduction"',
        '"headcount reduction"', '"cost cutting"',
    ],
    "startup": [
        '"cash runway"', '"burn reduction"', '"strategic restructuring"',
        '"organizational changes"', '"team reduction"',
    ],
    "hashtag": ['#layoffs', '#layoff', '#opentowork'],
}

# Flattened default active query set (every phrase, deduped, order preserved).
_DEFAULT_QUERIES = list(dict.fromkeys(
    q for group in QUERY_DICTIONARY.values() for q in group))


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
    global EXPANSION_ENABLED, EXPANSION_MAX_COMPANIES, EXPANSION_QUERIES_PER_COMPANY
    global SCAN_BUDGET_USD

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

    # ── Company-expansion (second-pass discovery) ──────────────────────────
    # After the first pass discovers companies, expand the strongest ones with
    # per-company searches ("<company> layoffs", site:linkedin.com/posts <company>…).
    EXPANSION_ENABLED = _bool("EXPANSION_ENABLED", True)
    # Cap the number of companies expanded per scan (each costs several searches).
    EXPANSION_MAX_COMPANIES = _int("EXPANSION_MAX_COMPANIES", 10)
    # How many expansion queries to run per company (capped against the template).
    EXPANSION_QUERIES_PER_COMPANY = _int("EXPANSION_QUERIES_PER_COMPANY", 3)
    # Hard spend ceiling (USD) for the EXPANSION phase: before expanding each
    # company we check the running scan cost and abort expansion once it crosses
    # this. Pass-1 (the base dictionary) is bounded by the query set + caps.
    SCAN_BUDGET_USD = _float("SCAN_BUDGET_USD", 3.0)
    SCAN_INTERVAL_HOURS = _int("SCAN_INTERVAL_HOURS", 4)

    # Target locations (blank = worldwide). Cities/regions are allowed
    # ("San Francisco, California"), so we split on pipe/semicolon/newline only —
    # NOT commas (those belong inside a place name). Default is San Francisco.
    _loc_raw = os.getenv("TARGET_LOCATIONS", "").strip()
    if _loc_raw:
        TARGET_LOCATIONS = _parse_locations(_loc_raw)
    else:
        # San Francisco OR anywhere in California. The "California" entry matches
        # any California location; the SF entry catches "San Francisco, CA" /
        # "San Francisco Bay Area" where the word "California" isn't spelled out.
        TARGET_LOCATIONS = ["San Francisco, California", "California"]
    _LOCATIONS_LOWER = [c.lower() for c in TARGET_LOCATIONS]
    # Default False: "only SF/California" means a record must actually match one
    # of the target locations — unknown-location posts are NOT given the benefit
    # of the doubt. Set LOCATION_INCLUDE_UNKNOWN=true to loosen (more volume).
    LOCATION_INCLUDE_UNKNOWN = _bool("LOCATION_INCLUDE_UNKNOWN", False)
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
    # Pull in the alias group for this place (e.g. SF -> Bay Area, Palo Alto…).
    for key in (loc_lower, primary):
        if key in LOCATION_ALIASES:
            terms.update(LOCATION_ALIASES[key])
    # Keep 2-char aliases like "sf" (matched on a word boundary, see
    # `_term_matches`); drop 1-char noise only.
    return [t for t in terms if len(t) >= 2]


def _term_matches(hay: str, term: str) -> bool:
    """True if `term` is present in `hay`. Very short terms (<=2 chars, e.g.
    'sf') must match on a word boundary so they never fire inside an unrelated
    word ('misfit', 'sfax'); longer terms match as a plain substring."""
    if len(term) <= 2:
        return re.search(rf"\b{re.escape(term)}\b", hay) is not None
    return term in hay


def target_location_aliases() -> list[str]:
    """Every alias/place term (lowercased, deduped) that counts as an in-location
    match across all configured target locations. Used to tell the extractor
    exactly which places qualify as `is_target_location`."""
    out: list[str] = []
    for loc in _LOCATIONS_LOWER:
        out.extend(_loc_match_terms(loc))
    return list(dict.fromkeys(out))


def location_ok(rec: dict) -> bool:
    """True if a record's location matches the target locations (or if no
    location filter is configured, i.e. worldwide). Matches at country, state,
    or city granularity (see `_loc_match_terms`), honoring alias groups
    (SF -> Bay Area / Silicon Valley / Palo Alto / …).

    The extractor's explicit `is_target_location` verdict is authoritative:
      - True  -> qualifies even if the raw location text is phrased unusually.
      - False -> the post is NOT in a target location, so it can never be given
                 the unknown-location benefit of the doubt (hard rejection).
    """
    if not _LOCATIONS_LOWER:
        return True
    verdict = rec.get("is_target_location")
    # US-alias targets ("United States", "USA", …) are satisfied by the is_us
    # flag. City/state targets are NOT — they must actually appear in the text.
    if rec.get("is_us") and any(c in _US_ALIASES for c in _LOCATIONS_LOWER):
        return True
    hay = " ".join(str(rec.get(k) or "") for k in ("country", "location")).lower()
    for c in _LOCATIONS_LOWER:
        if any(_term_matches(hay, term) for term in _loc_match_terms(c)):
            return True
    # The extractor explicitly confirmed this is a target-location post.
    if verdict is True:
        return True
    # Benefit of the doubt: unknown/unstated country passes when enabled — but
    # NEVER when the extractor explicitly said it is NOT the target location.
    if LOCATION_INCLUDE_UNKNOWN and verdict is not False:
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
