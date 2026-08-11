"""
knowledge.py — the business "brain food": the profile the agent answers from,
the qualifying questions it collects, and the greeting style.

Everything is stored in the `settings` table (as JSON) so the team can edit it
live from the dashboard without touching code or redeploying. `DEFAULT_PROFILE`
seeds a sensible starting point on first run.
"""

from __future__ import annotations

from typing import Any

from . import database

# Keys in the settings table.
K_PROFILE = "business_profile"
K_QUESTIONS = "qualifying_questions"
K_CONFIG = "agent_config"
K_EXAMPLES = "conversation_examples"

# Extra profile fields the agent uses (merged onto whatever profile is stored, so
# older profiles still work). Edit their real values in the dashboard.
PROFILE_EXTRAS: dict[str, Any] = {
    "scheduling_link": "",   # e.g. a Calendly link — shared when a lead wants to book
    "jobs": [],              # list of {title, stack, location, level, notes}
    "knowledge_doc": "",     # freeform reference text the agent may answer from
}

# A few past exchanges that show the human tone we want (few-shot style guide).
# Seeded from Aditya's real FutrBridge replies; edit/extend in the dashboard.
DEFAULT_EXAMPLES: list[dict[str, str]] = [
    {
        "customer": "Hello! I filled out your form and would like to know more about your business.",
        "reply": "Hey! Thanks for reaching out to FutrBridge. We get software engineers in front of the SF Bay Area companies that actually matter — mostly Full Stack and Backend roles. Quick one so I can point you the right way: are you more Backend or Full Stack, and roughly how many years in?",
    },
    {
        "customer": "What do you charge?",
        "reply": "Good question — let me have Aditya confirm the exact details with you directly so nothing's off. In the meantime, what kind of role are you targeting?",
    },
    {
        "customer": "I can talk between 12-6 pm",
        "reply": "Perfect, I'll set that up. Which day works better for you — today or tomorrow?",
    },
]


DEFAULT_PROFILE: dict[str, Any] = {
    "business_name": "Your Company",
    "one_liner": "We help people find great jobs.",
    "about": (
        "We are a recruiting company that connects qualified candidates with "
        "employers. Leads usually reach us from our Instagram ads."
    ),
    "offerings": [
        "Free candidate placement — we match you to open roles at no cost to you.",
        "Resume review and interview preparation.",
    ],
    "locations": ["San Francisco Bay Area"],
    "hours": "Mon–Sat, 9am–7pm. Messages outside these hours are answered next working hour by a human; the assistant replies instantly any time.",
    "website": "https://example.com",
    "pricing": "Our service is free for candidates.",
    "faqs": [
        {"q": "How much does it cost?", "a": "It's completely free for candidates."},
        {"q": "What kind of roles do you place?", "a": "Full-time and contract roles across the Bay Area, from entry level to senior."},
        {"q": "How fast can I get placed?", "a": "It depends on the role and your profile, but many candidates hear back within a week."},
    ],
    # Things the agent must NEVER guess at — always escalate instead.
    "escalate_topics": [
        "specific salary or offer negotiation for a named company",
        "legal, visa, or immigration guarantees",
        "anything requiring access to the person's private account or documents",
    ],
}


# Each question the agent should try to collect. `key` is stored in the
# conversation's qualification JSON; `ask` is a natural phrasing hint for the model.
DEFAULT_QUESTIONS: list[dict[str, str]] = [
    {"key": "name", "ask": "their name", "why": "so we can address them personally"},
    {"key": "role_interest", "ask": "what kind of role or work they're looking for", "why": "to match them to openings"},
    {"key": "location", "ask": "which city / area they're based in or open to", "why": "to check we serve their area"},
    {"key": "experience", "ask": "their years of experience or current/most recent role", "why": "to gauge fit"},
    {"key": "availability", "ask": "when they can start / their availability", "why": "to prioritise urgent seekers"},
]


DEFAULT_CONFIG: dict[str, Any] = {
    # Persona / tone for the greeting and replies.
    "assistant_name": "Ava",
    "tone": "warm, friendly, concise — like a helpful human teammate, not a robot",
    "greeting_style": (
        "Greet them by referencing that they reached out (often from our Instagram ad), "
        "introduce yourself by first name, and ask ONE opening question. Keep it short."
    ),
    # If the model's confidence in an answer is below this, escalate to a human.
    "escalation_confidence": 55,
    # After this many collected answers, wrap up qualifying and reassure them a
    # human will follow up.
    "max_questions_before_handoff": 5,
}


# ── accessors (seed defaults on first read) ───────────────────────────────────
def get_profile() -> dict:
    prof = database.get_setting(K_PROFILE)
    if prof is None:
        prof = dict(DEFAULT_PROFILE)
        database.set_setting(K_PROFILE, prof)
    # Make sure the newer fields (jobs, scheduling_link, knowledge_doc) always
    # exist so the agent can rely on them even on an older stored profile.
    for k, v in PROFILE_EXTRAS.items():
        prof.setdefault(k, v)
    return prof


def save_profile(profile: dict) -> None:
    database.set_setting(K_PROFILE, profile)


def get_questions() -> list[dict]:
    qs = database.get_setting(K_QUESTIONS)
    if qs is None:
        database.set_setting(K_QUESTIONS, DEFAULT_QUESTIONS)
        return list(DEFAULT_QUESTIONS)
    return qs


def save_questions(questions: list[dict]) -> None:
    database.set_setting(K_QUESTIONS, questions)


def get_config() -> dict:
    cfg = database.get_setting(K_CONFIG)
    if cfg is None:
        database.set_setting(K_CONFIG, DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    # Merge in any newly added defaults for forward compatibility.
    merged = dict(DEFAULT_CONFIG)
    merged.update(cfg)
    return merged


def save_config(cfg: dict) -> None:
    database.set_setting(K_CONFIG, cfg)


def get_examples() -> list[dict]:
    ex = database.get_setting(K_EXAMPLES)
    if ex is None:
        database.set_setting(K_EXAMPLES, DEFAULT_EXAMPLES)
        return list(DEFAULT_EXAMPLES)
    return ex


def save_examples(examples: list[dict]) -> None:
    database.set_setting(K_EXAMPLES, examples)


def seed_defaults() -> None:
    """Ensure the core settings exist (called on startup)."""
    get_profile()
    get_questions()
    get_config()
    get_examples()
