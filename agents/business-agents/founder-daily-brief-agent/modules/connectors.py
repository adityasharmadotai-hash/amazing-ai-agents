"""
connectors.py — Data sources for the Founder Daily Brief.

Each business tool (Gmail, Calendar, Notion, Slack, Stripe/Razorpay) is modelled
as a "connector". This module seeds rich, realistic demo data on first run so the
whole dashboard works immediately, and exposes clean read helpers + derived
health/productivity scores that the brief and analytics layers consume.

The seed functions are also the natural integration points: swap the body of
`seed_*` for a real Gmail/Calendar/Notion/Slack API call and the rest of the app
keeps working unchanged.
"""

import uuid
from datetime import datetime, timedelta

import streamlit as st


def _id() -> str:
    return str(uuid.uuid4())[:12]


def _iso(dt: datetime) -> str:
    return dt.isoformat()


# ══════════════════════════════════════════════════════════════════════════════
# SEED DATA — realistic founder morning, generated relative to "now"
# ══════════════════════════════════════════════════════════════════════════════

def _seed_emails(now: datetime) -> list:
    base = now.replace(hour=7, minute=0, second=0, microsecond=0)
    rows = [
        ("Priya Menon", "priya@abccorp.com", "Re: Proposal for ABC Corp — a few questions",
         "Thanks for sending this over. The team loves the direction. Two questions on pricing before we sign…",
         True, "high", "Sales", True, False, 2.0),
        ("Stripe", "receipts@stripe.com", "You received a payment of $1,250.00",
         "A subscription payment from Northwind Labs was successfully processed.",
         True, "low", "Finance", False, False, 1.5),
        ("Daniel Okoye", "daniel@northwindlabs.io", "URGENT: Dashboard is showing stale data",
         "Hey — our analytics dashboard hasn't refreshed since yesterday afternoon. This is blocking our board prep.",
         True, "high", "Customer", True, True, 0.5),
        ("Sara Lin", "sara@team.internal", "Sprint review notes + 2 blockers",
         "Recapping today's standup: onboarding flow is done, but we're blocked on the SSO vendor and need a decision on…",
         True, "medium", "Team", True, False, 3.0),
        ("Marcus Webb", "marcus@vc-frontier.com", "Following up on our chat — term sheet draft",
         "Great speaking last week. Attaching a draft term sheet for your review ahead of partner meeting Thursday.",
         True, "high", "Sales", True, False, 14.0),
        ("Acme Billing", "billing@acme-tools.com", "Your invoice is overdue",
         "Invoice #4521 for $480 is 6 days overdue. Please arrange payment to avoid service interruption.",
         True, "medium", "Finance", True, False, 20.0),
        ("Lena Park", "lena@happycustomer.co", "Loving the new feature 🎉",
         "Just wanted to say the bulk export feature is a game changer for our ops team. Thank you!",
         False, "low", "Customer", False, False, 22.0),
        ("Notion", "team@makenotion.com", "3 pages were updated in your workspace",
         "Activity digest: Q3 Roadmap, Hiring Plan, and Investor Update were edited.",
         True, "low", "Newsletter", False, False, 5.0),
        ("Raj Kapoor", "raj@growthpartners.in", "Partnership opportunity — India expansion",
         "We work with 40+ SaaS companies entering India and think there's a strong fit. Open to a quick call?",
         True, "medium", "Sales", True, False, 26.0),
        ("Tina Alvarez", "tina@northwindlabs.io", "Re: onboarding — one more seat",
         "Could we add one more seat to our plan? Also when is the SSO update landing?",
         True, "medium", "Customer", True, True, 4.0),
    ]
    out = []
    for name, email, subj, snip, unread, pri, cat, fu, issue, hrs_ago in rows:
        out.append({
            "id": _id(),
            "sender": name,
            "sender_email": email,
            "subject": subj,
            "snippet": snip,
            "received": _iso(base - timedelta(hours=hrs_ago)),
            "unread": unread,
            "priority": pri,
            "category": cat,
            "needs_followup": fu,
            "is_issue": issue,
        })
    return out


def _seed_meetings(now: datetime) -> list:
    day = now.replace(second=0, microsecond=0)
    rows = [
        ("Standup — Engineering", 9, 0, 9, 15,
         ["Sara Lin", "Dev team"], "Google Meet", "Internal",
         "Daily sync. Unblock SSO vendor decision."),
        ("ABC Corp — Proposal Walkthrough", 11, 0, 11, 45,
         ["Priya Menon", "ABC procurement"], "Zoom", "Sales",
         "Walk through pricing tiers; address the 2 open questions from Priya's email."),
        ("1:1 with Sara (Eng Lead)", 14, 0, 14, 30,
         ["Sara Lin"], "Office", "Internal",
         "Sprint blockers, hiring plan, SSO timeline."),
        ("Frontier Ventures — Intro Call", 16, 30, 17, 0,
         ["Marcus Webb"], "Google Meet", "Fundraising",
         "Discuss term sheet draft before Thursday's partner meeting."),
    ]
    out = []
    for title, sh, sm, eh, em, att, loc, mtype, notes in rows:
        out.append({
            "id": _id(),
            "title": title,
            "start": _iso(day.replace(hour=sh, minute=sm)),
            "end": _iso(day.replace(hour=eh, minute=em)),
            "attendees": att,
            "location": loc,
            "type": mtype,
            "notes": notes,
        })
    return out


def _seed_tasks(now: datetime) -> list:
    today = now.replace(hour=23, minute=59, second=0, microsecond=0)
    rows = [
        ("Finalise ABC Corp proposal pricing", "ABC Corp Deal", "In Progress", "high", 0),
        ("Approve SSO vendor (blocking onboarding)", "Platform", "Blocked", "high", 0),
        ("Review Frontier Ventures term sheet", "Fundraising", "Open", "high", 1),
        ("Reply to Northwind stale-data issue", "Customer Success", "Open", "high", 0),
        ("Publish Q3 roadmap to Notion", "Product", "In Progress", "medium", 2),
        ("Hire 2nd backend engineer — review candidates", "Hiring", "Open", "medium", 3),
        ("Pay overdue Acme invoice #4521", "Finance", "Open", "low", 1),
        ("Write investor update (May)", "Fundraising", "Done", "medium", -1),
        ("Ship bulk export feature", "Product", "Done", "high", -2),
        ("Set up Razorpay for India payments", "Finance", "Open", "low", 5),
    ]
    out = []
    for title, project, status, pri, due_off in rows:
        out.append({
            "id": _id(),
            "title": title,
            "project": project,
            "status": status,
            "priority": pri,
            "due": _iso(today + timedelta(days=due_off)),
            "updated": _iso(now - timedelta(hours=due_off * 3 + 1)),
        })
    return out


def _seed_slack(now: datetime) -> list:
    rows = [
        ("#engineering", "Sara Lin", "@founder we need a call on the SSO vendor today, it's blocking onboarding 🙏",
         True, True, True, 1.0),
        ("#customer-success", "Amir", "Northwind opened a ticket about stale dashboard data — flagging as P1.",
         False, True, True, 0.7),
        ("#sales", "Jordan", "@founder ABC Corp asked if we can do net-30 terms. Can we?",
         True, True, True, 2.0),
        ("#general", "Lena (HR)", "Reminder: team offsite planning doc needs your input by Friday.",
         False, True, False, 5.0),
        ("#product", "Sara Lin", "Bulk export shipped 🚀 customers already loving it.",
         False, False, False, 6.0),
        ("#random", "Dev", "anyone up for lunch?", False, False, False, 3.0),
    ]
    out = []
    for channel, user, text, mention, unanswered, important, hrs in rows:
        out.append({
            "id": _id(),
            "channel": channel,
            "user": user,
            "text": text,
            "ts": _iso(now - timedelta(hours=hrs)),
            "mention": mention,
            "unanswered": unanswered,
            "important": important,
        })
    return out


def _seed_revenue(now: datetime) -> list:
    today = now.replace(hour=12, minute=0, second=0, microsecond=0)
    # (days_ago, amount, source, customer, type)
    rows = [
        (1, 1250, "Stripe", "Northwind Labs", "subscription"),
        (1, 99, "Stripe", "Lena Park", "subscription"),
        (2, 499, "Stripe", "Brightwave", "one-time"),
        (3, 1250, "Stripe", "Northwind Labs", "subscription"),
        (4, 199, "Razorpay", "Growth Partners", "subscription"),
        (6, 2400, "Stripe", "ABC Corp (pilot)", "one-time"),
        (9, 1250, "Stripe", "Northwind Labs", "subscription"),
        (12, 99, "Stripe", "Indie Maker", "subscription"),
        (15, 850, "Razorpay", "Mumbai SaaS Co", "one-time"),
        (18, 1250, "Stripe", "Northwind Labs", "subscription"),
        (22, 99, "Stripe", "Lena Park", "subscription"),
        (27, 1800, "Stripe", "Brightwave", "one-time"),
    ]
    out = []
    for days_ago, amount, source, customer, rtype in rows:
        out.append({
            "id": _id(),
            "date": _iso((today - timedelta(days=days_ago))),
            "amount": float(amount),
            "source": source,
            "customer": customer,
            "type": rtype,
            "note": "",
        })
    return out


# ══════════════════════════════════════════════════════════════════════════════
# STORE INIT
# ══════════════════════════════════════════════════════════════════════════════

def init_connectors():
    """Seed demo data once per session."""
    now = datetime.now()
    if "seeded" not in st.session_state:
        st.session_state.emails = _seed_emails(now)
        st.session_state.meetings = _seed_meetings(now)
        st.session_state.tasks = _seed_tasks(now)
        st.session_state.slack = _seed_slack(now)
        st.session_state.revenue = _seed_revenue(now)
        st.session_state.seeded = True


def reset_demo_data():
    for k in ("emails", "meetings", "tasks", "slack", "revenue", "seeded",
              "last_brief", "last_insights", "chat_history", "gmail_live"):
        st.session_state.pop(k, None)
    init_connectors()


def emails_are_live() -> bool:
    return bool(st.session_state.get("gmail_live"))


def sync_gmail(max_results: int = 15, query: str = "newer_than:7d") -> tuple:
    """Pull real Gmail, AI-classify it, and replace the email store.

    Returns (ok: bool, message: str). Imports are local to avoid a circular
    import (brief.py imports this module).
    """
    from . import gmail_connector as gc
    from . import brief as bf

    if not gc.is_authenticated():
        return False, "Not connected to Gmail. Connect it in Settings first."
    try:
        raw = gc.fetch_emails(max_results=max_results, query=query)
        init_connectors()
        if not raw:
            st.session_state.gmail_live = True
            st.session_state.emails = []
            return True, "Connected — no matching emails in that window."
        classified = bf.classify_emails(raw)
        st.session_state.emails = classified
        st.session_state.gmail_live = True
        # invalidate cached AI outputs so the brief reflects real mail
        st.session_state.pop("last_brief", None)
        st.session_state.pop("last_insights", None)
        return True, f"Synced {len(classified)} emails from Gmail."
    except Exception as e:
        return False, f"Sync failed: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# READ HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def get_emails() -> list:
    init_connectors()
    return st.session_state.emails


def get_meetings() -> list:
    init_connectors()
    return st.session_state.meetings


def get_today_meetings() -> list:
    today = datetime.now().date()
    out = []
    for m in get_meetings():
        try:
            if datetime.fromisoformat(m["start"]).date() == today:
                out.append(m)
        except Exception:
            pass
    return sorted(out, key=lambda m: m["start"])


def get_tasks() -> list:
    init_connectors()
    return st.session_state.tasks


def get_open_tasks() -> list:
    return [t for t in get_tasks() if t["status"] != "Done"]


def get_slack() -> list:
    init_connectors()
    return st.session_state.slack


def get_revenue() -> list:
    init_connectors()
    return sorted(st.session_state.revenue, key=lambda r: r["date"], reverse=True)


# ── Mutations (manual entry) ────────────────────────────────────────────────────

def add_revenue(amount: float, source: str, customer: str, rtype: str,
                date_iso: str, note: str = "") -> str:
    init_connectors()
    rid = _id()
    st.session_state.revenue.append({
        "id": rid, "amount": float(amount), "source": source,
        "customer": customer, "type": rtype, "date": date_iso, "note": note,
    })
    return rid


def delete_revenue(rid: str):
    init_connectors()
    st.session_state.revenue = [r for r in st.session_state.revenue if r["id"] != rid]


def add_task(title: str, project: str, priority: str, due_iso: str) -> str:
    init_connectors()
    tid = _id()
    st.session_state.tasks.insert(0, {
        "id": tid, "title": title, "project": project, "status": "Open",
        "priority": priority, "due": due_iso, "updated": datetime.now().isoformat(),
    })
    return tid


def set_task_status(tid: str, status: str):
    init_connectors()
    for t in st.session_state.tasks:
        if t["id"] == tid:
            t["status"] = status
            t["updated"] = datetime.now().isoformat()


def mark_email_read(eid: str):
    init_connectors()
    for e in st.session_state.emails:
        if e["id"] == eid:
            e["unread"] = False


# ══════════════════════════════════════════════════════════════════════════════
# DERIVED METRICS
# ══════════════════════════════════════════════════════════════════════════════

def revenue_yesterday() -> float:
    yday = (datetime.now() - timedelta(days=1)).date()
    total = 0.0
    for r in get_revenue():
        try:
            if datetime.fromisoformat(r["date"]).date() == yday:
                total += r["amount"]
        except Exception:
            pass
    return total


def revenue_last_n_days(n: int) -> float:
    cutoff = datetime.now() - timedelta(days=n)
    return sum(r["amount"] for r in get_revenue()
               if _safe_dt(r["date"]) and _safe_dt(r["date"]) >= cutoff)


def estimated_mrr() -> float:
    """MRR estimate from the last 30 days of subscription revenue."""
    cutoff = datetime.now() - timedelta(days=30)
    return sum(r["amount"] for r in get_revenue()
               if r.get("type") == "subscription" and _safe_dt(r["date"]) and _safe_dt(r["date"]) >= cutoff)


def _safe_dt(iso: str):
    try:
        return datetime.fromisoformat(iso)
    except Exception:
        return None


def customer_issues() -> list:
    return [e for e in get_emails() if e.get("is_issue")]


def pending_followups() -> list:
    return [e for e in get_emails() if e.get("needs_followup")]


def important_emails() -> list:
    return [e for e in get_emails() if e.get("priority") == "high" or e.get("is_issue")]


def unread_emails() -> list:
    return [e for e in get_emails() if e.get("unread")]


def slack_mentions() -> list:
    return [m for m in get_slack() if m.get("mention")]


def unanswered_slack() -> list:
    return [m for m in get_slack() if m.get("unanswered")]


# ── Scores (0–100) ──────────────────────────────────────────────────────────────

def inbox_health_score() -> int:
    unread = len(unread_emails())
    fu = len(pending_followups())
    issues = len(customer_issues())
    score = 100 - unread * 4 - fu * 5 - issues * 6
    return max(0, min(100, score))


def productivity_score() -> int:
    tasks = get_tasks()
    if not tasks:
        return 0
    done = sum(1 for t in tasks if t["status"] == "Done")
    blocked = sum(1 for t in tasks if t["status"] == "Blocked")
    base = done / len(tasks) * 100
    score = base - blocked * 6
    return max(0, min(100, int(round(score))))


def task_completion_rate() -> int:
    tasks = get_tasks()
    if not tasks:
        return 0
    done = sum(1 for t in tasks if t["status"] == "Done")
    return int(round(done / len(tasks) * 100))


def meeting_load_hours() -> float:
    total = 0.0
    for m in get_today_meetings():
        s, e = _safe_dt(m["start"]), _safe_dt(m["end"])
        if s and e:
            total += (e - s).total_seconds() / 3600
    return round(total, 1)


def followup_status() -> dict:
    fu = pending_followups()
    return {"pending": len(fu), "people": [e["sender"] for e in fu]}


def collect_context() -> dict:
    """Single snapshot consumed by the AI brief / insights / assistant."""
    return {
        "today_meetings": get_today_meetings(),
        "important_emails": important_emails(),
        "unread_emails": unread_emails(),
        "pending_followups": pending_followups(),
        "customer_issues": customer_issues(),
        "open_tasks": get_open_tasks(),
        "slack_mentions": slack_mentions(),
        "unanswered_slack": unanswered_slack(),
        "revenue_yesterday": revenue_yesterday(),
        "revenue_7d": revenue_last_n_days(7),
        "mrr": estimated_mrr(),
        "scores": {
            "inbox_health": inbox_health_score(),
            "productivity": productivity_score(),
            "task_completion": task_completion_rate(),
            "meeting_load_hours": meeting_load_hours(),
        },
    }
