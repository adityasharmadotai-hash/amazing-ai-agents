"""
Newsletter generation engine.

Turns research output (insights / statistics / ranked items) into a fully
structured newsletter with every required section. Style and writing-mode
selections shape the system prompt so the same pipeline produces an AI
newsletter or a Finance newsletter with the appropriate voice.

The generated structure (``body_json``) is the canonical representation; the
exporters render it to Markdown / HTML / PDF / DOCX.
"""

from __future__ import annotations

from config import NEWSLETTER_STYLES, WRITING_MODES
from modules.llm import LLMClient

# Canonical ordered section keys
SECTIONS = [
    "introduction",
    "key_insights",
    "industry_updates",
    "actionable_takeaways",
    "closing",
    "call_to_action",
]


def generate_newsletter(
    topic: str,
    industry: str,
    style: str,
    writing_mode: str,
    research_data: dict,
    llm: LLMClient,
    references: list[dict] | None = None,
) -> dict:
    """Return a full newsletter dict ready to persist."""
    references = references or research_data.get("ranked_items", [])[:12]
    style_meta = NEWSLETTER_STYLES.get(style, list(NEWSLETTER_STYLES.values())[0])
    mode_desc = WRITING_MODES.get(writing_mode, "")

    if not llm.available:
        return _heuristic_newsletter(
            topic, industry, style, writing_mode, research_data, references, style_meta
        )

    system = (
        f"You are an elite newsletter writer producing a '{style}'. "
        f"Audience: {style_meta['audience']}. Editorial focus: {style_meta['focus']}. "
        f"Voice/style of this issue ({writing_mode}): {mode_desc} "
        "Write with substance — concrete details, no filler, no generic platitudes. "
        "Every claim should feel grounded in the supplied research."
    )

    insights = research_data.get("insights", [])
    statistics = research_data.get("statistics", [])
    ref_lines = "\n".join(
        f"- {r.get('title')} ({r.get('source_name')}): {r.get('url')}"
        for r in references[:12]
    )

    user = (
        f"Topic / theme of this issue: {topic}\n"
        f"Industry: {industry}\n\n"
        f"Research synthesis: {research_data.get('summary', '')}\n\n"
        f"Key insights to draw from:\n" + "\n".join(f"- {i}" for i in insights) + "\n\n"
        f"Statistics/data points available:\n" + "\n".join(f"- {s}" for s in statistics) + "\n\n"
        f"Source items (for links in industry updates):\n{ref_lines}\n\n"
        "Write the complete newsletter and return JSON with EXACTLY these keys:\n"
        "{\n"
        '  "title": "compelling newsletter issue title",\n'
        '  "subject_line": "email subject line under 60 chars, high open-rate",\n'
        '  "introduction": "2-3 paragraph engaging opener",\n'
        '  "key_insights": [{"heading": "...", "body": "1-2 paragraphs"}],\n'
        '  "industry_updates": [{"headline": "...", "summary": "...", "url": "..."}],\n'
        '  "actionable_takeaways": ["3-5 concrete actions the reader can take"],\n'
        '  "closing": "warm 1 paragraph sign-off",\n'
        '  "call_to_action": "single clear CTA sentence"\n'
        "}"
    )

    try:
        data = llm.complete_json(system, user, temperature=0.7, max_tokens=3000)
        return _assemble(topic, industry, style, writing_mode, data, references)
    except Exception:
        return _heuristic_newsletter(
            topic, industry, style, writing_mode, research_data, references, style_meta
        )


def _assemble(topic, industry, style, writing_mode, data: dict, references) -> dict:
    body = {
        "title": data.get("title") or f"{topic} — This Week",
        "subject_line": data.get("subject_line") or f"{topic}: what you need to know",
        "introduction": data.get("introduction", ""),
        "key_insights": data.get("key_insights", []),
        "industry_updates": data.get("industry_updates", []),
        "actionable_takeaways": data.get("actionable_takeaways", []),
        "closing": data.get("closing", ""),
        "call_to_action": data.get("call_to_action", ""),
    }
    return {
        "title": body["title"],
        "subject_line": body["subject_line"],
        "topic": topic,
        "industry": industry,
        "style": style,
        "writing_mode": writing_mode,
        "status": "draft",
        "body_json": body,
        "source_count": len(references),
        "engagement_score": estimate_engagement(body),
    }


def _heuristic_newsletter(topic, industry, style, writing_mode, research, references, style_meta) -> dict:
    """Template-based newsletter when no LLM is available (demo mode)."""
    insights = research.get("insights", [])
    stats = research.get("statistics", [])
    updates = [
        {"headline": r.get("title"), "summary": r.get("summary", "")[:240], "url": r.get("url")}
        for r in references[:6]
    ]
    body = {
        "title": f"{topic}: The {style.split()[0]} Brief",
        "subject_line": f"{topic} — your {writing_mode.lower()} digest",
        "introduction": (
            f"Welcome to this issue, written for {style_meta['audience']}. "
            f"{research.get('summary', '')} Below: the developments worth your attention "
            f"in {industry}."
        ),
        "key_insights": [
            {"heading": ins[:80], "body": ins} for ins in insights[:5]
        ],
        "industry_updates": updates,
        "actionable_takeaways": [
            f"Review the top item on {topic} and share it with your team.",
            "Pick one statistic from this issue and validate it against your own data.",
            "Identify one experiment to run this week based on these trends.",
        ],
        "closing": "That's it for this issue. Reply and tell us what you'd like covered next.",
        "call_to_action": "Forward this to one person who'd find it useful.",
    }
    if stats:
        body["actionable_takeaways"].insert(0, f"Note this data point: {stats[0]}")
    return {
        "title": body["title"],
        "subject_line": body["subject_line"],
        "topic": topic,
        "industry": industry,
        "style": style,
        "writing_mode": writing_mode,
        "status": "draft",
        "body_json": body,
        "source_count": len(references),
        "engagement_score": estimate_engagement(body),
    }


# --------------------------------------------------------------------------- #
# Engagement prediction (heuristic)
# --------------------------------------------------------------------------- #
def estimate_engagement(body: dict) -> float:
    """Predict a 0-100 engagement score from structural signals.

    This is a transparent heuristic (not a trained model): rewards a strong
    subject line, presence of statistics, concrete CTA, and balanced length.
    """
    score = 50.0
    subject = body.get("subject_line", "")
    if 20 <= len(subject) <= 60:
        score += 10
    if any(c.isdigit() for c in subject):
        score += 5
    if body.get("call_to_action"):
        score += 8
    insights = body.get("key_insights", [])
    score += min(len(insights) * 3, 12)
    score += min(len(body.get("actionable_takeaways", [])) * 2, 8)
    intro_len = len(body.get("introduction", "").split())
    if 40 <= intro_len <= 160:
        score += 7
    return round(min(score, 99), 1)
