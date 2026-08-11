"""
agent.py — Gemini 2.5 Pro reasoning engine.

Consumes the compact stats from `analytics.build_stats_payload()` and produces
the plain-English intelligence the spec asks for: performance analysis (§2),
daily recommendations aware of past outcomes (§3/§4), lead-quality learning (§6),
the daily summary (§9), and the chat assistant (§10). All data comes from the
team's own campaigns — no web/search grounding is used.
"""

from __future__ import annotations

import json
import os
import re
import time

from . import config

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None

log = config.get_logger("admanager.agent")
MODEL_NAME = config.GEMINI_MODEL

_PERSONA = (
    "You are the marketing analyst for a recruiting company that runs Instagram "
    "lead-generation ads to attract qualified job seekers in the San Francisco Bay Area. "
    "Your goal is to increase QUALIFIED applicants while REDUCING advertising cost. "
    "You explain numbers in plain English a non-technical marketer can act on. "
    "Be specific, cite the actual metric values you were given, and never invent data.\n\n"
    "HARD RULES (always follow):\n"
    "1. This account advertises on INSTAGRAM ONLY. Never mention, suggest, or recommend "
    "Facebook, Facebook placements, Audience Network, or Messenger.\n"
    "2. Only reference campaigns, ads, placements, or audiences that actually appear in the "
    "data with non-zero activity. Never invent a channel, placement, campaign, or audience.\n"
    "3. Leads are pre-qualified by a conditional application form. If the data shows a high "
    "qualified rate, do NOT treat lead quality as a problem — focus on getting MORE leads at "
    "a LOWER cost. Only raise quality concerns if the data truly shows many rejected/invalid leads."
)


class AgentError(RuntimeError):
    pass


def _api_key() -> str:
    if st is not None:
        try:
            val = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
            if val:
                return str(val)
        except Exception:
            pass
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")


def is_configured() -> bool:
    return bool(_api_key())


def _model(json_mode: bool = True):
    import google.generativeai as genai

    genai.configure(api_key=_api_key())
    gen_config = {"temperature": 0.4}
    if json_mode:
        gen_config["response_mime_type"] = "application/json"
    return genai.GenerativeModel(MODEL_NAME, generation_config=gen_config)


def _call(prompt: str, json_mode: bool = True, retries: int = 2) -> str:
    if not is_configured():
        raise AgentError("GEMINI_API_KEY is not set.")
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            model = _model(json_mode=json_mode)
            resp = model.generate_content(f"{_PERSONA}\n\n{prompt}")
            return (resp.text or "").strip()
        except Exception as e:  # pragma: no cover - network/SDK errors
            last_err = e
            log.warning("Gemini call failed (attempt %d/%d): %s", attempt + 1, retries + 1, e)
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise AgentError(f"Gemini call failed after {retries + 1} attempts: {last_err}")


def _safe_json(text: str, default):
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        # Best-effort: grab the first {...} or [...] block.
        m = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        return default


def _compact(stats: dict) -> str:
    return json.dumps(stats, ensure_ascii=False, default=str)


# ── §2 Performance analysis ───────────────────────────────────────────────────
def analyze_performance(stats: dict) -> dict:
    prompt = f"""
Analyze today's Instagram ad performance from this JSON snapshot:

{_compact(stats)}

WRITING RULES (important — keep it simple):
- Write for a busy non-marketer. Short, plain sentences.
- MAX 3 items per list. Each item ONE short sentence.
- Say "cost per lead" not "CPL". Write money as $6.04 (no backticks, no code formatting).
- Only include what truly matters; use empty lists [] for the rest.

Return ONLY JSON with these keys (lists of plain-English strings):
{{
  "headline": "one plain sentence: the single most important takeaway",
  "best_performing": ["what's working, with a number"],
  "worst_performing": ["the biggest problem, with a number"],
  "improving": ["only if clearly improving"],
  "declining": ["only if clearly declining"],
  "anomalies": ["anything unusual worth a glance"],
  "cost_opportunities": ["simple ways to spend less per lead"],
  "lead_quality_opportunities": ["simple ways to get MORE leads at lower cost (quality is already handled by the pre-qualifying form)"],
  "observations": ["at most 2 quick facts"]
}}
""".strip()
    return _safe_json(
        _call(prompt),
        {"headline": "", "best_performing": [], "worst_performing": [], "improving": [],
         "declining": [], "anomalies": [], "cost_opportunities": [],
         "lead_quality_opportunities": [], "observations": []},
    )


# ── §3/§4 Daily recommendations (past-outcome aware) ──────────────────────────
def daily_recommendations(stats: dict, past_recs: list[dict]) -> list[dict]:
    history = json.dumps(
        [
            {"target": r["target"], "type": r["type"], "status": r["status"], "outcome": r["outcome"]}
            for r in past_recs[:20]
        ],
        default=str,
    )
    # Recommendations must target ACTIVE campaigns/ads only — never paused/completed.
    active = [c for c in stats.get("campaigns", []) if str(c.get("status", "")).lower() == "active"]
    scoped = {**stats, "campaigns": active}
    prompt = f"""
Current performance snapshot (ACTIVE campaigns only — the campaigns list below is
already filtered to active ads; do NOT recommend anything for paused/completed ones):
{_compact(scoped)}

Previous recommendations and how they turned out (learn from what worked):
{history}

Produce today's action recommendations. Prefer actions similar to ones that
previously led to "improved" outcomes; avoid repeating ones that led to "worse".

WRITING RULES: plain English, no jargon, no backticks. Write money as $12.34.
Keep "rationale" to ONE short sentence a non-marketer understands.
Every recommendation MUST target an ACTIVE campaign/ad from the data above.
Instagram only — never suggest Facebook, Audience Network, or any placement/audience
that is not present in the data. Since leads are pre-qualified, prioritise MORE leads
at LOWER cost over "lead quality".

Return ONLY a JSON array (max 6 items, most important first), each:
{{
  "type": "one of: Increase budget, Decrease budget, Pause ad, Scale ad, Test new audience, Improve ad copy, Improve headline, Improve CTA, New creative idea, A/B test",
  "target": "which campaign/ad/audience it applies to",
  "rationale": "ONE short plain sentence with the key number",
  "priority": "high | medium | low",
  "confidence": <integer 0-100 — how sure you are this helps>,
  "expected_impact": "short outcome, e.g. 'lower cost per lead ~15%' or '+8 qualified leads/wk'"
}}
""".strip()
    data = _safe_json(_call(prompt), [])
    return data if isinstance(data, list) else []


# ── Creative suggestions (ad ideas) ───────────────────────────────────────────
def creative_suggestions(stats: dict, count: int = 4) -> list[dict]:
    prompt = f"""
Based on this performance + audience data, propose {count} fresh Instagram ad
creative concepts to attract QUALIFIED Bay Area job seekers. Favor formats and
angles that our best-performing placements/audiences suggest.

{_compact(stats)}

Return ONLY a JSON array, each item:
{{
  "format": "Reel | Story | Carousel | Single image",
  "angle": "the core idea / theme in a few words",
  "hook": "the first line / on-screen text that stops the scroll",
  "caption": "1-2 sentence caption",
  "cta": "the call to action",
  "why": "why this should work, citing our data"
}}
""".strip()
    data = _safe_json(_call(prompt), [])
    return data if isinstance(data, list) else []


# ── Audience targeting recommendations ────────────────────────────────────────
def audience_recommendations(audience_stats: dict) -> dict:
    prompt = f"""
Here is our audience/age/ad lead-quality breakdown (qualified_rate = % of leads
the recruiting team marked Qualified/Interview/Hired):

{json.dumps(audience_stats, default=str)}

Recommend how to reallocate targeting to raise lead quality and lower wasted spend.
Return ONLY JSON:
{{
  "scale_up": ["audiences/ages to invest more in, with the reason"],
  "scale_down": ["audiences/ages to cut or refine, with the reason"],
  "test_ideas": ["new audiences worth testing"],
  "summary": "one-sentence takeaway"
}}
""".strip()
    return _safe_json(_call(prompt),
                      {"scale_up": [], "scale_down": [], "test_ideas": [], "summary": ""})


# ── Executive summary (richer than daily_summary) ─────────────────────────────
def executive_summary(stats: dict) -> dict:
    prompt = f"""
Write a concise executive summary for leadership from this snapshot, including the
health score and the 7-day forecast that are embedded in the data.

{_compact(stats)}

Return ONLY JSON:
{{
  "headline": "one punchy sentence on where the account stands",
  "health_read": "interpret the health score in plain English",
  "wins": ["2-3 concrete wins with numbers"],
  "risks": ["2-3 concrete risks with numbers"],
  "forecast_note": "what the next 7 days look like and why",
  "priorities": ["the top 3 actions for this week, in order"]
}}
""".strip()
    return _safe_json(
        _call(prompt),
        {"headline": "", "health_read": "", "wins": [], "risks": [],
         "forecast_note": "", "priorities": []},
    )


# ── Short forecast narrative ──────────────────────────────────────────────────
def forecast_narrative(forecast_summary: dict) -> str:
    if not forecast_summary:
        return "Not enough history yet to forecast — sync a few more days of data."
    prompt = (
        "In 2-3 plain-English sentences, explain this 7-day ad forecast for a "
        "non-technical marketer and what to watch:\n" + json.dumps(forecast_summary, default=str)
    )
    return _call(prompt, json_mode=False)


# ── §6 Learn from lead feedback ───────────────────────────────────────────────
def learn_from_leads(lead_quality: dict) -> dict:
    prompt = f"""
Here is our lead-quality feedback, grouped by audience, age range, ad, and campaign.
"qualified_rate" is the % of leads the recruiting team marked Qualified/Interview/Hired:

{json.dumps(lead_quality, default=str)}

Identify what distinguishes high-quality lead sources from low-quality ones, and how
future campaigns should change. Return ONLY JSON:
{{
  "insights": ["plain-English findings, e.g. 'Audience X: 62% qualified vs Y: 11%'"],
  "recommendations": ["concrete changes to targeting/creative to raise lead quality"]
}}
""".strip()
    return _safe_json(_call(prompt), {"insights": [], "recommendations": []})


# ── §9 Daily summary / notification ───────────────────────────────────────────
def daily_summary(stats: dict) -> dict:
    prompt = f"""
Write today's executive summary for the marketing team from this snapshot:
{_compact(stats)}

Return ONLY JSON:
{{
  "health": "one of: Healthy, Needs attention, At risk — plus a short reason",
  "biggest_improvement": "one sentence",
  "biggest_concern": "one sentence",
  "recommended_actions": ["2-4 concrete next steps"],
  "opportunities": ["1-3 new optimization opportunities"]
}}
""".strip()
    return _safe_json(
        _call(prompt),
        {"health": "", "biggest_improvement": "", "biggest_concern": "",
         "recommended_actions": [], "opportunities": []},
    )


# ── §10 Chat assistant ────────────────────────────────────────────────────────
def chat(question: str, stats: dict, history: list[dict] | None = None) -> str:
    convo = ""
    for turn in (history or [])[-6:]:
        role = "User" if turn.get("role") == "user" else "Assistant"
        convo += f"{role}: {turn.get('content', '')}\n"
    prompt = f"""
You can answer using ONLY this campaign + lead-feedback data:
{_compact(stats)}

{('Conversation so far:' + chr(10) + convo) if convo else ''}
User question: {question}

Answer in clear, concise plain English. Cite specific numbers from the data.
If the data does not contain the answer, say so and suggest what to sync or check.
""".strip()
    return _call(prompt, json_mode=False)
