"""
generator.py — GPT-4o proposal generation engine.
One comprehensive call generates all sections as structured JSON.
Individual sections can be regenerated independently.
"""

import json, os, re
from datetime import datetime
import streamlit as st
from openai import OpenAI


TEMPLATE_CONTEXTS = {
    "Agency":      "You are a senior account manager at a top creative agency. Write confidently, creatively, and results-focused.",
    "SaaS":        "You are a SaaS solutions architect. Write technically yet accessibly, focused on ROI and scalability.",
    "Consulting":  "You are a senior Big 4 management consultant. Write authoritatively, analytically, and strategically.",
    "Marketing":   "You are a growth marketing director. Write in a data-driven, results-oriented, energetic tone.",
    "Development": "You are a lead software engineer and CTO. Write precisely, technically, and delivery-focused.",
}


def _client() -> OpenAI:
    try:
        key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY","")
    except Exception:
        key = os.environ.get("OPENAI_API_KEY","")
    return OpenAI(api_key=key)


def is_configured() -> bool:
    try:
        key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY","")
    except Exception:
        key = os.environ.get("OPENAI_API_KEY","")
    return bool(key)


def _call(system: str, user: str, tokens: int = 3000) -> str:
    r = _client().chat.completions.create(
        model="gpt-4o", max_tokens=tokens, temperature=0.72,
        messages=[{"role":"system","content":system},{"role":"user","content":user}]
    )
    return r.choices[0].message.content.strip()


def _parse_json(text: str):
    return json.loads(re.sub(r"```(?:json)?|```","",text).strip())


# ── Full proposal generation ──────────────────────────────────────────────────

def generate_full_proposal(
    client_name: str, project_type: str, budget: str,
    timeline: str, requirements: str, template: str,
    agency_name: str, extra_context: str = "",
) -> dict:
    today = datetime.now().strftime("%B %d, %Y")
    system = f"""{TEMPLATE_CONTEXTS.get(template, TEMPLATE_CONTEXTS['Agency'])}
You write compelling, winning business proposals. Return ONLY valid JSON — no fences, no preamble."""

    user = f"""Generate a complete professional {template} proposal:

AGENCY: {agency_name}
CLIENT: {client_name}
PROJECT TYPE: {project_type}
BUDGET: {budget}
TIMELINE: {timeline}
REQUIREMENTS: {requirements}
DATE: {today}
{f"EXTRA CONTEXT: {extra_context}" if extra_context else ""}

Return EXACTLY this JSON (all fields required, make content specific to this client and project):
{{
  "proposal_title": "Compelling proposal title (not generic)",
  "tagline": "One punchy value proposition line",
  "executive_summary": "3-4 paragraphs. Acknowledge the client challenge, present your solution, describe the transformation.",
  "about_us": "2 paragraphs. Expertise, track record, and why you are the right partner.",
  "problem_statement": "2 paragraphs. The client's pain points and what is at stake if not addressed.",
  "proposed_solution": "3 paragraphs. Approach, methodology, and why it is the best fit.",
  "scope_of_work": [
    {{"phase":"Phase 1: Discovery & Strategy","duration":"2 weeks","deliverables":["Stakeholder interviews","Competitive analysis","Strategic roadmap"],"description":"What happens in this phase"}},
    {{"phase":"Phase 2: Design & Development","duration":"4 weeks","deliverables":["Wireframes","Design system","Core build"],"description":"What happens in this phase"}},
    {{"phase":"Phase 3: Testing & Launch","duration":"2 weeks","deliverables":["QA testing","Client training","Go-live"],"description":"What happens in this phase"}}
  ],
  "timeline": [
    {{"milestone":"Project Kickoff","week":"Week 1","description":"Onboarding, access, kickoff call"}},
    {{"milestone":"Strategy Approved","week":"Week 2","description":"Direction signed off by client"}},
    {{"milestone":"First Delivery","week":"Week 4","description":"Core deliverable for review"}},
    {{"milestone":"Revisions Complete","week":"Week 6","description":"All feedback incorporated"}},
    {{"milestone":"Final Handover","week":"Week 8","description":"Launch and handover"}}
  ],
  "pricing": {{
    "intro": "2 sentences on pricing philosophy and value delivered",
    "packages": [
      {{"name":"Starter","price":"Budget-appropriate","description":"Core deliverables","features":["Feature 1","Feature 2","Feature 3"],"recommended":false}},
      {{"name":"Professional","price":"Budget-appropriate","description":"Full scope as outlined","features":["Feature 1","Feature 2","Feature 3","Feature 4","Feature 5"],"recommended":true}},
      {{"name":"Enterprise","price":"Budget-appropriate","description":"Full scope plus premium support","features":["Feature 1","Feature 2","Feature 3","Feature 4","Feature 5","Feature 6"],"recommended":false}}
    ],
    "payment_terms": "e.g. 50% deposit upfront, 25% at mid-point, 25% on final delivery",
    "included": ["Item 1","Item 2","Item 3","Item 4"],
    "excluded": ["Item 1","Item 2","Item 3"]
  }},
  "why_us": [
    {{"title":"Reason 1","description":"Why this matters to the client"}},
    {{"title":"Reason 2","description":"Why this matters to the client"}},
    {{"title":"Reason 3","description":"Why this matters to the client"}},
    {{"title":"Reason 4","description":"Why this matters to the client"}}
  ],
  "case_study": {{
    "title":"Relevant past project title",
    "client":"Industry or anonymised client",
    "challenge":"The problem (2 sentences)",
    "solution":"What was done (2 sentences)",
    "result":"Measurable outcome — e.g. 47% increase in conversions"
  }},
  "terms": {{
    "intellectual_property":"IP ownership clause — who owns what upon full payment",
    "confidentiality":"NDA and confidentiality obligations",
    "revisions":"Number of revision rounds included and process",
    "payment":"Payment schedule and late payment policy",
    "termination":"Notice period and termination conditions for both parties",
    "liability":"Limitation of liability clause",
    "governing_law":"Jurisdiction and governing law"
  }},
  "next_steps": [
    "Review and approve this proposal",
    "Sign the contract and pay the deposit",
    "Kickoff meeting scheduled within 3 business days"
  ],
  "closing_statement": "1-2 paragraphs. Warm close reinforcing excitement and creating urgency."
}}"""

    try:
        raw  = _call(system, user, tokens=4000)
        data = _parse_json(raw)
        data["_meta"] = {
            "client_name": client_name, "project_type": project_type,
            "budget": budget, "timeline": timeline, "template": template,
            "agency_name": agency_name, "today": today,
            "generated_at": datetime.now().isoformat(),
        }
        return data
    except Exception as e:
        return {"error": str(e)}


# ── Regenerate a single section ───────────────────────────────────────────────

def regenerate_section(section_name: str, proposal: dict, instruction: str = "") -> str:
    meta = proposal.get("_meta",{})
    system = f"""{TEMPLATE_CONTEXTS.get(meta.get('template','Agency'), TEMPLATE_CONTEXTS['Agency'])}
Rewrite one section of a business proposal. Return ONLY the rewritten text — no JSON, no headings, no labels."""
    user = f"""Rewrite the "{section_name}" section. Make it more compelling and persuasive.
Client: {meta.get('client_name','')} | Project: {meta.get('project_type','')} | Budget: {meta.get('budget','')}
{f"Instruction: {instruction}" if instruction else ""}
Current version: {str(proposal.get(section_name,''))[:400]}
Write 2-3 improved paragraphs."""
    try:
        return _call(system, user, tokens=700)
    except Exception as e:
        return f"Error: {e}"


# ── Cover letter generation ───────────────────────────────────────────────────

def generate_cover_letter(proposal: dict, tone: str = "professional") -> str:
    meta = proposal.get("_meta",{})
    system = f"You write compelling {tone} business emails. Be warm but professional."
    user = f"""Write a 3-paragraph cover email accompanying this proposal:
Client: {meta.get('client_name','')} | Agency: {meta.get('agency_name','')}
Project: {meta.get('project_type','')} | Title: {proposal.get('proposal_title','')}
Summary snippet: {str(proposal.get('executive_summary',''))[:200]}
Open with genuine excitement. Summarise key value. End with a clear CTA."""
    try:
        return _call(system, user, tokens=500)
    except Exception as e:
        return f"Error: {e}"


# ── Quick price estimate ──────────────────────────────────────────────────────

def quick_pricing_estimate(project_type: str, requirements: str, timeline: str) -> dict:
    system = "You are a senior project manager. Return ONLY valid JSON."
    user = f"""Estimate pricing:
Project: {project_type} | Requirements: {requirements} | Timeline: {timeline}
Return: {{"low":"£X,XXX","high":"£XX,XXX","recommended":"£XX,XXX","reasoning":"2 sentences","hours":"XX-XX hours","hourly":"£XXX/hr"}}"""
    try:
        return _parse_json(_call(system, user, tokens=300))
    except Exception as e:
        return {"error": str(e)}
