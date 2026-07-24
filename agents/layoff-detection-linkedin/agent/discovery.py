"""Company-expansion (second-pass) discovery engine.

Pass 1 (in pipeline.run_scan) searches the base query dictionary and extracts a
first set of companies. This module then runs a SECOND pass: for each strong
company it discovered, it searches LinkedIn again with company-specific queries
("<company> layoffs", "<company> restructuring", …), which surfaces additional
posts about that company that the generic search missed — including from other
employees at the same startup.

It reuses the existing provider orchestrator (sources.linkedin.search_linkedin_
posts) verbatim, just feeding it different queries. A budget governor caps how
many companies are expanded and hard-stops once the running scan cost crosses
SCAN_BUDGET_USD, so expansion can never run away.
"""
from __future__ import annotations

import logging
from collections import Counter

from . import companies, config, usage

log = logging.getLogger(__name__)

# Per-company expansion query templates, most valuable first. {c} = company name.
# Trimmed to config.EXPANSION_QUERIES_PER_COMPANY at runtime. SerpAPI/Perplexity
# already scope to linkedin.com/posts, so we don't repeat site: here.
_TEMPLATES = [
    '"{c}" layoffs',
    '"{c}" restructuring',
    '"{c}" "open to work"',
    '"{c}" layoff',
    '"{c}" "reduction in force"',
]


def expansion_queries(company_name: str) -> list[str]:
    """Company-specific search queries, capped at EXPANSION_QUERIES_PER_COMPANY."""
    name = (company_name or "").strip()
    if not name:
        return []
    n = max(1, config.EXPANSION_QUERIES_PER_COMPANY)
    return [t.format(c=name) for t in _TEMPLATES[:n]]


def select_companies(records: list[dict]) -> list[str]:
    """Companies worth expanding, most-mentioned first.

    Groups pass-1 records by normalized company key and orders by mention count,
    so the companies with the strongest first-pass signal are expanded first
    (and, under the budget cap, the weak long-tail is skipped). Returns display
    names; run_expansion() applies EXPANSION_MAX_COMPANIES.
    """
    tally: Counter[str] = Counter()
    names: dict[str, str] = {}
    for r in records:
        name = (r.get("company") or "").strip()
        key = companies.normalize_key(name)
        if not key:
            continue
        tally[key] += 1
        names.setdefault(key, name)      # first (usually cleanest) display name
    return [names[k] for k, _ in tally.most_common()]


def run_expansion(company_names: list[str], seen_urls: set[str],
                  metrics: dict) -> list[dict]:
    """Second-pass search for each company; return NEW candidates only.

    Honors the budget governor: before each company we check the running scan
    cost and stop once it crosses SCAN_BUDGET_USD. `seen_urls` (normalized) is
    updated in place so expansion never re-yields a first-pass post.
    """
    from .sources import linkedin

    budget = config.SCAN_BUDGET_USD
    cap = max(0, config.EXPANSION_MAX_COMPANIES)
    targets = company_names[:cap]
    out: list[dict] = []
    expanded = 0
    searches = 0
    metrics["budget_hit"] = False

    for name in targets:
        spent = usage.current_cost()
        if budget and spent >= budget:
            log.warning("Expansion budget $%.2f reached (spent $%.2f) after %d/%d "
                        "companies — stopping expansion.", budget, spent, expanded,
                        len(targets))
            metrics["budget_hit"] = True
            break
        queries = expansion_queries(name)
        if not queries:
            continue
        cands = linkedin.search_linkedin_posts(queries=queries)
        searches += len(queries)
        fresh = 0
        for c in cands:
            u = linkedin._norm_url(c.get("url"))
            if not u or u in seen_urls:
                continue
            seen_urls.add(u)
            c["discovery"] = "expansion"
            c["expanded_from"] = name
            out.append(c)
            fresh += 1
        expanded += 1
        log.info("Expansion %d/%d %r -> %d new post(s) (scan spend $%.2f)",
                 expanded, len(targets), name, fresh, usage.current_cost())

    metrics["companies_expanded"] = expanded
    metrics["expansion_searches"] = searches
    metrics["expansion_posts"] = len(out)
    return out
