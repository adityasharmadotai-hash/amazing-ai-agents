"""
demo_seed.py — populate a realistic business profile so the dashboard and the
simulator have something to show on first run, before any real leads arrive.

This only writes the knowledge base (business profile + questions + config). The
simulator generates live conversations against the real Gemini brain, so we don't
fake message threads here.
"""

from __future__ import annotations

from . import database, knowledge

DEMO_PROFILE = {
    "business_name": "BrightPath Careers",
    "one_liner": "We place Bay Area job seekers into full-time and contract roles — free for candidates.",
    "about": (
        "BrightPath Careers is a recruiting agency in the San Francisco Bay Area. "
        "We run Instagram ads to reach job seekers, then match them with employers "
        "in tech, operations, sales, and customer support. Our service is free for "
        "candidates — employers pay us when we place someone."
    ),
    "offerings": [
        "Free 1:1 matching to open roles that fit your experience.",
        "Resume review and a mock interview before you apply.",
        "Direct introductions to hiring managers (skip the online black hole).",
    ],
    "locations": ["San Francisco", "Oakland", "San Jose", "Remote (US)"],
    "hours": "Mon–Sat 9am–7pm PT. The assistant replies instantly 24/7; a human follows up during hours.",
    "website": "https://brightpathcareers.example.com",
    "pricing": "100% free for candidates. Employers pay a placement fee.",
    "faqs": [
        {"q": "Is it really free?", "a": "Yes — candidates never pay. Employers pay us when we place you."},
        {"q": "What roles do you place?", "a": "Tech, operations, sales, and customer support — entry to senior level."},
        {"q": "Do you do remote jobs?", "a": "Yes, we have both Bay Area on-site and US-remote roles."},
        {"q": "How long does placement take?", "a": "It varies, but many candidates get their first interview within a week."},
    ],
    "escalate_topics": [
        "guaranteeing a specific salary or a specific company's offer",
        "visa sponsorship or immigration/legal guarantees",
        "anything about an existing application's private status",
    ],
}


def run() -> None:
    database.init_db()
    knowledge.save_profile(DEMO_PROFILE)
    knowledge.get_questions()  # seeds defaults
    cfg = knowledge.get_config()
    cfg["assistant_name"] = "Ava"
    knowledge.save_config(cfg)
    print("Seeded demo business profile for BrightPath Careers.")


if __name__ == "__main__":
    run()
