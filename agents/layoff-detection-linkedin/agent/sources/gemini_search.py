"""LinkedIn layoff-post discovery via Gemini's built-in Google Search grounding.

This backend needs NO extra search key beyond GEMINI_API_KEY (already required
for extraction): it asks Gemini — with Google Search grounding switched on — to
find recent public LinkedIn layoff / "open to work" posts and hand back their
URLs plus a one-line snippet. It sits between SerpAPI (cheap, thin Google
snippets) and Apify (paid full scrape): no separate search subscription, and the
model can reason about the query, but coverage depends on what Google surfaces to
it and each query costs Gemini tokens.

Output shape matches the other two backends exactly, so the rest of the pipeline
is untouched: {"url", "text", "source": "linkedin", "profile_url"}.

Robustness: grounding tool specs differ across Gemini model families
(2.x wants `google_search`, 1.5 wants `google_search_retrieval`) and the installed
SDK may support only some of them, so `_generate()` tries each in turn and finally
falls back to an ungrounded call — the source degrades instead of crashing. The
model is asked for strict JSON; a regex fallback recovers post URLs from the raw
text if JSON parsing fails.
"""
from __future__ import annotations

import json
import logging
import re

from .. import config
from .linkedin import _profile_url_from_post

log = logging.getLogger(__name__)

_SYSTEM = (
    "You are a precise research assistant. You find REAL, currently-live public "
    "LinkedIn posts using Google Search and never invent URLs."
)

# Any LinkedIn post/activity URL — used to recover URLs from the raw reply when
# the model doesn't return clean JSON.
_URL_RE = re.compile(
    r"https?://(?:[\w-]+\.)?linkedin\.com/(?:posts|feed/update)/[^\s\"'<>)\]]+",
    re.I,
)

# Grounding tool specs to try, most-modern first. Strings and dicts are both
# accepted by different SDK versions; the last entry (None) is the ungrounded
# fallback so the source still returns *something* if grounding is unavailable.
_TOOL_SPECS = ([{"google_search": {}}], "google_search_retrieval",
               [{"google_search_retrieval": {}}], None)


def _recency_days() -> int:
    """The N-day window to ask the model to respect (mirrors the other sources)."""
    days = config.LINKEDIN_RECENCY_DAYS
    if days and days > 0:
        return days
    # Legacy single-letter fallback -> an approximate day count.
    return {"d": 1, "w": 7, "m": 30, "y": 365}.get(config.LINKEDIN_RECENCY, 7)


def _build_prompt(query: str) -> str:
    loc = config.location_query()
    limit = max(1, config.LINKEDIN_RESULTS_PER_Q)
    lines = [
        "Use Google Search to find recent PUBLIC LinkedIn posts where an "
        "individual says they were laid off / impacted by layoffs / let go and "
        "are open to work or seeking new opportunities.",
        "",
        f"Search intent: {query}",
    ]
    if loc:
        lines.append(f"Prefer people based in: {loc}")
    lines += [
        f"Only include posts from roughly the last {_recency_days()} day(s).",
        "",
        f"Return STRICT JSON only: an array of up to {limit} objects, each with:",
        '  "url":  the full post URL, starting with '
        "https://www.linkedin.com/posts/ (or /feed/update/).",
        '  "text": one sentence with the person\'s name, their role/title, their '
        "company, and the layoff signal.",
        "",
        "Rules:",
        "- Only real URLs you actually found via search. Never guess or fabricate "
        "a URL or an activity id.",
        "- Skip company announcements and news articles — only individuals' posts.",
        "- Output the JSON array and nothing else: no prose, no markdown, no fences.",
    ]
    return "\n".join(lines)


def _record_usage(prompt: str, reply: str) -> None:
    from .. import usage
    usage.add("gemini_calls", 1)
    usage.add("gemini_in_tokens", (len(_SYSTEM) + len(prompt)) // 4)
    usage.add("gemini_out_tokens", len(reply) // 4)


def _strip_fence(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else text
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def _generate(prompt: str) -> str:
    """Run one grounded generation, trying each tool spec then ungrounded.

    Returns the model's raw text reply ('' if every attempt failed).
    """
    from .. import llm
    llm._ensure_configured()
    genai = llm._get_genai()
    last_exc: Exception | None = None
    for tool in _TOOL_SPECS:
        try:
            kwargs = {"system_instruction": _SYSTEM}
            if tool is not None:
                kwargs["tools"] = tool
            model = genai.GenerativeModel(config.GEMINI_MODEL, **kwargs)
            resp = model.generate_content(prompt)
            reply = _strip_fence(resp.text or "")
            _record_usage(prompt, reply)
            if tool is None:
                log.info("Gemini search ran WITHOUT grounding (no search tool "
                         "accepted by this model/SDK) — coverage may be limited.")
            return reply
        except Exception as exc:  # noqa: BLE001 — try the next tool spec
            last_exc = exc
            log.debug("Gemini search tool spec %r failed: %s", tool, exc)
            continue
    log.warning("Gemini search failed for every tool spec: %s", last_exc)
    return ""


def _candidates_from_reply(reply: str) -> list[dict]:
    """Parse the model reply into candidate dicts (JSON first, regex fallback)."""
    out: list[dict] = []
    parsed = None
    try:
        parsed = json.loads(reply)
    except (json.JSONDecodeError, TypeError):
        # Model may have wrapped the array in prose — grab the outermost [...].
        m = re.search(r"\[.*\]", reply, re.S)
        if m:
            try:
                parsed = json.loads(m.group(0))
            except json.JSONDecodeError:
                parsed = None

    if isinstance(parsed, list):
        for item in parsed:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url") or "").strip()
            if "linkedin.com" not in url:
                continue
            text = str(item.get("text") or "").strip()
            out.append({"url": url, "text": text})

    if not out:  # JSON gave us nothing — scrape any post URLs from the raw text.
        for url in _URL_RE.findall(reply):
            out.append({"url": url, "text": ""})
    return out


def search_linkedin_posts() -> list[dict]:
    """Run every configured query through Gemini search; dedupe by URL."""
    seen: set[str] = set()
    out: list[dict] = []
    for query in config.LINKEDIN_QUERIES:
        reply = _generate(_build_prompt(query))
        cands = _candidates_from_reply(reply)
        log.info("Gemini search %r -> %d candidate(s)", query[:60], len(cands))
        for c in cands:
            url = c["url"]
            if url in seen:
                continue
            seen.add(url)
            out.append({"url": url, "text": c["text"], "source": "linkedin",
                        "profile_url": _profile_url_from_post(url)})
    if not out:
        log.warning("Gemini search returned 0 posts. Likely causes: the model "
                    "couldn't ground on Google Search (check GEMINI_MODEL supports "
                    "grounding), the recency window is too narrow, or nothing "
                    "matched. Try a wider window or a simpler query.")
    log.info("Gemini LinkedIn: %d unique candidate post(s)", len(out))
    return out


def fetch_single(url: str) -> dict | None:
    """Best-effort single-URL fetch (for the 'Analyze a URL' box).

    Asks Gemini to summarise the specific post; if it can't, we still return a
    bare candidate so the downstream extractor can mine the URL slug.
    """
    prompt = (
        "Use Google Search to open this specific public LinkedIn post and "
        f"summarise it: {url}\n\n"
        'Return STRICT JSON only: {"text": "one sentence with the person\'s name, '
        'role/title, company, and layoff signal"}. No prose, no markdown.'
    )
    reply = _generate(prompt)
    text = ""
    try:
        data = json.loads(reply)
        if isinstance(data, dict):
            text = str(data.get("text") or "").strip()
    except (json.JSONDecodeError, TypeError):
        text = reply.strip()[:500]
    return {"url": url, "text": text, "source": "linkedin",
            "profile_url": _profile_url_from_post(url)}
