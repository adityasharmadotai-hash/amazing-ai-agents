"""
suggestions.py — Find winnable long-tail keywords + how to rank for them.

Discovers real search queries from SerpAPI (Google "related searches" and the
"People Also Ask" box) seeded from the site's topics, then attaches a concrete
ranking plan to each: which page should target it, what content to add, the
title/meta to use, and the schema to mark up. Cached to data/suggestions.json
so the (small) SerpAPI cost is only paid on an explicit refresh.

No OpenAI needed — recommendations are intent-driven heuristics tuned for an
AI talent / staffing platform (FutrBridge) hiring for US & SF Bay Area roles.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

import requests

from modules import rankings  # reuse api_key() + SERPAPI_URL

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_FILE = os.path.join(_DATA_DIR, "suggestions.json")

# Seed topics to expand into long-tail. Tuned to FutrBridge's niche (hiring AI /
# engineering talent in the US & SF Bay Area). Each seed costs one SerpAPI search.
DISCOVERY_SEEDS = [
    "AI staffing agency",
    "hire AI engineers",
    "AI recruiting agency",
    "hire full stack developers San Francisco",
    "hire machine learning engineers",
    "reinforcement learning engineer hiring",
]
SITE = "futrbridge.com"


# ── SerpAPI discovery ─────────────────────────────────────────────────────────
def _related(query: str) -> list:
    """Related searches + People-Also-Ask questions for one query."""
    params = {
        "engine": "google", "q": query, "gl": "us",
        "google_domain": "google.com", "num": 10, "hl": "en",
        "api_key": rankings.api_key(),
    }
    try:
        resp = requests.get(rankings.SERPAPI_URL, params=params, timeout=25)
        resp.raise_for_status()
        data = resp.json()
        out = []
        # People-Also-Ask questions = featured-snippet opportunities (more winnable)
        for q in data.get("related_questions", []):
            if q.get("question"):
                out.append((q["question"].rstrip("?"), "paa"))
        for rs in data.get("related_searches", []):
            if rs.get("query"):
                out.append((rs["query"], "related"))
        return out
    except (requests.RequestException, ValueError):
        return []


# ── intent + recommendations ──────────────────────────────────────────────────
def _slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")[:48]


_LOCATION_WORDS = ("san francisco", "bay area", "california", "silicon valley",
                   "sf ", "usa", "united states", "remote", "us ")
_ROLE_WORDS = ("engineer", "developer", "full stack", "full-stack", "backend",
               "back end", "machine learning", "ml ", "llm", "reinforcement learning",
               "data scientist", "researcher")


def classify(kw: str) -> str:
    k = " " + kw.lower() + " "
    if "futrbridge" in k:
        return "brand"
    if any(w in k for w in (" vs ", " or ", "versus", "better than", "alternative", "reviews", "legit")):
        return "comparison"
    if any(w in k for w in ("salary", "cost", "rate", "pricing", "how much", "fees")):
        return "cost"
    hire_intent = any(w in k for w in ("hire", "hiring", "staffing", "recruit", "recruiting", "talent", "for hire"))
    if any(w in k for w in _LOCATION_WORDS) and (hire_intent or any(r in k for r in _ROLE_WORDS)):
        return "location"
    if hire_intent or any(r in k for r in _ROLE_WORDS):
        return "hire"
    return "informational"


def difficulty(kw: str, source: str = "related") -> str:
    k = kw.lower()
    if "futrbridge" in k:
        return "Easy"
    n = len(kw.split())
    if any(w in k for w in _LOCATION_WORDS):
        return "Easy" if n >= 4 else "Medium"   # localized long-tail = lowest competition
    if n >= 4:
        return "Medium"
    return "Hard"


# Keep only employer / hiring-intent ideas; FutrBridge's audience is companies that
# want to hire — not job-seekers, learners, or curiosity searchers.
_RELEVANT = ("hire", "hiring", "staff", "recruit", "talent", "agency", "engineer",
             "developer", "full stack", "full-stack", "backend", "back end",
             "machine learning", "llm", "reinforcement", "data scientist",
             "contractor", "outsourc", "augment", "build a team")
_NOISE = ("salary", "reddit", "glassdoor", "resume", "quiz", "meme", "course",
          "bootcamp", "how much do", "$", "big 4", "top 5", "top 10", "make ",
          "makes ", "free ", "sims", "near me salary", "become a",
          "jobs", " job", "entry level", "internship")


def _keep(kw: str) -> bool:
    k = kw.lower()
    if any(nz in k for nz in _NOISE):
        return False
    return any(r in k for r in _RELEVANT)


def recommend(kw: str, source: str = "related") -> dict:
    """How-to-rank plan for a keyword, driven by its (staffing) search intent."""
    intent = classify(kw)
    slug = _slug(kw)
    title_kw = kw[0].upper() + kw[1:]
    plans = {
        "brand": {
            "page": "Home page (strengthen entity signals)",
            "content": "Put “FutrBridge” + “AI staffing” in the H1 and first paragraph. Add an About/Company section, client logos, and consistent NAP. Reinforce with LinkedIn + Crunchbase.",
            "title": f"{title_kw} — Hire the Top 1% AI Talent in the US",
            "schema": "Organization + WebSite (JSON-LD)",
        },
        "hire": {
            "page": f"New role landing page · /hire/{slug}",
            "content": "Create a dedicated page for this role: who these engineers are, your vetting process, time-to-hire, sample profiles, and a “request talent” CTA. Put the exact phrase in the H1 and first 100 words.",
            "title": f"{title_kw} — Vetted, US-Based | FutrBridge",
            "schema": "Service + FAQPage (JSON-LD)",
        },
        "location": {
            "page": f"New location landing page · /locations/{slug}",
            "content": "Build a geo page for this market: local talent pool, on-site/hybrid options, Bay Area rate benchmarks, and case studies from nearby startups. Add a Google Business Profile and embed a map.",
            "title": f"{title_kw} — On-Demand AI Talent | FutrBridge",
            "schema": "LocalBusiness + Service (JSON-LD)",
        },
        "cost": {
            "page": f"Pricing / guide page · /pricing (or /guides/{slug})",
            "content": "Answer the pricing question directly in the first 60 words, then a rate-benchmark table by role and seniority. Transparent-pricing pages win featured snippets and high-intent traffic.",
            "title": f"{title_kw} — 2026 Rate Benchmarks | FutrBridge",
            "schema": "FAQPage + Article (JSON-LD)",
        },
        "comparison": {
            "page": f"New comparison post · /compare/{slug}",
            "content": "Lead with a comparison table (FutrBridge vs alternatives), then pros/cons and a verdict. Answer “which is better / is it legit” in the first 60 words to win the snippet.",
            "title": f"{title_kw}: Honest 2026 Comparison",
            "schema": "FAQPage + Article (JSON-LD)",
        },
        "informational": {
            "page": f"New pillar / blog page · /guides/{slug}",
            "content": "Write a 1,200+ word guide for hiring managers: definition, when to hire, how to evaluate, and a checklist. Answer the query directly up top and link internally to your role pages.",
            "title": f"{title_kw}: A Hiring Manager’s Guide (2026)",
            "schema": "Article + FAQPage (JSON-LD)",
        },
    }
    plan = plans[intent]
    return {"intent": intent, "difficulty": difficulty(kw, source), **plan}


# ── build / cache ─────────────────────────────────────────────────────────────
def load_cache() -> dict:
    try:
        with open(_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(cache: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


_DIFF_ORDER = {"Easy": 0, "Medium": 1, "Hard": 2}


def generate(seeds: list | None = None, limit: int = 18, progress=None) -> dict:
    """Discover long-tail ideas and attach ranking plans. Costs len(seeds) searches."""
    seeds = seeds or DISCOVERY_SEEDS
    found, total, done = {}, len(seeds), 0
    for s in seeds:
        if progress:
            progress(done, total, s)
        for kw, src in _related(s):
            key = kw.lower().strip()
            # drop head terms, dups, and off-audience (job-seeker / curiosity) noise
            if len(kw.split()) >= 2 and key not in found and _keep(kw):
                found[key] = (kw.strip(), src)
        done += 1
    if progress:
        progress(total, total, "done")

    items = [{"keyword": kw, **recommend(kw, src)} for kw, src in found.values()]
    # winnable first: Easy → Medium → Hard, then shorter wins ties
    items.sort(key=lambda x: (_DIFF_ORDER[x["difficulty"]], len(x["keyword"])))
    items = items[:limit]

    cache = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items": items,
    }
    _save(cache)
    return cache


def counts(cache: dict | None = None) -> dict:
    cache = cache or load_cache()
    c = {"Easy": 0, "Medium": 0, "Hard": 0}
    for it in cache.get("items", []):
        c[it["difficulty"]] = c.get(it["difficulty"], 0) + 1
    return c
