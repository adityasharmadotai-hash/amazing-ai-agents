"""
brief.py — The AI brain of the Founder Daily Brief Agent.

Turns the raw connector snapshot into:
  • a daily founder brief (greeting, headline metrics, suggested focus)
  • AI insights (priorities, risks, opportunities, follow-ups, next actions)
  • answers to free-form questions (search assistant)
  • per-meeting preparation briefs

Everything has a deterministic, rule-based fallback so the dashboard is fully
functional without an OpenAI key — the key simply upgrades the narrative quality.
"""

import json
from datetime import datetime

from . import ai
from . import connectors as cx


def _fmt_money(x) -> str:
    try:
        return f"${x:,.0f}"
    except Exception:
        return f"${x}"


def _greeting_word() -> str:
    h = datetime.now().hour
    if h < 12:
        return "Good Morning"
    if h < 17:
        return "Good Afternoon"
    return "Good Evening"


def _context_for_ai(ctx: dict) -> str:
    """Compact JSON snapshot the model can reason over (trimmed for tokens)."""
    def email_brief(e):
        return {"from": e["sender"], "subject": e["subject"], "priority": e["priority"],
                "category": e["category"], "issue": e.get("is_issue", False)}

    payload = {
        "meetings_today": [{"title": m["title"], "time": m["start"][11:16], "type": m["type"],
                            "attendees": m["attendees"]} for m in ctx["today_meetings"]],
        "important_emails": [email_brief(e) for e in ctx["important_emails"]],
        "pending_followups": [{"from": e["sender"], "subject": e["subject"]} for e in ctx["pending_followups"]],
        "customer_issues": [{"from": e["sender"], "subject": e["subject"]} for e in ctx["customer_issues"]],
        "open_tasks": [{"title": t["title"], "project": t["project"], "status": t["status"],
                        "priority": t["priority"]} for t in ctx["open_tasks"]],
        "slack_unanswered": [{"channel": m["channel"], "user": m["user"], "text": m["text"]}
                             for m in ctx["unanswered_slack"]],
        "revenue_yesterday": ctx["revenue_yesterday"],
        "revenue_7d": ctx["revenue_7d"],
        "mrr_estimate": ctx["mrr"],
        "scores": ctx["scores"],
    }
    return json.dumps(payload, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# DAILY BRIEF
# ══════════════════════════════════════════════════════════════════════════════

def generate_brief(founder_name: str, ctx: dict) -> dict:
    metrics = {
        "meetings": len(ctx["today_meetings"]),
        "important_emails": len(ctx["important_emails"]),
        "followups": len(ctx["pending_followups"]),
        "customer_issues": len(ctx["customer_issues"]),
        "open_actions": len(ctx["open_tasks"]),
        "revenue_yesterday": ctx["revenue_yesterday"],
    }

    if ai.is_configured():
        try:
            system = (
                "You are an elite chief of staff to a startup founder. You write crisp, "
                "high-signal daily briefings. No fluff. Return ONLY valid JSON.")
            user = f"""Founder: {founder_name}
Today is {datetime.now().strftime('%A, %B %d, %Y')}.

Here is this morning's snapshot across Gmail, Calendar, Notion, Slack, and revenue:
{_context_for_ai(ctx)}

Write the founder's daily brief. Return EXACTLY this JSON:
{{
  "summary": "2-3 sentence executive summary of where the day stands.",
  "suggested_focus": "The single most valuable thing the founder should focus on today, plus 1-2 supporting actions. 2-3 sentences, specific and actionable.",
  "highlights": ["3-5 short bullet highlights — the things that actually matter today"],
  "watch_outs": ["1-3 short risk / time-sensitive items to not drop"]
}}"""
            data = ai.complete_json(system, user, tokens=900, temperature=0.5)
            data["metrics"] = metrics
            data["greeting"] = f"{_greeting_word()} {founder_name}"
            data["generated_at"] = datetime.now().isoformat()
            data["ai"] = True
            return data
        except Exception:
            pass  # fall through to rule-based

    return _fallback_brief(founder_name, ctx, metrics)


def _fallback_brief(founder_name: str, ctx: dict, metrics: dict) -> dict:
    issues = ctx["customer_issues"]
    fu = ctx["pending_followups"]
    hi_tasks = [t for t in ctx["open_tasks"] if t["priority"] == "high"]

    highlights = []
    if metrics["meetings"]:
        first = ctx["today_meetings"][0]
        highlights.append(f"{metrics['meetings']} meetings today — first up: {first['title']} at {first['start'][11:16]}.")
    if metrics["important_emails"]:
        highlights.append(f"{metrics['important_emails']} important emails need a look.")
    if metrics["revenue_yesterday"]:
        highlights.append(f"{_fmt_money(metrics['revenue_yesterday'])} in revenue landed yesterday.")
    if hi_tasks:
        highlights.append(f"{len(hi_tasks)} high-priority action items open, incl. \"{hi_tasks[0]['title']}\".")

    watch = []
    for i in issues[:2]:
        watch.append(f"Customer issue from {i['sender']}: {i['subject']}")
    if fu:
        watch.append(f"{len(fu)} follow-ups pending ({', '.join(e['sender'] for e in fu[:3])}).")

    focus_bits = []
    if hi_tasks:
        focus_bits.append(f"Knock out \"{hi_tasks[0]['title']}\"")
    if fu:
        focus_bits.append(f"follow up with {len(fu)} contacts ({', '.join(e['sender'] for e in fu[:2])})")
    if issues:
        focus_bits.append(f"resolve the issue from {issues[0]['sender']}")
    suggested = ". ".join(focus_bits[:3]) + "." if focus_bits else "Clear your inbox and prep for today's meetings."

    return {
        "greeting": f"{_greeting_word()} {founder_name}",
        "summary": (f"You have {metrics['meetings']} meetings, {metrics['important_emails']} important emails, "
                    f"and {metrics['open_actions']} open action items. "
                    f"{_fmt_money(metrics['revenue_yesterday'])} came in yesterday."),
        "suggested_focus": suggested,
        "highlights": highlights or ["A quiet morning — good time for deep work."],
        "watch_outs": watch or ["Nothing urgent flagged."],
        "metrics": metrics,
        "generated_at": datetime.now().isoformat(),
        "ai": False,
    }


# ══════════════════════════════════════════════════════════════════════════════
# AI INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════

def generate_insights(ctx: dict) -> dict:
    if ai.is_configured():
        try:
            system = ("You are a sharp startup operator advising a founder. Be specific and "
                      "decision-oriented. Return ONLY valid JSON.")
            user = f"""Snapshot of the founder's tools this morning:
{_context_for_ai(ctx)}

Analyse and return EXACTLY this JSON:
{{
  "priorities": [{{"title":"...","why":"one sentence on why it matters today"}}],
  "risks": [{{"title":"...","detail":"one sentence"}}],
  "opportunities": [{{"title":"...","detail":"one sentence"}}],
  "followups": [{{"who":"name","action":"what to send/say"}}],
  "next_actions": ["concrete next step", "..."]
}}
Give 3-5 items in priorities, next_actions; 2-4 in the rest."""
            data = ai.complete_json(system, user, tokens=1400, temperature=0.5)
            data["ai"] = True
            return data
        except Exception:
            pass
    return _fallback_insights(ctx)


def _fallback_insights(ctx: dict) -> dict:
    hi_tasks = [t for t in ctx["open_tasks"] if t["priority"] == "high"]
    blocked = [t for t in ctx["open_tasks"] if t["status"] == "Blocked"]
    issues = ctx["customer_issues"]
    fu = ctx["pending_followups"]

    priorities = [{"title": t["title"], "why": f"High priority in {t['project']}."} for t in hi_tasks[:5]]
    if not priorities:
        priorities = [{"title": "Triage inbox and Slack", "why": "Stay responsive to customers and team."}]

    risks = []
    for b in blocked[:2]:
        risks.append({"title": f"Blocked: {b['title']}", "detail": f"{b['project']} is stalled until this clears."})
    for i in issues[:2]:
        risks.append({"title": f"Customer issue: {i['sender']}", "detail": i["subject"]})

    opportunities = []
    rev = ctx["revenue_yesterday"]
    if rev:
        opportunities.append({"title": "Revenue momentum", "detail": f"{_fmt_money(rev)} yesterday — good time to push expansion."})
    opportunities.append({"title": "Pipeline follow-ups", "detail": f"{len(fu)} warm threads awaiting your reply."})

    followups = [{"who": e["sender"], "action": f"Reply re: {e['subject']}"} for e in fu[:4]]
    next_actions = [f"Resolve: {i['subject']}" for i in issues[:2]]
    next_actions += [t["title"] for t in hi_tasks[:3]]

    return {
        "priorities": priorities,
        "risks": risks or [{"title": "No major risks", "detail": "Smooth sailing today."}],
        "opportunities": opportunities,
        "followups": followups,
        "next_actions": next_actions or ["Plan tomorrow's top 3."],
        "ai": False,
    }


# ══════════════════════════════════════════════════════════════════════════════
# SEARCH ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════

def ask(question: str, ctx: dict) -> str:
    if ai.is_configured():
        try:
            system = ("You are the founder's executive assistant. Answer ONLY from the provided "
                      "snapshot data. Be concise, use bullet points when listing. If the data "
                      "doesn't cover it, say so briefly.")
            user = f"""Snapshot:
{_context_for_ai(ctx)}

Founder's question: {question}"""
            return ai.complete(system, user, tokens=700, temperature=0.4)
        except Exception:
            pass
    return _fallback_answer(question, ctx)


def _fallback_answer(question: str, ctx: dict) -> str:
    q = question.lower()
    if any(w in q for w in ["meeting", "calendar", "schedule"]):
        ms = ctx["today_meetings"]
        if not ms:
            return "You have no meetings on the calendar today."
        lines = [f"You have **{len(ms)} meetings** today:"]
        lines += [f"- {m['start'][11:16]} — {m['title']} ({', '.join(m['attendees'])})" for m in ms]
        return "\n".join(lines)
    if any(w in q for w in ["follow", "client", "customer"]):
        fu = ctx["pending_followups"]
        issues = ctx["customer_issues"]
        lines = [f"**{len(fu)} follow-ups pending:**"]
        lines += [f"- {e['sender']} — {e['subject']}" for e in fu]
        if issues:
            lines.append(f"\n**{len(issues)} customer issues:**")
            lines += [f"- {e['sender']} — {e['subject']}" for e in issues]
        return "\n".join(lines)
    if any(w in q for w in ["revenue", "mrr", "money", "sales", "$"]):
        return (f"**Revenue yesterday:** {_fmt_money(ctx['revenue_yesterday'])}\n"
                f"**Last 7 days:** {_fmt_money(ctx['revenue_7d'])}\n"
                f"**Estimated MRR:** {_fmt_money(ctx['mrr'])}")
    if any(w in q for w in ["risk", "danger", "worry", "problem", "block"]):
        ins = _fallback_insights(ctx)
        lines = ["**Top risks this week:**"]
        lines += [f"- {r['title']}: {r['detail']}" for r in ins["risks"]]
        return "\n".join(lines)
    if any(w in q for w in ["task", "todo", "action", "do today", "attention", "focus"]):
        hi = [t for t in ctx["open_tasks"] if t["priority"] == "high"]
        lines = ["**What needs your attention today:**"]
        lines += [f"- {t['title']} ({t['project']})" for t in (hi or ctx["open_tasks"])[:6]]
        return "\n".join(lines)
    # default summary
    s = ctx["scores"]
    return (f"Here's where things stand: {len(ctx['today_meetings'])} meetings, "
            f"{len(ctx['important_emails'])} important emails, {len(ctx['open_tasks'])} open tasks, "
            f"{len(ctx['customer_issues'])} customer issues. "
            f"Inbox health {s['inbox_health']}/100, productivity {s['productivity']}/100. "
            f"(Add an OpenAI key in Settings for smarter answers.)")


# ══════════════════════════════════════════════════════════════════════════════
# MEETING PREP
# ══════════════════════════════════════════════════════════════════════════════

def meeting_prep(meeting: dict, ctx: dict) -> str:
    if ai.is_configured():
        try:
            system = ("You are a chief of staff preparing a founder for a meeting. Output a tight, "
                      "skimmable prep brief in markdown: objective, talking points, likely questions, "
                      "and the desired outcome. Keep it under 180 words.")
            related = [e for e in cx.get_emails()
                       if any(a.split()[0].lower() in e["sender"].lower() for a in meeting["attendees"])]
            rel_txt = "\n".join(f"- {e['sender']}: {e['subject']} — {e['snippet']}" for e in related) or "None"
            user = f"""Meeting: {meeting['title']}
Time: {meeting['start'][11:16]}–{meeting['end'][11:16]}
Type: {meeting['type']}
Attendees: {', '.join(meeting['attendees'])}
Notes: {meeting.get('notes','')}

Related recent emails:
{rel_txt}

Write the prep brief."""
            return ai.complete(system, user, tokens=500, temperature=0.5)
        except Exception:
            pass
    # fallback
    return (f"**Objective:** {meeting.get('notes','Align and move things forward.')}\n\n"
            f"**Attendees:** {', '.join(meeting['attendees'])}\n\n"
            f"**Talking points:**\n- Review status and open items\n- Confirm next steps and owners\n"
            f"- Surface any blockers\n\n"
            f"**Desired outcome:** Clear decisions and assigned follow-ups.\n\n"
            f"_Add an OpenAI key in Settings for an AI-tailored prep brief._")
