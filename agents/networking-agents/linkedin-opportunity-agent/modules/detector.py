"""
detector.py — Opportunity detection, AI analysis & lead scoring.

Two engines:
  • AI engine (Claude) — nuanced analysis returning summary, type, rationale,
    recommended action and a confidence score.
  • Fallback engine — deterministic keyword/signal matching used when no API key
    is configured, so the product is fully functional with zero cost.

Both produce the same normalised opportunity dict, so the rest of the app does
not care which engine ran.
"""

from __future__ import annotations

import re

from . import ai

# ── Opportunity taxonomy ─────────────────────────────────────────────────────────
OPPORTUNITY_TYPES = [
    "Hiring",
    "Sales / Buying Intent",
    "Partnership",
    "Funding",
    "Networking",
    "Lead / Client",
    "Collaboration",
]

# Signal phrases per category. Used by the fallback engine and to give the AI a
# strong prior. Keep them lowercase — matching is case-insensitive.
SIGNALS: dict[str, list[str]] = {
    "Hiring": [
        "we are hiring", "we're hiring", "now hiring", "join our team",
        "looking for engineers", "looking for a", "open position", "open role",
        "open roles", "job opening", "hiring for", "apply now", "we have an opening",
        "growing our team", "expanding the team", "recruiting",
    ],
    "Sales / Buying Intent": [
        "looking for solutions", "looking for a tool", "tool recommendations",
        "recommend a", "any recommendations", "vendor", "evaluating", "rfp",
        "request for proposal", "need a platform", "shopping for", "in the market for",
        "looking for a vendor", "which tool", "best tool for", "switching from",
    ],
    "Partnership": [
        "seeking partners", "looking for partners", "partnership", "strategic alliance",
        "collaboration opportunity", "co-marketing", "reseller", "channel partner",
        "integration partner", "partner with us",
    ],
    "Funding": [
        "raised", "funding", "seed round", "series a", "series b", "series c",
        "closed our round", "backed by", "led by", "pre-seed", "venture",
        "we are thrilled to announce our", "million in funding", "fundraise",
    ],
    "Networking": [
        "founder introductions", "happy to connect", "let's connect", "open to connect",
        "attending", "speaking at", "see you at", "meetup", "community", "intro to",
        "looking to meet", "coffee chat", "join the conversation",
    ],
    "Lead / Client": [
        "need help with", "looking for an agency", "looking for a consultant",
        "looking for a freelancer", "who can help", "looking to hire a", "any experts",
        "looking for a developer", "looking for a designer",
    ],
    "Collaboration": [
        "let's collaborate", "guest post", "co-author", "joint webinar",
        "work together", "collaborate on", "looking for collaborators",
    ],
}

# Buying-intent boosters that raise a lead's score regardless of category.
INTENT_BOOSTERS = [
    "budget", "asap", "urgently", "this quarter", "decision", "evaluating",
    "demo", "pricing", "buy", "purchase", "contract", "rolling out",
]

SCORE_BANDS = [(75, "High"), (50, "Medium"), (0, "Low")]


def label_for(score: int) -> str:
    for threshold, label in SCORE_BANDS:
        if score >= threshold:
            return label
    return "Low"


# ── Fallback (deterministic) engine ──────────────────────────────────────────────
def _match_signals(text: str) -> dict[str, list[str]]:
    low = text.lower()
    found: dict[str, list[str]] = {}
    for category, phrases in SIGNALS.items():
        hits = [p for p in phrases if p in low]
        if hits:
            found[category] = hits
    return found


def _engagement_score(post: dict) -> int:
    """Cheap proxy for engagement: longer, well-formed posts with @ mentions /
    questions tend to be higher-signal. Bounded contribution."""
    text = post.get("text", "") or ""
    score = 0
    if "?" in text:
        score += 5
    if len(text) > 280:
        score += 5
    if re.search(r"#\w+", text):
        score += 3
    if re.search(r"@\w+", text):
        score += 2
    return min(score, 15)


def fallback_analyze(post: dict, keywords: list[str], industries: list[str]) -> dict | None:
    """Rule-based analysis. Returns None when no opportunity signal is present."""
    text = post.get("text", "") or ""
    low = text.lower()
    found = _match_signals(text)
    if not found:
        return None

    # Choose the dominant category (most phrase hits).
    opp_type = max(found, key=lambda c: len(found[c]))
    matched_phrases = found[opp_type]

    # ── Score components (0-100) ────────────────────────────────────────────────
    relevance = min(len(matched_phrases) * 18, 45)
    kw_hits = [k for k in keywords if k and k.lower() in low]
    keyword_score = min(len(kw_hits) * 12, 24)
    industry_match = 0
    detected_industry = post.get("industry", "") or ""
    for ind in industries:
        if ind and (ind.lower() in low or ind.lower() == detected_industry.lower()):
            industry_match = 16
            detected_industry = detected_industry or ind
            break
    intent = min(sum(1 for b in INTENT_BOOSTERS if b in low) * 6, 18)
    engagement = _engagement_score(post)

    score = min(relevance + keyword_score + industry_match + intent + engagement, 100)
    confidence = min(60 + len(matched_phrases) * 8 + len(kw_hits) * 4, 96)

    action = _fallback_action(opp_type, post.get("author_name", "this person"))
    return {
        "opp_type": opp_type,
        "summary": _truncate(text, 220),
        "why_it_matters": _fallback_why(opp_type, detected_industry),
        "recommended_action": action,
        "confidence": confidence,
        "score_value": score,
        "score_label": label_for(score),
        "industry": detected_industry,
        "signals": matched_phrases + [f"keyword:{k}" for k in kw_hits],
        "ai_generated": False,
    }


def _fallback_why(opp_type: str, industry: str) -> str:
    base = {
        "Hiring": "An active hiring signal — a warm moment to pitch talent, services, or a partnership.",
        "Sales / Buying Intent": "Explicit buying intent — the author is actively evaluating solutions.",
        "Partnership": "A partnership/alliance request that maps to a collaboration opportunity.",
        "Funding": "Fresh capital usually means new budget, hiring, and tooling decisions.",
        "Networking": "A low-friction networking opening to start a genuine relationship.",
        "Lead / Client": "A direct request for help — a potential inbound client.",
        "Collaboration": "An invitation to collaborate on content or projects.",
    }.get(opp_type, "A relevant opportunity worth a timely, personalised reply.")
    if industry:
        base += f" (Industry: {industry}.)"
    return base


def _fallback_action(opp_type: str, name: str) -> str:
    return {
        "Hiring": f"Send {name} a tailored note referencing the role and how you can help fill or support it.",
        "Sales / Buying Intent": f"Reply with a concise, helpful recommendation, then offer {name} a short call.",
        "Partnership": f"Propose a specific partnership angle to {name} with a clear mutual benefit.",
        "Funding": f"Congratulate {name} on the raise and open a conversation about their next priorities.",
        "Networking": f"Send {name} a personal connection request that references the post.",
        "Lead / Client": f"Reply with a quick, relevant insight and ask {name} a qualifying question.",
        "Collaboration": f"Pitch {name} one concrete collaboration idea with a clear next step.",
    }.get(opp_type, f"Send {name} a personalised, value-first message within 24 hours.")


def _truncate(text: str, n: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


# ── AI engine (Claude) ───────────────────────────────────────────────────────────
_AI_SYSTEM = """You are an expert B2B sales, recruiting and networking analyst.
You read a single LinkedIn post and decide whether it represents a high-value
OPPORTUNITY for the user, then analyse it.

Opportunity types (choose exactly one that fits best):
Hiring, Sales / Buying Intent, Partnership, Funding, Networking, Lead / Client, Collaboration.

Scoring guidance (score_value 0-100): weigh relevance to the user's keywords/
industries, strength of buying or hiring intent, engagement signals, and how
actionable the post is. 75-100 = High, 50-74 = Medium, 0-49 = Low.

Respond with ONLY a JSON object, no prose, in this exact shape:
{
  "is_opportunity": true | false,
  "opp_type": "<one type above>",
  "summary": "<one tight sentence describing the opportunity>",
  "why_it_matters": "<one sentence on why the user should care>",
  "recommended_action": "<one concrete next step the user should take>",
  "confidence": <integer 0-100>,
  "score_value": <integer 0-100>,
  "industry": "<best-guess industry or empty string>",
  "signals": ["<key phrase or reason>", "..."]
}
If the post is not a genuine opportunity, set is_opportunity to false."""


def ai_analyze(post: dict, keywords: list[str], industries: list[str]) -> dict | None:
    """Claude-powered analysis. Returns None when the post is genuinely not an
    opportunity. Raises on an API/parse error so the caller can fall back to the
    deterministic engine instead of silently dropping the post."""
    user = _build_user_prompt(post, keywords, industries)
    data = ai.complete_json(_AI_SYSTEM, user, max_tokens=700)
    return _normalise_ai(data, post)


def build_ai_prompt(post: dict, keywords: list[str], industries: list[str]) -> tuple[str, str]:
    """Expose (system, user) for the async scanner."""
    return _AI_SYSTEM, _build_user_prompt(post, keywords, industries)


def _build_user_prompt(post: dict, keywords: list[str], industries: list[str]) -> str:
    return (
        f"User keywords: {', '.join(keywords) or '(none)'}\n"
        f"User target industries: {', '.join(industries) or '(none)'}\n\n"
        f"LinkedIn post by {post.get('author_name','Unknown')} "
        f"({post.get('author_headline','')}) at {post.get('company','')}:\n"
        f"\"\"\"\n{post.get('text','')}\n\"\"\""
    )


def normalise_ai_response(data: dict, post: dict) -> dict | None:
    """Public wrapper for the async scanner."""
    return _normalise_ai(data, post)


def _normalise_ai(data: dict, post: dict) -> dict | None:
    if not isinstance(data, dict) or not data.get("is_opportunity"):
        return None
    score = int(data.get("score_value", 0) or 0)
    score = max(0, min(score, 100))
    opp_type = data.get("opp_type") or "Networking"
    if opp_type not in OPPORTUNITY_TYPES:
        opp_type = "Networking"
    signals = data.get("signals") or []
    if not isinstance(signals, list):
        signals = [str(signals)]
    return {
        "opp_type": opp_type,
        "summary": str(data.get("summary", "")).strip() or _truncate(post.get("text", ""), 200),
        "why_it_matters": str(data.get("why_it_matters", "")).strip(),
        "recommended_action": str(data.get("recommended_action", "")).strip(),
        "confidence": max(0, min(int(data.get("confidence", 0) or 0), 100)),
        "score_value": score,
        "score_label": label_for(score),
        "industry": str(data.get("industry", "") or post.get("industry", "")).strip(),
        "signals": [str(s) for s in signals][:8],
        "ai_generated": True,
    }


# ── Unified entry point ──────────────────────────────────────────────────────────
def analyze_post(post: dict, keywords: list[str], industries: list[str]) -> dict | None:
    """Analyse one post with the best available engine.

    With a key configured we trust Claude's verdict (a returned None means "not
    an opportunity"). Only if the API call itself errors do we fall back to the
    deterministic engine, so no post is silently dropped on a transient failure.
    """
    if ai.is_configured():
        try:
            return ai_analyze(post, keywords, industries)
        except Exception:
            pass  # transient API/parse error → use the rule-based engine
    return fallback_analyze(post, keywords, industries)
