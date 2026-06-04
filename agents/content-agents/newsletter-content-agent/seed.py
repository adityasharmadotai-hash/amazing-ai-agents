"""
modules/seed.py
---------------
Seeds a couple of sample newsletters so the dashboard/history look alive
before the user generates their own. Safe to call repeatedly — it only
seeds when the table is empty.
"""

from datetime import datetime
from modules import database as db

_DEMO = [
    {
        "title": "The Agent Era: 5 Signals Worth Your Attention",
        "subject": "🤖 AI agents just leveled up — here's what changed",
        "topic": "AI agents",
        "audience": "AI engineers and founders",
        "style": "Professional",
        "length": "Medium",
        "sources": [
            {"title": "Sample source on autonomous agents", "source": "Demo Wire", "url": "https://example.com/a"},
        ],
        "content_md": (
            "# The Agent Era: 5 Signals Worth Your Attention\n\n"
            "**Subject line:** 🤖 AI agents just leveled up — here's what changed\n\n"
            "*Demo edition*\n\n---\n\n"
            "This is a seeded sample so you can see how a finished edition looks "
            "in the dashboard. Generate a real one from the **Create** page.\n\n"
            "## Key Insights\n\n### 1. Tooling is consolidating\n\n"
            "Frameworks are converging on a shared agent loop pattern.\n\n"
            "## Conclusion\n\nThe building blocks are stabilizing fast.\n\n---\n\n"
            "**Reply and tell me which agent you're building next.**\n"
        ),
    },
    {
        "title": "Healthcare AI Weekly: Where Models Still Stumble",
        "subject": "🩺 The clinical AI gap nobody is talking about",
        "topic": "AI in healthcare",
        "audience": "Clinicians and ML researchers",
        "style": "Storytelling",
        "length": "Short",
        "sources": [
            {"title": "Sample source on clinical LLMs", "source": "Demo Health", "url": "https://example.com/b"},
        ],
        "content_md": (
            "# Healthcare AI Weekly: Where Models Still Stumble\n\n"
            "**Subject line:** 🩺 The clinical AI gap nobody is talking about\n\n"
            "*Demo edition*\n\n---\n\n"
            "A short seeded sample edition.\n\n"
            "## Key Insights\n\n### 1. Evaluation beats hype\n\n"
            "Real de-identified cases reveal failure modes benchmarks miss.\n\n"
            "## Conclusion\n\nTrust is earned one validated case at a time.\n\n---\n\n"
            "**Forward this to a colleague who works in clinical AI.**\n"
        ),
    },
]


def seed_if_empty():
    if db.count_newsletters() > 0:
        return False
    for item in _DEMO:
        db.save_newsletter(item)
    return True
