"""
Job Market Intelligence Agent
Orchestrates Dice + Indeed + HubSpot MCP servers via the Anthropic API
to surface high-intent hiring companies as HireGen.co prospects.
"""

import anthropic
import json
from typing import Generator

# ── MCP server config ────────────────────────────────────────────────────────
MCP_SERVERS = [
    {"type": "url", "url": "https://mcp.dice.com/mcp",       "name": "dice"},
    {"type": "url", "url": "https://mcp.indeed.com/claude/mcp", "name": "indeed"},
    {"type": "url", "url": "https://mcp.hubspot.com/anthropic", "name": "hubspot"},
]

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are the Job Market Intelligence Agent for HireGen.co, a specialized recruiting firm focused on AI and engineering talent.

Your mission: monitor Dice and Indeed for companies actively hiring at scale, identify the highest-value prospects for HireGen.co's outreach, and automatically create or update them as deals/contacts in HubSpot CRM.

## Workflow

### Step 1 — Search job boards
Search both Dice and Indeed for the target job categories provided. Run searches in parallel where possible. Collect all postings with company name, role title, location, and posting date.

### Step 2 — Aggregate by company
Group all postings by company name. Count how many relevant roles each company is posting. A company posting 3+ relevant roles in the past 30 days is a HIGH-INTENT prospect.

### Step 3 — Score and rank prospects
Score each company:
- 5+ roles posting = Priority A (urgent outreach)
- 3–4 roles = Priority B (this week)
- 1–2 roles = Priority C (pipeline)

Also note: remote-friendly roles, SF Bay Area hiring, and LLM/AI-specific roles get a priority boost.

### Step 4 — Enrich with company context
For each Priority A and B company, use Indeed's company data tool to pull: industry, company size, headquarters location, and a brief description.

### Step 5 — Create/update HubSpot
For each qualified prospect:
- Search HubSpot contacts/companies to check if they already exist
- If new: create a HubSpot company record with all enriched data
- If existing: update the record with fresh job posting count and date
- Add a HubSpot note summarizing the hiring signal and recommended outreach angle
- Set deal stage to "Prospect - Hiring Signal Detected"

### Step 6 — Report
Return a structured JSON summary with:
{
  "run_date": "ISO date",
  "jobs_found": total count,
  "companies_analyzed": count,
  "prospects_created": count,
  "prospects_updated": count,
  "priority_a": [ { "company": "...", "roles": N, "hubspot_id": "...", "top_roles": [...] } ],
  "priority_b": [ ... ],
  "priority_c": [ ... ],
  "highlights": "2–3 sentence narrative of the most interesting findings"
}

## Rules
- Always check HubSpot before creating to avoid duplicates
- Never create a prospect with fewer than 1 confirmed job posting
- Log every HubSpot action clearly (created vs updated)
- If a tool call fails, log the error and continue — do not abort the entire run
- Be concise in notes; recruiters scan fast
- Focus on engineering roles: Backend, Full Stack, ML/AI, Platform, Infrastructure, Data
"""

# ── Agent runner ──────────────────────────────────────────────────────────────

def run_agent(
    job_categories: list[str],
    location: str = "San Francisco, CA",
    min_roles_threshold: int = 3,
    stream_callback=None,
) -> dict:
    """
    Run the Job Market Intelligence Agent.

    Args:
        job_categories: list of job titles/keywords to search (e.g. ["ML Engineer", "Backend"])
        location: target hiring location filter
        min_roles_threshold: minimum roles a company must post to qualify
        stream_callback: optional callable(event_type, text) for UI streaming

    Returns:
        dict with 'result' (parsed JSON summary) and 'raw_response' (full text)
    """
    client = anthropic.Anthropic()

    user_message = f"""Run a full job market intelligence scan with these parameters:

Job categories to search: {', '.join(job_categories)}
Target location: {location}
Minimum roles for prospect qualification: {min_roles_threshold}
Priority boost: companies posting AI/LLM/ML roles, remote-friendly positions

Search both Dice and Indeed. Identify high-intent hiring companies, enrich the top prospects, create or update them in HubSpot CRM, and return the structured JSON report.

Today's date context: use recent postings (last 30 days preferred).
"""

    if stream_callback:
        stream_callback("status", "🔍 Connecting to MCP servers...")

    # Use extended thinking + streaming for the full agentic workflow
    full_text = ""
    input_tokens = 0
    output_tokens = 0

    try:
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
            mcp_servers=MCP_SERVERS,
        ) as stream:
            for event in stream:
                event_type = type(event).__name__

                if event_type == "RawContentBlockDeltaEvent":
                    delta = event.delta
                    if hasattr(delta, "text"):
                        full_text += delta.text
                        if stream_callback:
                            stream_callback("text", delta.text)

                elif event_type == "RawMessageStartEvent":
                    if stream_callback:
                        stream_callback("status", "🤖 Agent started...")

                elif event_type == "RawContentBlockStartEvent":
                    block = event.content_block
                    block_type = getattr(block, "type", "")
                    if block_type == "tool_use":
                        tool_name = getattr(block, "name", "unknown_tool")
                        if stream_callback:
                            stream_callback("tool", f"⚙️ Calling: {tool_name}")

                elif event_type == "RawMessageStopEvent":
                    if stream_callback:
                        stream_callback("status", "✅ Agent completed")

            # Get final message for token usage
            final = stream.get_final_message()
            if hasattr(final, "usage"):
                input_tokens = final.usage.input_tokens
                output_tokens = final.usage.output_tokens

    except Exception as e:
        if stream_callback:
            stream_callback("error", f"Agent error: {str(e)}")
        return {"result": None, "raw_response": str(e), "error": str(e)}

    # Parse JSON from response
    parsed = _extract_json(full_text)

    return {
        "result": parsed,
        "raw_response": full_text,
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    }


def _extract_json(text: str) -> dict | None:
    """Extract the JSON report block from the agent's response text."""
    import re

    # Look for ```json ... ``` block first
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Fall back: find the outermost { ... } block
    start = text.find("{")
    if start != -1:
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        break

    return None
