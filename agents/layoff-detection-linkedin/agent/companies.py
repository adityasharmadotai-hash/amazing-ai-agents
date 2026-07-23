"""Company Discovery — roll individual layoff posts up into a company-centric
view with a confidence score built from independent signals.

Slice A of the Company Discovery Engine: the primary entity becomes the COMPANY,
with each post as evidence. Confidence rises when multiple independent signals
name the same company (several employees + a recruiter + a founder + a news
article is far stronger than one anonymous post).

Two pure pieces live here so they're easy to test:
  - normalize_key(): canonicalize a company name so "Retell AI", "Retell.ai" and
    "Retell, Inc." collapse to one key.
  - confidence(): a noisy-OR over weighted signal types.

rebuild() reads every stored post, groups by company_key, and upserts the
`companies` rollup table. It is intentionally recomputed from posts each scan, so
counts accumulate across scans (that's what makes repeated mentions raise
confidence) and it self-heals if a post is re-classified.
"""
from __future__ import annotations

import logging
import re

log = logging.getLogger(__name__)

# Corporate suffixes stripped during canonicalization. NOTE: we deliberately keep
# "ai" — it's part of real names (Retell AI, OpenAI) and stripping it would merge
# distinct companies.
_SUFFIXES = {
    "inc", "llc", "corp", "co", "ltd", "company", "technologies", "technology",
    "labs", "holdings", "group", "incorporated", "limited", "gmbh", "plc",
    "the",
}

# How much each signal type raises confidence that a company really had layoffs.
# Used as per-signal probabilities in a noisy-OR (see confidence()).
_WEIGHTS = {
    "news": 0.80,          # a news article naming the company
    "company": 0.80,       # official company announcement / press release
    "founder": 0.70,       # a founder/exec confirming
    "recruiter": 0.45,     # a recruiter referencing the layoff
    "employee": 0.38,      # an affected employee's own post
    "other": 0.12,         # commentary / mention
}

# The poster-role buckets we recognize (mirrors the LLM's poster_role output).
ROLES = ("employee", "recruiter", "founder", "company", "news", "other")


def normalize_key(name: str | None) -> str:
    """Canonical dedupe key for a company name.

    Lowercase, strip punctuation and common corporate suffixes, collapse
    whitespace. "Retell AI" / "Retell.ai" / "Retell, Inc." -> "retell ai" /
    "retell" respectively — not perfect (AI is kept, so "Retell" and "Retell AI"
    still differ), but good enough for MVP and safe against false merges.
    """
    if not name:
        return ""
    s = name.strip().lower()
    s = re.sub(r"[^\w\s&-]", " ", s)          # drop punctuation except & and -
    tokens = [t for t in s.split() if t and t not in _SUFFIXES]
    return " ".join(tokens).strip()


def confidence(counts: dict[str, int]) -> float:
    """Noisy-OR confidence from a {role: count} tally.

    Each signal independently argues the layoff is real; combined confidence is
    1 - Π(1 - weight)^count. Many weak signals (several employees) still add up,
    and one strong signal (news/founder) lands high on its own.
    """
    p_not_real = 1.0
    for role, n in counts.items():
        if n <= 0:
            continue
        w = _WEIGHTS.get(role, _WEIGHTS["other"])
        p_not_real *= (1.0 - w) ** n
    return round(1.0 - p_not_real, 4)


def _best_name(posts: list[dict]) -> str:
    """Pick the most common non-empty display name among a company's posts."""
    tally: dict[str, int] = {}
    for p in posts:
        name = (p.get("company") or "").strip()
        if name:
            tally[name] = tally.get(name, 0) + 1
    if not tally:
        return ""
    return max(tally, key=tally.get)


def _locations(posts: list[dict]) -> str:
    """Distinct, non-empty locations observed for a company (comma-joined)."""
    seen: list[str] = []
    for p in posts:
        loc = (p.get("location") or "").strip()
        if loc and loc not in seen:
            seen.append(loc)
    return ", ".join(seen[:5])


def company_row(key: str, posts: list[dict]) -> dict:
    """Build one `companies` rollup row from all posts sharing a company_key."""
    counts = {r: 0 for r in ROLES}
    for p in posts:
        role = (p.get("poster_role") or "other").strip().lower()
        counts[role if role in counts else "other"] += 1
    return {
        "company_key": key,
        "company_name": _best_name(posts) or key,
        "employee_posts": counts["employee"],
        "recruiter_posts": counts["recruiter"],
        "founder_posts": counts["founder"],
        "announcement_posts": counts["company"],
        "news_posts": counts["news"],
        "total_posts": len(posts),
        "confidence": confidence(counts),
        "locations": _locations(posts),
    }


def rebuild() -> int:
    """Recompute the `companies` rollup from every stored post. Returns the number
    of companies upserted. Non-fatal: logs and returns 0 on any storage error so a
    scan still succeeds even if the companies table isn't set up yet."""
    from . import store
    try:
        posts = store.posts_for_rollup()
    except Exception as exc:  # noqa: BLE001
        log.warning("Company rollup skipped — couldn't read posts: %s", exc)
        return 0
    groups: dict[str, list[dict]] = {}
    for p in posts:
        key = (p.get("company_key") or "").strip()
        if key:
            groups.setdefault(key, []).append(p)
    rows = [company_row(key, ps) for key, ps in groups.items()]
    if not rows:
        return 0
    try:
        return store.upsert_companies(rows)
    except Exception as exc:  # noqa: BLE001 — company table optional / not migrated
        log.warning("Company rollup skipped — upsert failed (did you run the "
                    "companies migration?): %s", exc)
        return 0
