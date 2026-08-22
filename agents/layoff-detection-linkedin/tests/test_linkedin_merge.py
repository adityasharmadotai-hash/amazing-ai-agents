"""Multi-provider orchestrator merges concurrently without dropping batches
(agent/sources/linkedin.py)."""
from __future__ import annotations

import pytest

from agent import config
from agent.sources import linkedin


@pytest.fixture
def three_providers(monkeypatch):
    """serpapi + apify + perplexity, each returning a canned batch."""
    monkeypatch.setattr(config, "active_sources",
                        lambda: ["serpapi", "apify", "perplexity"])

    batches = {
        "serpapi": [
            {"url": "https://linkedin.com/posts/a", "text": "short"},
            {"url": "https://linkedin.com/posts/b", "text": "serp b"},
        ],
        # 'a' is a cross-provider duplicate with RICHER text -> should win.
        "apify": [
            {"url": "https://linkedin.com/posts/a", "text": "a much longer body"},
            {"url": "https://linkedin.com/posts/c", "text": "apify c"},
        ],
        "perplexity": [
            {"url": "https://linkedin.com/posts/d", "text": "pplx d"},
        ],
    }

    def fake_provider_search(name):
        return lambda queries=None: [dict(r) for r in batches[name]]

    monkeypatch.setattr(linkedin, "_provider_search", fake_provider_search)
    return batches


def test_merges_all_providers(three_providers):
    out = linkedin.search_linkedin_posts()
    urls = {linkedin._norm_url(r["url"]) for r in out}
    # a, b, c, d — every provider's candidates survive the merge.
    assert urls == {
        "https://linkedin.com/posts/a", "https://linkedin.com/posts/b",
        "https://linkedin.com/posts/c", "https://linkedin.com/posts/d",
    }


def test_dedup_keeps_richest_text(three_providers):
    out = linkedin.search_linkedin_posts()
    a = next(r for r in out if r["url"].endswith("/a"))
    assert a["text"] == "a much longer body"          # apify copy won on length


def test_provider_tag_present(three_providers):
    out = linkedin.search_linkedin_posts()
    assert all(r.get("provider") in {"serpapi", "apify", "perplexity"}
               for r in out)


def test_failing_provider_does_not_drop_others(monkeypatch):
    monkeypatch.setattr(config, "active_sources",
                        lambda: ["serpapi", "apify"])

    def fake_provider_search(name):
        if name == "apify":
            def boom(queries=None):
                raise RuntimeError("apify down")
            return boom
        return lambda queries=None: [{"url": "https://linkedin.com/posts/x",
                                      "text": "serp x"}]

    monkeypatch.setattr(linkedin, "_provider_search", fake_provider_search)
    out = linkedin.search_linkedin_posts()
    assert [r["url"] for r in out] == ["https://linkedin.com/posts/x"]


def test_url_less_candidates_skipped_not_crashing(monkeypatch):
    monkeypatch.setattr(config, "active_sources", lambda: ["serpapi", "apify"])

    def fake_provider_search(name):
        if name == "apify":
            return lambda queries=None: [{"text": "no url here"}]   # missing url
        return lambda queries=None: [{"url": "https://linkedin.com/posts/y",
                                      "text": "serp y"}]

    monkeypatch.setattr(linkedin, "_provider_search", fake_provider_search)
    out = linkedin.search_linkedin_posts()
    # The URL-less candidate is skipped; the valid one still comes through.
    assert [r["url"] for r in out] == ["https://linkedin.com/posts/y"]
