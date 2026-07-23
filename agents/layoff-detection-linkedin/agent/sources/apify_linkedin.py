"""LinkedIn post discovery via Apify (paid, real LinkedIn scrape).

Uses the `apimaestro/linkedin-posts-search-scraper-no-cookies` actor, which
returns FULL post text + author headline (job title) — far richer than the
Google-indexed snippets SerpAPI gives, and it reaches posts Google never
indexed. Output shape matches the SerpAPI source: {"url", "text", "source"}.

The actor's exact output field names aren't publicly documented, so extraction
is defensive (tries several likely keys, with a deep-scan fallback for the URL).
If the actor returns posts but none parse, `search_linkedin_posts()` logs the
first raw item's keys + a JSON sample to the scan log so the real shape is
visible without any extra tooling.
"""
from __future__ import annotations

import json
import logging
import re

import httpx

from .. import config

log = logging.getLogger(__name__)

_API = "https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"

# LINKEDIN_RECENCY (d/w/m/y) -> actor date_filter value. The actor only supports
# past-1h / past-24h / past-week / past-month (there is NO past-year), so 'y'
# maps to the widest available window, past-month.
_DATE_MAP = {"d": "past-24h", "w": "past-week", "m": "past-month", "y": "past-month"}

# Matches any LinkedIn post/activity URL, used as a last-resort deep fallback
# when the actor nests the URL under an unexpected key.
_URL_RE = re.compile(r"https?://[^\s\"'<>]*linkedin\.com/[^\s\"'<>]+", re.I)


def _actor_path() -> str:
    # API wants the '/' in the actor id replaced by '~'
    return config.APIFY_ACTOR.replace("/", "~")


def _date_filter() -> str:
    if config.APIFY_DATE_FILTER:
        return config.APIFY_DATE_FILTER
    # The actor only offers fixed buckets, so map the requested N-day window to
    # the nearest one (e.g. the 2-day default -> past-week, since there is no
    # "past-2-days" option). Set APIFY_DATE_FILTER to override exactly.
    days = config.LINKEDIN_RECENCY_DAYS
    if days and days > 0:
        if days <= 1:
            return "past-24h"
        if days <= 7:
            return "past-week"
        return "past-month"          # actor has no window wider than a month
    return _DATE_MAP.get(config.LINKEDIN_RECENCY, "past-week")


def _simplify_keyword(query: str) -> str:
    """Turn a Google-style boolean query into a plain LinkedIn keyword.

    LinkedIn's post search barely understands quotes / parentheses / OR — the
    app's default boolean query returns ~4 posts, while the same intent as a
    plain phrase returns ~170. So for the Apify backend we flatten each query:
    keep the first alternative of every (A OR B OR …) group, then drop quotes,
    hashes and any leftover OR. A query with no operators passes through
    unchanged.
    """
    def _first_or(m):
        return m.group(1).split(" OR ")[0]
    s = re.sub(r"\(([^()]*)\)", _first_or, query)   # (A OR B …) -> A
    s = s.replace('"', "").replace("#", "")          # drop quotes & hashes
    s = re.sub(r"\s+OR\s+", " ", s)                  # any leftover OR -> space
    return re.sub(r"\s+", " ", s).strip()


def _keyword_variants(query: str) -> list[str]:
    """Break one boolean query into several plain-keyword searches.

    LinkedIn post search wants a simple phrase, not boolean logic. The old code
    collapsed a whole query to ONE keyword (first alternative only), throwing away
    every other OR-variant — a big coverage loss. Instead we pull out each quoted
    phrase and hashtag as its own keyword, so `"laid off" OR "reduction in force"
    OR #layoffs` becomes three separate searches. Falls back to the flattened
    keyword when the query has no quotes/hashtags.
    """
    seen: set[str] = set()
    variants: list[str] = []
    for kw in re.findall(r'"([^"]+)"', query) + re.findall(r"#(\w+)", query):
        kw = kw.strip()
        if len(kw) >= 3 and kw.lower() not in seen:
            seen.add(kw.lower())
            variants.append(kw)
    if not variants:
        simplified = _simplify_keyword(query)
        if simplified:
            variants = [simplified]
    return variants


def _first(d: dict, *keys, default=""):
    """Return the first present, non-empty value among keys (supports a.b nesting)."""
    for k in keys:
        cur = d
        ok = True
        for part in k.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur:
            return cur
    return default


def _run_actor(payload: dict) -> list[dict]:
    url = _API.format(actor=_actor_path())
    headers = {"Authorization": f"Bearer {config.APIFY_TOKEN}",
               "Content-Type": "application/json"}
    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=180)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.warning("Apify actor run failed: %s", exc)
        return []
    data = resp.json()
    items = data if isinstance(data, list) else data.get("items", [])
    from .. import usage
    usage.add("apify_posts", len(items))
    return items


def _deep_find_url(obj) -> str:
    """Walk a nested structure for the first LinkedIn post/activity URL."""
    if isinstance(obj, str):
        m = _URL_RE.search(obj)
        return m.group(0) if m else ""
    if isinstance(obj, dict):
        for v in obj.values():
            u = _deep_find_url(v)
            if u:
                return u
    elif isinstance(obj, list):
        for v in obj:
            u = _deep_find_url(v)
            if u:
                return u
    return ""


def _author_name(item: dict) -> str:
    author = _first(item, "author.name", "authorName", "author_name",
                    "author.full_name", "actor.name", default="")
    if isinstance(author, dict):
        author = _first(author, "name", "full_name", default="")
    if not author:  # some actors split the name into first/last
        first = _first(item, "author.first_name", "author.firstName", default="")
        last = _first(item, "author.last_name", "author.lastName", default="")
        author = " ".join(x for x in (str(first), str(last)) if x).strip()
    return str(author or "")


def _to_candidate(item: dict) -> dict | None:
    url = _first(item, "url", "post_url", "postUrl", "share_url", "shareUrl",
                 "link", "postLink", "full_urn", "urn")
    if not url or "linkedin.com" not in str(url):
        url = _deep_find_url(item) or url          # last-resort: scan the whole item
    text = _first(item, "text", "content", "post_text", "postText", "commentary",
                  "description", "post.text", default="")
    # author headline carries the job title — critical for the role filter
    author = _author_name(item)
    headline = _first(item, "author.headline", "authorHeadline", "author_headline",
                      "author.occupation", "author.sub_title", "actor.description",
                      default="")
    # Require only a URL: even with no snippet, the extractor recovers keywords
    # from the post URL slug, so a bare URL is still a usable candidate.
    if not url:
        return None
    profile_url = _first(item, "author.profile_url", "author.profileUrl",
                         "authorProfileUrl", "author.url", "author.public_url",
                         default="")
    if isinstance(profile_url, dict):
        profile_url = ""
    if not profile_url:  # build it from the author's handle if present
        handle = _first(item, "author.username", "author.public_identifier",
                        "authorUsername", default="")
        if handle and isinstance(handle, str):
            profile_url = f"https://www.linkedin.com/in/{handle}"
    blob = " | ".join(filter(None, [str(author), str(headline), str(text)]))
    return {"url": str(url), "text": blob, "source": "linkedin",
            "profile_url": str(profile_url), "author_name": str(author)}


def search_linkedin_posts() -> list[dict]:
    """Run every configured query through the Apify actor; dedupe by URL."""
    seen: set[str] = set()
    out: list[dict] = []
    raw_total = 0
    first_dropped: dict | None = None
    loc = config.location_query()

    # Build a global, deduped list of keyword variants across ALL queries, then
    # cap the total number of Apify searches (each is one paid actor run).
    variants: list[str] = []
    seen_kw: set[str] = set()
    for query in config.LINKEDIN_QUERIES:
        for kw in _keyword_variants(query):
            if kw.lower() not in seen_kw:
                seen_kw.add(kw.lower())
                variants.append(kw)
    cap = max(1, config.APIFY_MAX_KEYWORD_VARIANTS)
    if len(variants) > cap:
        log.info("Apify: %d keyword variants found, capping to %d "
                 "(raise APIFY_MAX_KEYWORD_VARIANTS for more coverage/cost).",
                 len(variants), cap)
        variants = variants[:cap]
    log.info("Apify: running %d keyword search(es): %s", len(variants), variants)

    for kw in variants:
        keyword = f"{kw} {loc}".strip() if loc else kw
        payload = {
            "keyword": keyword,
            "sort_type": "date_posted",
            "date_filter": _date_filter(),
            "limit": config.LINKEDIN_RESULTS_PER_Q,
            "total_posts": config.LINKEDIN_RESULTS_PER_Q,
        }
        items = _run_actor(payload)
        raw_total += len(items)
        log.info("Apify query %r (date_filter=%s) -> %d raw item(s)",
                 keyword, payload["date_filter"], len(items))
        for item in items:
            cand = _to_candidate(item)
            if not cand:
                if first_dropped is None and isinstance(item, dict):
                    first_dropped = item
                continue
            if cand["url"] in seen:
                continue
            seen.add(cand["url"])
            out.append(cand)

    # Self-diagnosis: if the actor returned posts but we parsed none, the output
    # field names differ from what _to_candidate expects. Dump the real shape to
    # the scan log so it can be seen (and the parser tightened) without a token.
    if raw_total and not out and first_dropped is not None:
        log.warning("Apify returned %d post(s) but 0 were parseable — the actor's "
                    "output field names differ from expected. First item keys: %s",
                    raw_total, list(first_dropped.keys()))
        log.warning("First raw item (truncated): %s",
                    json.dumps(first_dropped, ensure_ascii=False, default=str)[:1500])
    elif raw_total == 0:
        log.warning("Apify returned 0 posts for every query. Likely causes: the "
                    "keyword's boolean/parentheses aren't understood by LinkedIn "
                    "search, the date window is too narrow, or the location term "
                    "is too restrictive. Try a simpler keyword or a wider window.")
    log.info("Apify LinkedIn: %d raw item(s) -> %d unique candidate post(s)",
             raw_total, len(out))
    return out


def fetch_single(url: str) -> dict | None:
    """Best-effort single-URL fetch (for the 'Analyze a URL' box)."""
    payload = {"post_url": url, "keyword": "", "limit": 1, "total_posts": 1}
    for item in _run_actor(payload):
        cand = _to_candidate(item)
        if cand:
            cand["url"] = url
            return cand
    return None
