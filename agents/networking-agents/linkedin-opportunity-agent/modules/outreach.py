"""
outreach.py — AI Outreach Assistant.

Generates connection requests, personalised first messages, follow-ups, and
networking introductions for a given opportunity. Uses Claude when configured,
otherwise falls back to high-quality templates so the feature always works.
"""

from __future__ import annotations

from . import ai

MESSAGE_KINDS = {
    "connection": "LinkedIn connection request (≤ 280 chars, no link)",
    "message": "Personalised first message / InMail",
    "followup": "Polite follow-up message (sent 3-5 days later)",
    "intro": "Warm networking introduction the user can forward",
}

_SYSTEM = """You are an expert at warm, concise, non-spammy LinkedIn outreach.
Write in the user's voice: friendly, specific, value-first, and human. Never use
hype, never sound like a template, and reference the actual post. Keep it short.
Output ONLY the message text — no preamble, no quotes, no subject line unless asked."""


def _user_prompt(opp: dict, kind: str, sender_name: str, sender_role: str) -> str:
    return (
        f"Write a {MESSAGE_KINDS[kind]}.\n\n"
        f"From: {sender_name or 'me'}"
        + (f", {sender_role}" if sender_role else "")
        + "\n"
        f"To: {opp.get('person_name','')} — {opp.get('person_headline','')} "
        f"at {opp.get('company','')}\n"
        f"Opportunity type: {opp.get('opp_type','')}\n"
        f"Their post: \"{(opp.get('post_text') or '')[:600]}\"\n"
        f"Why it matters: {opp.get('why_it_matters','')}\n"
        f"Recommended action: {opp.get('recommended_action','')}\n\n"
        "Make it personal and reference something concrete from their post."
    )


def generate_message(
    opp: dict, kind: str = "message", sender_name: str = "", sender_role: str = ""
) -> str:
    """Generate one outreach message of the requested kind."""
    if kind not in MESSAGE_KINDS:
        kind = "message"
    if ai.is_configured():
        try:
            return ai.complete(_SYSTEM, _user_prompt(opp, kind, sender_name, sender_role),
                               max_tokens=500).strip().strip('"')
        except Exception:
            pass
    return _template(opp, kind, sender_name, sender_role)


# ── Template fallback ────────────────────────────────────────────────────────────
def _template(opp: dict, kind: str, sender_name: str, sender_role: str) -> str:
    name = (opp.get("person_name") or "there").split()[0]
    company = opp.get("company") or "your company"
    opp_type = opp.get("opp_type", "")
    me = sender_name or "—"
    role = f" ({sender_role})" if sender_role else ""

    topic = {
        "Hiring": f"the roles you're hiring for at {company}",
        "Sales / Buying Intent": "the tooling you're evaluating",
        "Partnership": "the partnership you mentioned",
        "Funding": "your recent raise",
        "Networking": "what you shared",
        "Lead / Client": "the help you're looking for",
        "Collaboration": "the collaboration you proposed",
    }.get(opp_type, "your recent post")

    if kind == "connection":
        return (
            f"Hi {name} — saw your post about {topic} and it really resonated. "
            f"Would love to connect and follow your work. — {me}"
        )[:280]
    if kind == "followup":
        return (
            f"Hi {name}, just floating this back to the top of your inbox. "
            f"I know things get busy after a post like yours about {topic}. "
            f"Happy to share a quick, relevant idea whenever the timing's right — no pressure. "
            f"Best,\n{me}{role}"
        )
    if kind == "intro":
        return (
            f"Quick intro: {name} at {company} recently posted about {topic}. "
            f"I think there's a strong fit with what {me}{role} is working on. "
            f"Connecting you both here — I'll let you take it from here!"
        )
    # default: personalised first message
    why = opp.get("why_it_matters") or "it stood out"
    action = opp.get("recommended_action") or "I would love to compare notes."
    return (
        f"Hi {name},\n\n"
        f"Your post about {topic} caught my eye — {why}\n\n"
        f"{action}\n\n"
        f"Would you be open to a short conversation this week?\n\n"
        f"Best,\n{me}{role}"
    )
