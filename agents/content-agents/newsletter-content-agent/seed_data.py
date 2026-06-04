"""
Demo data seeder.

Populates the database with realistic-looking sources, collected content items,
a couple of generated newsletters and a schedule so a brand-new user sees a
fully populated dashboard without needing an API key or live network calls.

Idempotent: it checks a settings flag and only seeds once unless ``force``.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from modules import database as db
from modules.newsletter_generator import estimate_engagement

_SEED_FLAG = "demo_seeded_v1"

DEMO_SOURCES = [
    ("Hacker News Front Page", "RSS Feed", "https://hnrss.org/frontpage", "AI Tooling", "Developer Tools"),
    ("TechCrunch", "News Website", "https://techcrunch.com", "Startups", "SaaS"),
    ("r/MachineLearning", "Reddit", "MachineLearning", "Machine Learning", "Artificial Intelligence"),
    ("Two Minute Papers", "YouTube", "https://www.youtube.com/channel/UCbfYPyITQ-7l4upoX8nvctg", "AI Research", "Artificial Intelligence"),
    ("Stratechery", "Blog", "https://stratechery.com", "Tech Strategy", "General Technology"),
    ("OpenAI Blog", "Company Website", "https://openai.com/blog", "AI Models", "Artificial Intelligence"),
    ("AI Builders on X", "Twitter/X", "", "AI", "Artificial Intelligence"),
]

DEMO_CONTENT = [
    ("New open-weights model beats prior SOTA on reasoning benchmarks", "Artificial Intelligence",
     "A newly released open-weights model posts a 12% gain on graduate-level reasoning evals while running on a single consumer GPU.", "Reddit", "r/MachineLearning", 1840),
    ("Seed-stage AI funding rebounds 30% quarter-over-quarter", "SaaS",
     "Investors poured fresh capital into AI infra and vertical agents, with median seed rounds climbing to $3.5M.", "News Website", "TechCrunch", 0),
    ("The agent stack is consolidating around three primitives", "Developer Tools",
     "Memory, tool-use and planning are emerging as the durable building blocks as dozens of frameworks converge.", "Blog", "Stratechery", 0),
    ("Inference costs fell 80% year-over-year for frontier-class quality", "Artificial Intelligence",
     "Cheaper inference is reshaping product economics, making always-on AI features viable for the first time.", "Company Website", "OpenAI Blog", 0),
    ("Why most RAG pipelines fail in production (and the fix)", "Developer Tools",
     "Retrieval quality, not model quality, is the usual culprit; chunking and reranking deliver the biggest gains.", "RSS Feed", "Hacker News Front Page", 920),
    ("Founders are hiring AI-native generalists over specialists", "SaaS",
     "Early teams increasingly value people who can wire together models, tools and data over deep single-domain experts.", "News Website", "TechCrunch", 0),
    ("Video explainer: how diffusion transformers actually work", "Artificial Intelligence",
     "A clear visual walkthrough of the architecture powering the latest generation of media models.", "YouTube", "Two Minute Papers", 0),
    ("Regulators signal lighter-touch approach to open models", "General Technology",
     "Draft guidance distinguishes foundation-model providers from downstream deployers, easing fears for open ecosystems.", "Blog", "Stratechery", 0),
]


def seed(force: bool = False) -> None:
    db.init_db()
    if not force and db.get_setting(_SEED_FLAG):
        return

    src_ids = {}
    for name, stype, url, topic, industry in DEMO_SOURCES:
        sid = db.add_source(name, stype, url, topic, industry)
        src_ids[name] = sid

    now = datetime.now(timezone.utc)
    for i, (title, industry, summary, stype, sname, votes) in enumerate(DEMO_CONTENT):
        db.upsert_content_item({
            "source_id": src_ids.get(sname),
            "source_type": stype,
            "source_name": sname,
            "title": title,
            "url": f"https://example.com/article/{i+1}",
            "summary": summary,
            "raw_text": summary,
            "author": "Demo Author",
            "topic": "AI" if "AI" in industry or "Artificial" in industry else industry,
            "industry": industry,
            "published_at": (now - timedelta(days=i)).isoformat(),
            "content_hash": hashlib.sha256(f"seed-{i}-{title}".encode()).hexdigest(),
            "score": votes,
        })

    _seed_newsletters()
    _seed_schedule()
    db.set_setting(_SEED_FLAG, True)
    db.log_event("demo_seeded", {})


def _seed_newsletters() -> None:
    body1 = {
        "title": "The AI Builder's Brief — Issue 14",
        "subject_line": "3 shifts reshaping the agent stack",
        "introduction": (
            "This week the signal was loud: open models are catching up, inference is "
            "getting absurdly cheap, and the agent ecosystem is finally converging on a "
            "shared vocabulary. Here's what actually matters for builders."
        ),
        "key_insights": [
            {"heading": "Open weights are closing the gap",
             "body": "A new open-weights release posts double-digit gains on reasoning evals while running on a single consumer GPU — the practical ceiling for self-hosted AI just moved up."},
            {"heading": "Inference economics flipped",
             "body": "An 80% year-over-year drop in inference cost makes always-on AI features viable. Product decisions you shelved last year are worth revisiting."},
            {"heading": "The agent stack is consolidating",
             "body": "Memory, tool-use and planning are emerging as the durable primitives. Betting on these rather than any single framework is the safer architecture."},
        ],
        "industry_updates": [
            {"headline": "Seed-stage AI funding rebounds 30%", "summary": "Median seed rounds climbed to $3.5M, concentrated in infra and vertical agents.", "url": "https://example.com/article/2"},
            {"headline": "Lighter-touch model regulation signaled", "summary": "Draft guidance separates providers from deployers, easing open-ecosystem fears.", "url": "https://example.com/article/8"},
        ],
        "actionable_takeaways": [
            "Re-run your build-vs-buy math on inference — last year's numbers are stale.",
            "Audit your RAG pipeline's retrieval quality before blaming the model.",
            "Standardize your agent design around memory/tools/planning, not a framework.",
        ],
        "closing": "That's the brief. Reply and tell me which of these you want unpacked next week.",
        "call_to_action": "Forward this to one builder who'd thank you for it.",
    }
    db.save_newsletter({
        "title": body1["title"], "subject_line": body1["subject_line"],
        "topic": "AI", "industry": "Artificial Intelligence",
        "style": "AI Newsletter", "writing_mode": "Thought Leadership",
        "status": "sent", "body_json": body1, "source_count": 6,
        "engagement_score": estimate_engagement(body1),
    })

    body2 = {
        "title": "Founder Field Notes — Hiring AI-Native Teams",
        "subject_line": "Hire generalists, not specialists (for now)",
        "introduction": "A short one this week, prompted by a pattern I keep seeing across early teams.",
        "key_insights": [
            {"heading": "Generalists are winning early roles",
             "body": "Teams that can wire models, tools and data together are out-shipping those stacked with narrow specialists."},
        ],
        "industry_updates": [
            {"headline": "AI-native generalists in demand", "summary": "Early teams prize range over depth at the zero-to-one stage.", "url": "https://example.com/article/6"},
        ],
        "actionable_takeaways": [
            "Rewrite your next JD to emphasize range and shipping speed.",
            "Add a practical build task to your interview loop.",
        ],
        "closing": "Keep shipping. More next week.",
        "call_to_action": "Share your hiring playbook — reply and tell me what's working.",
    }
    db.save_newsletter({
        "title": body2["title"], "subject_line": body2["subject_line"],
        "topic": "Hiring", "industry": "SaaS",
        "style": "Founder Newsletter", "writing_mode": "Conversational",
        "status": "draft", "body_json": body2, "source_count": 2,
        "engagement_score": estimate_engagement(body2),
    })


def _seed_schedule() -> None:
    from modules.scheduler import compute_next_run
    db.add_schedule({
        "name": "Weekly AI Brief",
        "frequency": "Weekly",
        "topic": "AI",
        "industry": "Artificial Intelligence",
        "style": "AI Newsletter",
        "writing_mode": "Thought Leadership",
        "next_run": compute_next_run("Weekly"),
    })
