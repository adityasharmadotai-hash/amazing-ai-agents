"""
rankings.py — Live Google keyword rankings via SerpAPI, for the US and SF Bay Area.

For each target keyword we ask SerpAPI for the top-100 Google organic results in a
locale, then find the first result whose domain matches the tracked site and record
its position (1–100) and URL. Results are cached to data/rankings.json; a refresh
costs len(keywords) × len(locations) SerpAPI searches, so we only refresh on demand
or when the cache is older than REFRESH_AFTER_DAYS.

Key is read from SERPAPI_KEY (env or Streamlit secret synced into env) — the same
name the outreach-agent already uses.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

SERPAPI_URL = "https://serpapi.com/search.json"
TARGET_DOMAIN = "futrbridge.com"

# FutrBridge = AI talent / staffing platform (US, esp. SF Bay Area & California).
# Employers come to hire full-stack, backend, AI, RL research and LLM-eval engineers.
DEFAULT_KEYWORDS = [
    "AI staffing agency",
    "AI recruiting agency",
    "hire AI engineers",
    "hire AI engineers San Francisco",
    "AI talent",
    "AI talent Bay Area",
    "hire full stack developers",
    "hire backend developers",
    "hire machine learning engineers",
    "hire reinforcement learning engineers",
    "LLM evaluation experts",
    "AI staffing agency San Francisco",
]

# Two tracked markets: national US and the localized SF Bay Area (where the
# demand concentrates). SerpAPI's `location` param returns geo-localized results.
LOCATIONS = {
    "us": {"gl": "us", "label": "United States", "flag": "🇺🇸",
           "google_domain": "google.com", "location": None},
    "sf": {"gl": "us", "label": "SF Bay Area", "flag": "🌉",
           "google_domain": "google.com", "location": "San Francisco, California, United States"},
}

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_FILE = os.path.join(_DATA_DIR, "rankings.json")
REFRESH_AFTER_DAYS = 7

# Domains that show up in staffing/AI-hiring SERPs but aren't direct competitors
# (job boards, social, aggregators, info sites). Excluded from the Competitors view.
_NON_COMPETITORS = {
    "wikipedia.org", "reddit.com", "quora.com", "youtube.com", "google.com",
    "facebook.com", "twitter.com", "x.com", "instagram.com", "medium.com",
    "linkedin.com", "indeed.com", "glassdoor.com", "ziprecruiter.com",
    "monster.com", "forbes.com", "businessinsider.com", "nytimes.com",
    "techcrunch.com", "g2.com", "trustpilot.com", "gartner.com", "yelp.com",
    "bing.com", "coursera.org", "udemy.com",
}


# ── key / cache ───────────────────────────────────────────────────────────────
def api_key() -> str:
    return os.environ.get("SERPAPI_KEY", "").strip()


def has_key() -> bool:
    return bool(api_key())


def _norm_domain(host: str) -> str:
    host = (host or "").lower().strip()
    return host[4:] if host.startswith("www.") else host


def load_cache() -> dict:
    try:
        with open(_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_cache(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def is_stale(cache: dict) -> bool:
    ts = cache.get("updated")
    if not ts:
        return True
    try:
        age = datetime.now(timezone.utc) - datetime.fromisoformat(ts)
        return age.days >= REFRESH_AFTER_DAYS
    except ValueError:
        return True


# ── one keyword × locale ──────────────────────────────────────────────────────
def fetch_rank(keyword: str, loc_key: str, domain: str = TARGET_DOMAIN,
               capture_top: int = 10) -> dict:
    """Return {position, url, top} for `domain`. `top` is the top-N organic results
    (domain/position/title) so the Competitors view can be built from the same query."""
    loc = LOCATIONS[loc_key]
    params = {
        "engine": "google",
        "q": keyword,
        "gl": loc["gl"],
        "google_domain": loc["google_domain"],
        "num": 100,
        "hl": "en",
        "api_key": api_key(),
    }
    if loc.get("location"):
        params["location"] = loc["location"]
    try:
        resp = requests.get(SERPAPI_URL, params=params, timeout=25)
        if resp.status_code == 429:
            return {"position": None, "url": "", "top": [], "error": "quota"}
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            return {"position": None, "url": "", "top": [], "error": data["error"]}
        target = _norm_domain(domain)
        result = {"position": None, "url": "", "top": []}
        for r in data.get("organic_results", []):
            pos = r.get("position")
            link = r.get("link", "")
            host = _norm_domain(urlparse(link).netloc)
            if capture_top and pos and pos <= capture_top and host:
                result["top"].append({"domain": host, "position": pos,
                                      "title": (r.get("title") or "")[:90]})
            if result["position"] is None and host and (host == target or host.endswith("." + target)):
                result["position"], result["url"] = pos, link
        return result
    except requests.RequestException as e:
        return {"position": None, "url": "", "top": [], "error": str(e)}


# ── full refresh ──────────────────────────────────────────────────────────────
def refresh(keywords: list | None = None, domain: str = TARGET_DOMAIN,
            progress=None) -> dict:
    """Re-query every keyword × locale and persist. `progress(done, total, label)`
    is an optional callback for a Streamlit progress bar."""
    keywords = keywords or DEFAULT_KEYWORDS
    total = len(keywords) * len(LOCATIONS)
    done = 0
    out = {}
    for kw in keywords:
        out[kw] = {}
        for lk in LOCATIONS:
            if progress:
                progress(done, total, f"{kw} · {LOCATIONS[lk]['label']}")
            out[kw][lk] = fetch_rank(kw, lk, domain)
            done += 1
    if progress:
        progress(total, total, "done")
    cache = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "domain": domain,
        "keywords": keywords,
        "data": out,
    }
    _save_cache(cache)
    return cache


# ── shaping for the UI ────────────────────────────────────────────────────────
def rows(cache: dict | None = None) -> list:
    """Flatten cache into per-keyword rows. Positions are keyed by location under
    `pos` (e.g. {"us": 7, "sf": 3}) so the UI can render any set of locations."""
    cache = cache or load_cache()
    data = cache.get("data", {})
    locs = list(LOCATIONS.keys())
    out = []
    for kw in cache.get("keywords", DEFAULT_KEYWORDS):
        kd = data.get(kw, {})
        pos = {lk: (kd.get(lk) or {}).get("position") for lk in locs}
        page = next(((kd.get(lk) or {}).get("url") for lk in locs
                     if (kd.get(lk) or {}).get("url")), "")
        path = (urlparse(page).path or "/") if page else "—"
        vals = [p for p in pos.values() if p]
        out.append({"keyword": kw, "page": path, "pos": pos,
                    "best": min(vals) if vals else None})
    out.sort(key=lambda r: (r["best"] is None, r["best"] or 999))
    return out


def summary(cache: dict | None = None, loc: str = "best") -> dict:
    """Counts of keywords in each ranking band for the KPI tiles. `loc` is a
    location key, or "best" to use each keyword's best position across markets."""
    cache = cache or load_cache()
    bands = {"top10": 0, "top20": 0, "top100": 0, "none": 0}
    for r in rows(cache):
        p = r["best"] if loc in ("best", "both") else r["pos"].get(loc)
        if not p:
            bands["none"] += 1
        elif p <= 10:
            bands["top10"] += 1
        elif p <= 20:
            bands["top20"] += 1
        else:
            bands["top100"] += 1
    return bands


def locations() -> list:
    """(key, flag, label) for each tracked market — for the UI to render columns."""
    return [(k, v["flag"], v["label"]) for k, v in LOCATIONS.items()]


def _is_competitor(dom: str) -> bool:
    if not dom:
        return False
    return not any(dom == b or dom.endswith("." + b) for b in _NON_COMPETITORS)


def competitors(cache: dict | None = None, limit: int = 15) -> list:
    """Who else ranks in the top 10 for your keywords — built from the cached SERPs.
    Groups the captured top results by domain, keeping each competitor's best
    position per keyword. Excludes the tracked site and non-competitor domains."""
    cache = cache or load_cache()
    data = cache.get("data", {})
    target = _norm_domain(cache.get("domain", TARGET_DOMAIN))
    agg: dict = {}  # domain -> {keyword: best_position}
    for kw, locs in data.items():
        for _lk, res in (locs or {}).items():
            for t in (res or {}).get("top", []):
                dom = t.get("domain", "")
                if dom == target or not _is_competitor(dom):
                    continue
                slot = agg.setdefault(dom, {})
                if kw not in slot or t["position"] < slot[kw]:
                    slot[kw] = t["position"]
    out = []
    for dom, kws in agg.items():
        positions = list(kws.values())
        out.append({
            "domain": dom,
            "appearances": len(kws),
            "best": min(positions),
            "top10": sum(1 for p in positions if p <= 10),
            "keywords": sorted(({"keyword": k, "position": p} for k, p in kws.items()),
                               key=lambda x: x["position"]),
        })
    out.sort(key=lambda c: (-c["appearances"], c["best"]))
    return out[:limit]


def competitor_summary(cache: dict | None = None) -> dict:
    comps = competitors(cache, limit=999)
    return {
        "total": len(comps),
        "strong": sum(1 for c in comps if c["appearances"] >= 3),
        "keywords_covered": len({kw for c in comps for kw in (k["keyword"] for k in c["keywords"])}),
    }
