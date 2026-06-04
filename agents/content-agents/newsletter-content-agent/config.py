"""
Central configuration for the Newsletter Content Agent.

Holds all tunable constants: model names, enumerations for newsletter
styles / writing modes / sources, scheduling options and export formats.
Keeping these in one place makes the rest of the codebase declarative and
easy to extend.
"""

import os
from dataclasses import dataclass, field

# --------------------------------------------------------------------------- #
# OpenAI / model settings
# --------------------------------------------------------------------------- #
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_MODEL_FAST = os.getenv("OPENAI_MODEL_FAST", "gpt-4o-mini")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))

DB_PATH = os.getenv("NEWSLETTER_DB", "newsletter_agent.db")

APP_NAME = "Quill"
APP_TAGLINE = "Autonomous Newsletter Content Agent"

# --------------------------------------------------------------------------- #
# Content source catalogue
# --------------------------------------------------------------------------- #
# Each source type maps to a collector strategy in modules/content_sources.py
SOURCE_TYPES = [
    "RSS Feed",
    "News Website",
    "Blog",
    "Reddit",
    "Twitter/X",
    "LinkedIn",
    "YouTube",
    "Company Website",
]

SOURCE_ICONS = {
    "RSS Feed": "📡",
    "News Website": "📰",
    "Blog": "✍️",
    "Reddit": "👽",
    "Twitter/X": "🐦",
    "LinkedIn": "💼",
    "YouTube": "▶️",
    "Company Website": "🏢",
}

# --------------------------------------------------------------------------- #
# Newsletter styles
# --------------------------------------------------------------------------- #
NEWSLETTER_STYLES = {
    "Founder Newsletter": {
        "audience": "startup founders and operators",
        "focus": "company building, fundraising, leadership lessons and candid founder stories",
        "tone_hint": "candid, first-person, lessons-learned",
    },
    "AI Newsletter": {
        "audience": "AI engineers, researchers and builders",
        "focus": "model releases, research breakthroughs, tooling and practical AI applications",
        "tone_hint": "technically credible but accessible",
    },
    "Startup Newsletter": {
        "audience": "early-stage startup ecosystem",
        "focus": "funding rounds, launches, growth tactics and market shifts",
        "tone_hint": "energetic, opportunity-focused",
    },
    "Marketing Newsletter": {
        "audience": "growth and marketing professionals",
        "focus": "campaigns, channels, conversion tactics and brand strategy",
        "tone_hint": "actionable, data-backed",
    },
    "Recruiting Newsletter": {
        "audience": "recruiters, talent leaders and hiring managers",
        "focus": "hiring trends, sourcing strategy, candidate experience and talent markets",
        "tone_hint": "people-first, practical",
    },
    "Technology Newsletter": {
        "audience": "engineers and technology decision-makers",
        "focus": "infrastructure, developer tooling, security and emerging tech",
        "tone_hint": "precise, forward-looking",
    },
    "Finance Newsletter": {
        "audience": "investors, analysts and finance professionals",
        "focus": "markets, macro trends, deals and financial strategy",
        "tone_hint": "analytical, measured",
    },
}

# --------------------------------------------------------------------------- #
# AI writing modes
# --------------------------------------------------------------------------- #
WRITING_MODES = {
    "Professional": "Polished, business-appropriate, confident and concise.",
    "Educational": "Explanatory and clear, defining concepts and teaching the reader.",
    "Conversational": "Warm, direct, second-person, like writing to a friend.",
    "Technical": "Precise and detailed, comfortable with jargon and specifics.",
    "Thought Leadership": "Opinionated and visionary, framing big-picture narratives.",
}

# --------------------------------------------------------------------------- #
# Scheduling + email + export
# --------------------------------------------------------------------------- #
SCHEDULE_FREQUENCIES = ["Daily", "Weekly", "Monthly"]

EMAIL_PROVIDERS = ["Gmail", "Mailchimp", "ConvertKit", "Beehiiv"]

EXPORT_FORMATS = ["HTML", "Markdown", "PDF", "DOCX"]

INDUSTRIES = [
    "Artificial Intelligence",
    "SaaS",
    "Fintech",
    "Healthcare",
    "E-commerce",
    "Cybersecurity",
    "Climate Tech",
    "Developer Tools",
    "Marketing",
    "Recruiting / HR Tech",
    "General Technology",
]


@dataclass
class AppSettings:
    """Runtime settings resolved from the environment / UI."""

    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = OPENAI_MODEL
    temperature: float = OPENAI_TEMPERATURE

    @property
    def has_api_key(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key.strip())
