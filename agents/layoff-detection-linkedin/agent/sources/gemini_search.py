"""Layoff-NEWS discovery via Gemini's Google Search grounding (REST API).

Why news, not LinkedIn posts: individual LinkedIn posts are login-walled, so
Google's grounding index does not contain them — grounded queries only ever
return news/blog articles *about* layoffs, never `linkedin.com/posts` URLs
(verified). So this backend is repurposed to do what Gemini grounding is
actually good at: find RECENT layoff NEWS from real news sites, using the same
layoff keywords, target location and recency window as the other sources. The
articles flow through the same extractor as the NewsAPI source (source="news"),
surfacing company layoff announcements and the companies behind them.

Why the REST API (not the google-generativeai SDK): the pinned SDK
(google-generativeai==0.8.3) cannot express the `google_search` grounding tool
for gemini-2.x models — `google_search` → "Unknown field",
`google_search_retrieval` → 400 "not supported". The REST `generateContent`
endpoint accepts `tools:[{"google_search":{}}]` and returns grounded results, so
we call it directly with httpx (already a dependency) — no SDK upgrade, no
httpx version conflict with the Supabase stack.

Output shape matches the other sources: {"url", "text", "source": "news"}.
Only GEMINI_API_KEY is required (already needed for extraction) — no extra
search subscription.
"""
from __future__ import annotations

import json
import logging
import re
from urllib.parse import urlsplit

import httpx

from .. import config

log = logging.getLogger(__name__)

_ENDPOINT = ("https://generativelanguage.googleapis.com/v1beta/models/"
             "{model}:generateContent")

_SYSTEM = (
    "You are a precise layoffs-news researcher. You use Google Search to find "
    "REAL, currently-live news articles from reputable outlets and never invent "
    "URLs or facts."
)

# Base search intents for the first pass — the same layoff vocabulary the other
# sources use, phrased for news discovery. Capped by GEMINI_NEWS_MAX_SEARCHES.
_BASE_NEWS_INTENTS = [
    "companies announcing layoffs or job cuts",
    "tech company layoffs and workforce reductions",
    "startup layoffs, downsizing or restructuring",
    "reduction in force / headcount reduction announcements",
    "company shutting down or cutting staff",
]

# Any absolute http(s) URL — used to recover article URLs from the reply text.
_URL_RE = re.compile(r"https?://[^\s\"'<>)\]}]+", re.I)

# Hosts that are never a news article (grounding redirect, LinkedIn, the search
# engine itself). Filtered out of results.
_SKIP_HOSTS = ("vertexaisearch.cloud.google.com", "linkedin.com",
               "google.com", "bing.com", "duckduckgo.com")

# When grounded, Gemini cites sources as redirect URLs on this host rather than
# the publisher's real URL. We resolve them to the final article URL.
_REDIRECT_HOST = "vertexaisearch.cloud.google.com"
_resolve_cache: dict[str, str] = {}


def _resolve(url: str) -> str:
    """Resolve a Gemini grounding-redirect URL to the real article URL.

    Non-redirect URLs are returned unchanged. Returns '' if resolution fails so
    the caller drops it rather than storing an unusable redirect link.
    """
    if _REDIRECT_HOST not in urlsplit(url).netloc.lower():
        return url
    if url in _resolve_cache:
        return _resolve_cache[url]
    final = ""
    try:
        r = httpx.head(url, follow_redirects=True, timeout=20,
                       headers={"User-Agent": "Mozilla/5.0"})
        final = str(r.url)
        if _REDIRECT_HOST in urlsplit(final).netloc.lower():
            final = ""  # still a redirect — unusable
    except Exception as exc:  # noqa: BLE001
        log.debug("Redirect resolve failed for %s: %s", url[:60], exc)
    _resolve_cache[url] = final
    return final


def _max_searches() -> int:
    """GEMINI_NEWS_MAX_SEARCHES, read defensively.

    Streamlit reruns the main script but keeps already-imported submodules
    cached, so a *newly added* config global can be absent on a stale `config`
    module after a redeploy. getattr with a default keeps this source working
    regardless (a fresh process always has the real value)."""
    return max(1, int(getattr(config, "GEMINI_NEWS_MAX_SEARCHES", 4) or 4))


def _trusted_domains() -> list[str]:
    """NEWS_TRUSTED_DOMAINS, read defensively (see _max_searches)."""
    return getattr(config, "NEWS_TRUSTED_DOMAINS", []) or []


def _recency_days() -> int:
    """The N-day window to ask the model to respect (mirrors the other sources)."""
    days = config.LINKEDIN_RECENCY_DAYS
    if days and days > 0:
        return days
    return {"d": 1, "w": 7, "m": 30, "y": 365}.get(config.LINKEDIN_RECENCY, 7)


def _build_prompt(focus: str | None) -> str:
    loc = ", ".join(config.TARGET_LOCATIONS)
    limit = max(1, config.LINKEDIN_RESULTS_PER_Q)
    lines = [
        "Use Google Search to find RECENT news articles reporting that a company "
        "is laying off staff, cutting jobs, or reducing its workforce.",
        f"Only include articles published in roughly the last {_recency_days()} "
        "day(s).",
    ]
    if focus:
        lines.append(f"Focus this search on: {focus}.")
    if loc:
        lines.append(f"Prefer layoffs that affect {loc} (companies headquartered "
                     "there, local offices, or workers based there).")
    trusted = _trusted_domains()
    if trusted:
        lines.append("Only use these news domains: " + ", ".join(trusted) + ".")
    else:
        lines.append("Prefer established, reputable news outlets; avoid blogs, "
                     "forums, and press-release wire spam.")
    lines += [
        "",
        f"Return STRICT JSON only: an array of up to {limit} objects, each with:",
        '  "url": the real article URL on the news site (not a redirect).',
        '  "company": the company laying people off.',
        '  "text": one sentence stating the company, how many/what roles, the '
        "location, and that it is a layoff.",
        "",
        "Rules:",
        "- Only real URLs you actually found via search. Never invent a URL.",
        "- Each object must be a distinct article about a real, recent layoff.",
        "- Output the JSON array and nothing else: no prose, no markdown fences.",
    ]
    return "\n".join(lines)


def _grounded_generate(user: str) -> str:
    """Run one grounded generation via the REST API; return the raw text reply.

    Raises RuntimeError on an HTTP error so the caller can decide how to react.
    """
    key = config.GEMINI_API_KEY
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set — the Gemini news source "
                           "needs it (it's the same key used for extraction).")
    url = _ENDPOINT.format(model=config.GEMINI_MODEL)
    body = {
        "contents": [{"parts": [{"text": user}]}],
        "systemInstruction": {"parts": [{"text": _SYSTEM}]},
        "tools": [{"google_search": {}}],
    }
    resp = httpx.post(url, params={"key": key}, json=body, timeout=90)
    if resp.status_code >= 300:
        raise RuntimeError(
            f"Gemini search failed {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    cand = (data.get("candidates") or [{}])[0]
    parts = (cand.get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    from .. import usage
    usage.add("gemini_calls", 1)
    usage.add("gemini_in_tokens", (len(_SYSTEM) + len(user)) // 4)
    usage.add("gemini_out_tokens", len(text) // 4)
    return text


def _loose_json(text: str):
    """Parse a JSON array from the reply, tolerating markdown fences / prose."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else text
        if text.endswith("```"):
            text = text[:-3]
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        m = re.search(r"\[.*\]", text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _acceptable(url: str) -> bool:
    if not url.lower().startswith(("http://", "https://")):
        return False
    host = urlsplit(url).netloc.lower()
    if any(skip in host for skip in _SKIP_HOSTS):
        return False
    trusted = _trusted_domains()
    if trusted:
        return any(host == d.lower() or host.endswith("." + d.lower())
                   for d in trusted)
    return True


def _candidates_from_reply(reply: str) -> list[dict]:
    """Parse the model reply into {url, text} dicts (JSON first, regex fallback)."""
    out: list[dict] = []
    parsed = _loose_json(reply)
    if isinstance(parsed, list):
        for item in parsed:
            if not isinstance(item, dict):
                continue
            url = _resolve(str(item.get("url") or "").strip().rstrip(").,];"))
            if not _acceptable(url):
                continue
            text = str(item.get("text") or "").strip()
            company = str(item.get("company") or "").strip()
            if company and company.lower() not in text.lower():
                text = (text + f" (company: {company})").strip()
            out.append({"url": url, "text": text})
    if not out:  # JSON gave nothing — scrape article URLs from the raw text.
        for url in _URL_RE.findall(reply):
            url = _resolve(url.rstrip(").,];"))
            if _acceptable(url):
                out.append({"url": url, "text": ""})
    return out


def _norm(url: str) -> str:
    p = urlsplit(url.strip())
    return f"{p.scheme.lower()}://{p.netloc.lower()}{p.path.rstrip('/')}"


def search_linkedin_posts(queries: list[str] | None = None) -> list[dict]:
    """Discover recent layoff NEWS via grounded Gemini search; dedupe by URL.

    Kept under this name so the provider dispatch in `linkedin.py` is unchanged,
    but it returns NEWS candidates (source="news"), not LinkedIn posts — see the
    module docstring. `queries` (used by company-expansion) becomes per-company
    focus terms; otherwise a capped set of broad layoff-news intents is used.
    """
    if not config.GEMINI_API_KEY:
        log.info("Gemini news source skipped (GEMINI_API_KEY unset).")
        return []

    cap = _max_searches()
    if queries is not None:
        foci = list(dict.fromkeys(q for q in queries if q))[:cap]
    else:
        foci = _BASE_NEWS_INTENTS[:cap]

    seen: set[str] = set()
    out: list[dict] = []
    for focus in foci:
        try:
            reply = _grounded_generate(_build_prompt(focus))
        except Exception as exc:  # noqa: BLE001 — one failed search is non-fatal
            log.warning("Gemini news search failed for %r: %s",
                        str(focus)[:60], exc)
            continue
        cands = _candidates_from_reply(reply)
        log.info("Gemini news %r -> %d article(s)", str(focus)[:60], len(cands))
        for c in cands:
            key = _norm(c["url"])
            if key in seen:
                continue
            seen.add(key)
            out.append({"url": c["url"], "text": c["text"], "source": "news"})
    if not out:
        log.warning("Gemini news search returned 0 articles. Try a wider recency "
                    "window (Settings → Tuning) or clear NEWS_TRUSTED_DOMAINS.")
    log.info("Gemini news: %d unique article(s)", len(out))
    return out


def fetch_single(url: str) -> dict | None:
    """Best-effort single-URL summary (for the 'Analyze a post' box).

    Asks Gemini (grounded) to summarise the specific article/post; falls back to
    a bare candidate so the downstream extractor can still mine the URL.
    """
    prompt = (
        "Use Google Search to open this specific URL and summarise it: "
        f"{url}\n\n"
        'Return STRICT JSON only: {"company": "...", "text": "one sentence with '
        'the company, roles/number affected, location, and the layoff signal"}. '
        "No prose, no markdown."
    )
    text = ""
    try:
        reply = _grounded_generate(prompt)
        data = _loose_json(reply)
        if isinstance(data, dict):
            text = str(data.get("text") or "").strip()
            company = str(data.get("company") or "").strip()
            if company and company.lower() not in text.lower():
                text = (text + f" (company: {company})").strip()
        elif reply:
            text = reply.strip()[:500]
    except Exception as exc:  # noqa: BLE001 — non-fatal; extractor mines the URL
        log.warning("Gemini single-URL summary failed: %s", exc)
    source = "linkedin" if "linkedin.com" in url.lower() else "news"
    return {"url": url, "text": text, "source": source}
