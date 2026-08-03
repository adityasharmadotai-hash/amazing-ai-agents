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

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None

MODEL_NAME = "gemini-2.5-pro"

_PERSONA = (
    "You are the marketing analyst for a recruiting company that runs Instagram "
    "lead-generation ads to attract qualified job seekers in the San Francisco Bay Area. "
    "Your goal is to increase QUALIFIED applicants while REDUCING advertising cost. "
    "You explain numbers in plain English a non-technical marketer can act on. "
    "Be specific, cite the actual metric values you were given, and never invent data."
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


def _call(prompt: str, json_mode: bool = True) -> str:
    if not is_configured():
        raise AgentError("GEMINI_API_KEY is not set.")
    try:
        model = _model(json_mode=json_mode)
        resp = model.generate_content(f"{_PERSONA}\n\n{prompt}")
        return (resp.text or "").strip()
    except AgentError:
        raise
    except Exception as e:  # pragma: no cover - network/SDK errors
        raise AgentError(f"Gemini call failed: {e}") from e


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

Return ONLY JSON with these keys, each a list of short plain-English strings
(reference concrete numbers; empty list if nothing applies):
{{
  "headline": "one sentence overall read of the account",
  "best_performing": ["..."],
  "worst_performing": ["..."],
  "improving": ["..."],
  "declining": ["..."],
  "anomalies": ["unusual changes worth attention"],
  "cost_opportunities": ["ways to reduce cost per lead / spend"],
  "lead_quality_opportunities": ["ways to get more QUALIFIED leads"],
  "observations": ["e.g. 'Reels outperform Feed', 'CPL up 18% week over week'"]
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
    prompt = f"""
Current performance snapshot:
{_compact(stats)}

Previous recommendations and how they turned out (learn from what worked):
{history}

Produce today's action recommendations. Prefer actions similar to ones that
previously led to "improved" outcomes; avoid repeating ones that led to "worse".
Return ONLY a JSON array (max 8 items), each:
{{
  "type": "one of: Increase budget, Decrease budget, Pause ad, Scale ad, Test new audience, Improve ad copy, Improve headline, Improve CTA, New creative idea, A/B test",
  "target": "which campaign/ad/audience it applies to",
  "rationale": "1-2 sentences citing the numbers",
  "priority": "high | medium | low"
}}
""".strip()
    data = _safe_json(_call(prompt), [])
    return data if isinstance(data, list) else []


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
