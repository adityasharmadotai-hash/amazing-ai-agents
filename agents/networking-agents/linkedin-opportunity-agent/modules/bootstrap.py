"""
bootstrap.py — One-time app initialisation & demo seeding.

Called once per session from app.py. Creates the schema, loads persisted
settings into session state, and (on a fresh database) seeds realistic demo
data using the deterministic engine so the dashboard is never empty — even
before an API key is added.
"""

from __future__ import annotations

import streamlit as st

from . import database as db, detector, monitor
from .samples import SAMPLE_COMPANIES, SAMPLE_POSTS, SAMPLE_PROFILES

DEFAULT_KEYWORDS = ["AI", "hiring", "funding", "SaaS", "automation", "founder"]
DEFAULT_INDUSTRIES = ["Artificial Intelligence", "Fintech", "SaaS", "Cybersecurity"]


def _load_settings_into_session() -> None:
    """Hydrate session_state from the settings table (first run picks defaults)."""
    if "keywords" not in st.session_state:
        st.session_state.keywords = db.get_setting("keywords", DEFAULT_KEYWORDS)
    if "industries" not in st.session_state:
        st.session_state.industries = db.get_setting("industries", DEFAULT_INDUSTRIES)
    if "model" not in st.session_state:
        st.session_state.model = db.get_setting("model", "")
    if "sender_name" not in st.session_state:
        st.session_state.sender_name = db.get_setting("sender_name", "")
    if "sender_role" not in st.session_state:
        st.session_state.sender_role = db.get_setting("sender_role", "")


def _seed_demo() -> None:
    """Populate sample profiles, companies and opportunities on a fresh DB."""
    if db.counts()["total"] > 0:
        return

    for p in SAMPLE_PROFILES:
        db.add_profile(p["name"], p["headline"], p["profile_url"], p["company"], p["industry"])
    for c in SAMPLE_COMPANIES:
        db.add_company(c["name"], c["page_url"], c["industry"])

    keywords = st.session_state.get("keywords", DEFAULT_KEYWORDS)
    industries = st.session_state.get("industries", DEFAULT_INDUSTRIES)

    for sp in SAMPLE_POSTS:
        post = {
            "external_id": monitor._external_id(sp["text"], sp["author_name"]),
            "author_name": sp["author_name"],
            "author_headline": sp.get("author_headline", ""),
            "company": sp.get("company", ""),
            "url": sp.get("url", ""),
            "text": sp["text"],
            "industry": sp.get("industry", ""),
            "posted_at": None,
        }
        db.upsert_post(post)
        db.mark_post_processed(post["external_id"])
        # Use the deterministic engine for instant, free seeding.
        result = detector.fallback_analyze(post, keywords, industries)
        if not result:
            continue
        db.add_opportunity(
            {
                "post_external_id": post["external_id"],
                "person_name": post["author_name"],
                "person_headline": post["author_headline"],
                "company": post["company"],
                "profile_url": post["url"],
                "post_url": post["url"],
                "post_text": post["text"],
                **result,
            }
        )


def ensure_ready() -> None:
    """Idempotent per-session initialisation entry point."""
    if st.session_state.get("_booted"):
        return
    db.init_db()
    _load_settings_into_session()
    _seed_demo()
    st.session_state._booted = True
