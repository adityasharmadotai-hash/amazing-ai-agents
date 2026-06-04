"""
Auxiliary AI features.

Small, focused generators used throughout the editor:
* subject-line variations
* CTA suggestions
* newsletter hooks / openers
* content recommendations (gaps to fill)
* future newsletter ideas

Each function returns a plain list[str] and falls back to sensible
deterministic suggestions when the LLM is unavailable.
"""

from __future__ import annotations

from modules.llm import LLMClient


def _list_or_fallback(llm: LLMClient, system: str, user: str, fallback: list[str], n: int) -> list[str]:
    if not llm.available:
        return fallback[:n]
    try:
        data = llm.complete_json(system, user, temperature=0.9)
        if isinstance(data, dict):
            data = data.get("items") or next(iter(data.values()), [])
        items = [str(x).strip() for x in data if str(x).strip()]
        return items[:n] or fallback[:n]
    except Exception:
        return fallback[:n]


def subject_line_variations(topic: str, current: str, style: str, llm: LLMClient, n: int = 6) -> list[str]:
    system = (
        "You are an email marketing expert who writes high-open-rate subject lines. "
        "Vary the angle: curiosity, number-led, urgency, benefit, contrarian, question."
    )
    user = (
        f"Newsletter style: {style}. Topic: {topic}. Current subject: '{current}'.\n"
        f"Write {n} distinct subject lines, each under 60 characters. "
        'Return a JSON array of strings.'
    )
    fallback = [
        f"{topic}: 5 things you missed",
        f"Why {topic} matters this week",
        f"The {topic} update you need",
        f"Inside {topic}: what's changing",
        f"{topic}, decoded",
        f"Is {topic} about to shift?",
    ]
    return _list_or_fallback(llm, system, user, fallback, n)


def cta_suggestions(topic: str, style: str, llm: LLMClient, n: int = 5) -> list[str]:
    system = "You write punchy newsletter calls-to-action that drive a single clear action."
    user = (
        f"Style: {style}. Topic: {topic}. Write {n} distinct CTA sentences "
        "(subscribe, share, reply, book, download). Return a JSON array of strings."
    )
    fallback = [
        "Forward this to a colleague who'd find it useful.",
        "Reply and tell us what to cover next week.",
        "Subscribe to never miss an issue.",
        "Share your take with us — hit reply.",
        "Book a 15-minute call to go deeper.",
    ]
    return _list_or_fallback(llm, system, user, fallback, n)


def newsletter_hooks(topic: str, style: str, llm: LLMClient, n: int = 5) -> list[str]:
    system = "You write scroll-stopping opening hooks for newsletters — first line that earns the second."
    user = (
        f"Style: {style}. Topic: {topic}. Write {n} distinct opening-line hooks. "
        "Return a JSON array of strings."
    )
    fallback = [
        f"Everyone's talking about {topic}. Almost everyone is wrong.",
        f"This week, {topic} crossed a line that's hard to walk back.",
        f"Three numbers explain everything happening in {topic} right now.",
        f"If you only read one thing about {topic}, make it this.",
        f"We dug into {topic} so you don't have to.",
    ]
    return _list_or_fallback(llm, system, user, fallback, n)


def content_recommendations(topic: str, existing_titles: list[str], llm: LLMClient, n: int = 5) -> list[str]:
    system = "You are a content strategist spotting coverage gaps for a newsletter."
    titles = "; ".join(existing_titles[:15]) or "none yet"
    user = (
        f"Topic: {topic}. Already covered: {titles}.\n"
        f"Suggest {n} angles/sub-topics NOT yet covered that the audience would value. "
        "Return a JSON array of strings."
    )
    fallback = [
        f"A beginner's primer on {topic}",
        f"Contrarian take: what the {topic} hype gets wrong",
        f"Interview-style breakdown with a {topic} practitioner",
        f"Tooling roundup for {topic}",
        f"What {topic} looks like 12 months from now",
    ]
    return _list_or_fallback(llm, system, user, fallback, n)


def future_ideas(topic: str, industry: str, style: str, llm: LLMClient, n: int = 6) -> list[str]:
    system = "You are an editorial planner generating a forward calendar of newsletter issue ideas."
    user = (
        f"Style: {style}. Industry: {industry}. Anchor topic: {topic}.\n"
        f"Propose {n} compelling future issue concepts (title-like). "
        "Return a JSON array of strings."
    )
    fallback = [
        f"The state of {industry}: a quarterly deep-dive",
        f"{topic} myths, busted",
        f"Builders to watch in {industry}",
        f"The economics of {topic}",
        f"A field guide to {topic} for newcomers",
        f"Predictions: {industry} next year",
    ]
    return _list_or_fallback(llm, system, user, fallback, n)
