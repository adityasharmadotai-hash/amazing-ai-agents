"""
tasks.py — In-session task, note, reminder, and calendar event management.
All data stored in st.session_state (no DB required, optional Supabase).

REMINDER SYSTEM:
- Reminders store a parsed datetime (due_dt) when possible
- check_due_reminders() scans for overdue/due reminders on every page load
- Returns list of reminders that are due now for the alert banner
"""

from datetime import datetime, timedelta
import re
import streamlit as st
import uuid


# ─────────────────────────────────────────────
# Initialise session stores
# ─────────────────────────────────────────────

def init_stores():
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    if "notes" not in st.session_state:
        st.session_state.notes = []
    if "reminders" not in st.session_state:
        st.session_state.reminders = []
    if "calendar_events" not in st.session_state:
        st.session_state.calendar_events = []
    if "dismissed_alert_ids" not in st.session_state:
        st.session_state.dismissed_alert_ids = set()
    if "user_tz_offset" not in st.session_state:
        st.session_state.user_tz_offset = None  # minutes offset from UTC


# ─────────────────────────────────────────────
# Local time — uses browser-reported offset when available
# ─────────────────────────────────────────────

def local_now() -> datetime:
    """
    Return current datetime in the USER'S local timezone.
    Uses browser-reported UTC offset stored in session state.
    Falls back to server time if offset not yet captured.
    """
    utc_now = datetime.utcnow()
    offset = st.session_state.get("user_tz_offset")
    if offset is not None:
        return utc_now + timedelta(minutes=offset)
    return local_now()  # fallback: server local time


def _now() -> str:
    return local_now().strftime("%Y-%m-%d %H:%M")

def _id() -> str:
    return str(uuid.uuid4())[:8]


# ─────────────────────────────────────────────
# Time parsing — convert natural language to datetime
# ─────────────────────────────────────────────

def _parse_time(time_str: str) -> datetime | None:
    """
    Parse natural language time strings into datetime objects.
    Always uses local_now() as base so comparisons are in the user's timezone.

    Supported formats:
      "3:05 PM"             → today at 15:05
      "8:15 PM (IST)"       → today at 20:15  ← strips timezone labels
      "8:15 PM IST"         → today at 20:15
      "9 AM"                → today at 09:00
      "tomorrow 2 PM"       → tomorrow at 14:00
      "today at 3 PM"       → today at 15:00
      "2025-06-01 10:00"    → exact date+time
      "in 5 minutes"        → now + 5 min
      "in 1 hour"           → now + 60 min
    Returns None if unparseable.
    """
    if not time_str or time_str.strip().lower() in ("not set", "tbd", ""):
        return None

    s = time_str.strip().lower()

    # ── Strip timezone labels: (IST), IST, (UTC), UTC+5:30, EST, PST etc. ──
    # Remove parenthesized timezone: "(IST)", "(UTC+5:30)", "(EST)"
    s = re.sub(r'\([a-z]{2,5}[+-]?\d*:?\d*\)', '', s)
    # Remove bare 2-5 letter timezone abbreviations at word boundary
    s = re.sub(r'\b(ist|utc|gmt|est|pst|cst|mst|cet|jst|aest|nzst|bst|eet)\b', '', s)
    # Remove UTC offset like +05:30, -08:00
    s = re.sub(r'[+-]\d{1,2}:\d{2}', '', s)
    # Strip "at" as connector: "today at 3 PM" → "today 3 PM"
    s = re.sub(r'\bat\b', '', s)
    s = re.sub(r'\s+', ' ', s).strip()

    now = local_now()
    base = now.replace(second=0, microsecond=0)

    # ── "in X minutes/hours" ──
    m = re.search(r'in\s+(\d+)\s*(min|minute|minutes|hour|hours|hr)', s)
    if m:
        val = int(m.group(1))
        unit = m.group(2)
        if 'hour' in unit or unit == 'hr':
            return base + timedelta(hours=val)
        return base + timedelta(minutes=val)

    # ── Day modifiers ──
    day_offset = 0
    if 'tomorrow' in s:
        day_offset = 1
        s = s.replace('tomorrow', '').strip()
    elif 'today' in s:
        s = s.replace('today', '').strip()

    s = s.strip()

    # ── ISO format: "2025-06-01 10:00" or "2025-06-01" ──
    for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            pass

    # ── "H:MM AM/PM" or "H AM/PM" or "HH:MM" (24h) ──
    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', s)
    if time_match:
        hour   = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        ampm   = time_match.group(3)

        if ampm == 'pm' and hour < 12:
            hour += 12
        elif ampm == 'am' and hour == 12:
            hour = 0

        # If no am/pm given and hour looks like 12h (<=12), default to PM
        # only if the hour has already passed today (smart guess)
        if ampm is None and 1 <= hour <= 12:
            candidate_am = (base + timedelta(days=day_offset)).replace(
                hour=hour, minute=minute, second=0, microsecond=0)
            candidate_pm = (base + timedelta(days=day_offset)).replace(
                hour=hour + 12 if hour < 12 else hour,
                minute=minute, second=0, microsecond=0)
            # Pick PM if AM has already passed and PM hasn't
            if candidate_am < base and candidate_pm >= base:
                hour = hour + 12 if hour < 12 else hour

        try:
            target = (base + timedelta(days=day_offset)).replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            return target
        except ValueError:
            pass

    return None



# ─────────────────────────────────────────────
# Tasks
# ─────────────────────────────────────────────

def add_task(task: str, deadline: str = "", priority: str = "Medium") -> dict:
    init_stores()
    item = {
        "id": _id(),
        "task": task,
        "deadline": deadline or "",
        "priority": priority,
        "status": "pending",
        "created_at": _now(),
        "completed_at": None,
    }
    st.session_state.tasks.insert(0, item)
    return item


def complete_task(task_id: str) -> bool:
    init_stores()
    for t in st.session_state.tasks:
        if t["id"] == task_id:
            t["status"] = "done"
            t["completed_at"] = _now()
            return True
    return False


def delete_task(task_id: str):
    init_stores()
    st.session_state.tasks = [t for t in st.session_state.tasks if t["id"] != task_id]


def get_tasks(status: str = "all") -> list:
    init_stores()
    if status == "pending":
        return [t for t in st.session_state.tasks if t["status"] == "pending"]
    if status == "done":
        return [t for t in st.session_state.tasks if t["status"] == "done"]
    return st.session_state.tasks


# ─────────────────────────────────────────────
# Notes
# ─────────────────────────────────────────────

def add_note(title: str, content: str, tag: str = "General") -> dict:
    init_stores()
    item = {
        "id": _id(),
        "title": title or f"Note {len(st.session_state.notes) + 1}",
        "content": content,
        "tag": tag,
        "created_at": _now(),
    }
    st.session_state.notes.insert(0, item)
    return item


def delete_note(note_id: str):
    init_stores()
    st.session_state.notes = [n for n in st.session_state.notes if n["id"] != note_id]


def get_notes() -> list:
    init_stores()
    return st.session_state.notes


# ─────────────────────────────────────────────
# Reminders — with time parsing
# ─────────────────────────────────────────────

def add_reminder(text: str, time_str: str = "") -> dict:
    init_stores()
    due_dt = _parse_time(time_str)
    item = {
        "id": _id(),
        "reminder": text,
        "time": time_str or "Not set",
        "due_dt": due_dt.strftime("%Y-%m-%d %H:%M") if due_dt else None,
        "status": "active",
        "created_at": _now(),
    }
    st.session_state.reminders.insert(0, item)
    return item


def dismiss_reminder(reminder_id: str):
    init_stores()
    for r in st.session_state.reminders:
        if r["id"] == reminder_id:
            r["status"] = "dismissed"
    # Also remove from alert tracking
    if "dismissed_alert_ids" not in st.session_state:
        st.session_state.dismissed_alert_ids = set()
    st.session_state.dismissed_alert_ids.add(reminder_id)


def dismiss_alert(reminder_id: str):
    """Dismiss just the alert banner without fully dismissing the reminder."""
    if "dismissed_alert_ids" not in st.session_state:
        st.session_state.dismissed_alert_ids = set()
    st.session_state.dismissed_alert_ids.add(reminder_id)


def get_reminders(active_only: bool = True) -> list:
    init_stores()
    if active_only:
        return [r for r in st.session_state.reminders if r["status"] == "active"]
    return st.session_state.reminders


def check_due_reminders() -> list:
    """
    Returns list of reminders that are due now (within the last 30 minutes)
    and have not been alert-dismissed.
    Called on every page load.
    """
    init_stores()
    now = local_now().replace(second=0, microsecond=0)
    window_start = now - timedelta(minutes=30)
    dismissed = st.session_state.get("dismissed_alert_ids", set())
    due = []

    for r in st.session_state.reminders:
        if r["status"] != "active":
            continue
        if r["id"] in dismissed:
            continue
        due_str = r.get("due_dt")
        if not due_str:
            continue
        try:
            due_dt = datetime.strptime(due_str, "%Y-%m-%d %H:%M")
            if window_start <= due_dt <= now:
                due.append(r)
        except ValueError:
            continue

    return due


def get_reminder_status(r: dict) -> str:
    """Return 'overdue', 'due-soon', 'upcoming', or 'no-time' for display."""
    due_str = r.get("due_dt")
    if not due_str:
        return "no-time"
    try:
        due_dt = datetime.strptime(due_str, "%Y-%m-%d %H:%M")
        now = local_now()
        diff = (due_dt - now).total_seconds() / 60   # minutes
        if diff < -30:
            return "overdue"
        if diff < 0:
            return "due-soon"
        if diff <= 15:
            return "due-soon"
        return "upcoming"
    except ValueError:
        return "no-time"


# ─────────────────────────────────────────────
# Calendar Events
# ─────────────────────────────────────────────

def add_calendar_event(title: str, date: str = "", time: str = "", notes: str = "") -> dict:
    init_stores()
    # Build a due_dt for alert checking
    date_str = date or datetime.now().strftime("%Y-%m-%d")
    due_dt = None
    if time:
        combined = f"{date_str} {time}"
        due_dt = _parse_time(combined) or _parse_time(time)
    if due_dt is None and date_str:
        try:
            due_dt = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=0, minute=0)
        except ValueError:
            pass

    item = {
        "id": _id(),
        "title": title,
        "date": date_str,
        "time": time or "",
        "notes": notes,
        "due_dt": due_dt.strftime("%Y-%m-%d %H:%M") if due_dt else None,
        "status": "active",
        "created_at": _now(),
    }
    st.session_state.calendar_events.insert(0, item)
    return item


def get_calendar_events() -> list:
    init_stores()
    return sorted(st.session_state.calendar_events, key=lambda x: x.get("date", ""))


def delete_calendar_event(event_id: str):
    init_stores()
    st.session_state.calendar_events = [e for e in st.session_state.calendar_events if e["id"] != event_id]


def dismiss_event_alert(event_id: str):
    """Dismiss just the alert for a calendar event."""
    if "dismissed_alert_ids" not in st.session_state:
        st.session_state.dismissed_alert_ids = set()
    st.session_state.dismissed_alert_ids.add(f"evt_{event_id}")


def check_due_events() -> list:
    """
    Returns calendar events starting within the next 15 minutes or
    that started within the last 30 minutes (and alert not dismissed).
    Called on every page load alongside check_due_reminders().
    """
    init_stores()
    now = local_now().replace(second=0, microsecond=0)
    window_start = now - timedelta(minutes=30)   # already started (late alert)
    window_end   = now + timedelta(minutes=15)    # starting very soon
    dismissed = st.session_state.get("dismissed_alert_ids", set())
    due = []

    for e in st.session_state.calendar_events:
        if e.get("status") == "dismissed":
            continue
        alert_key = f"evt_{e['id']}"
        if alert_key in dismissed:
            continue
        due_str = e.get("due_dt")
        if not due_str:
            continue
        try:
            due_dt = datetime.strptime(due_str, "%Y-%m-%d %H:%M")
            if window_start <= due_dt <= window_end:
                due.append(e)
        except ValueError:
            continue

    return due


def get_event_status(e: dict) -> str:
    """Return 'starting-now', 'soon', 'today', 'upcoming', or 'past'."""
    due_str = e.get("due_dt")
    today = datetime.now().strftime("%Y-%m-%d")
    event_date = e.get("date", "")

    if not due_str:
        if event_date == today:
            return "today"
        if event_date and event_date < today:
            return "past"
        return "upcoming"

    try:
        due_dt = datetime.strptime(due_str, "%Y-%m-%d %H:%M")
        now = local_now()
        diff_mins = (due_dt - now).total_seconds() / 60
        if diff_mins < -30:
            return "past"
        if diff_mins < 0:
            return "starting-now"
        if diff_mins <= 15:
            return "soon"
        if event_date == today:
            return "today"
        return "upcoming"
    except ValueError:
        return "upcoming"


# ─────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────

def get_analytics() -> dict:
    init_stores()
    tasks    = st.session_state.tasks
    notes    = st.session_state.notes
    reminders= st.session_state.reminders
    events   = st.session_state.calendar_events

    pending  = sum(1 for t in tasks if t["status"] == "pending")
    done     = sum(1 for t in tasks if t["status"] == "done")
    completion_rate = round(done / len(tasks) * 100, 1) if tasks else 0

    priority_counts = {"High": 0, "Medium": 0, "Low": 0}
    for t in tasks:
        p = t.get("priority", "Medium")
        priority_counts[p] = priority_counts.get(p, 0) + 1

    return {
        "total_tasks": len(tasks),
        "pending_tasks": pending,
        "done_tasks": done,
        "completion_rate": completion_rate,
        "total_notes": len(notes),
        "total_reminders": len(reminders),
        "active_reminders": sum(1 for r in reminders if r["status"] == "active"),
        "total_events": len(events),
        "priority_counts": priority_counts,
    }
