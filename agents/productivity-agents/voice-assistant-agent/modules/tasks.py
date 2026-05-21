"""
tasks.py — Task, note, reminder, and calendar management.
Uses st.session_state for storage + a background thread scheduler
for real-time reminder/event alerts that fire at the correct time.
"""

from datetime import datetime, timedelta
import re
import threading
import time as _time
import streamlit as st
import uuid


# ─────────────────────────────────────────────
# Session store initialisation
# ─────────────────────────────────────────────

def init_stores():
    defaults = {
        "tasks": [],
        "notes": [],
        "reminders": [],
        "calendar_events": [],
        "fired_alerts": [],       # list of alert dicts ready to show
        "user_tz_offset": None,   # minutes from UTC, set by browser JS
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _id() -> str:
    return str(uuid.uuid4())[:8]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ─────────────────────────────────────────────
# Timezone-aware local time
# ─────────────────────────────────────────────

def local_now() -> datetime:
    """Current time in user's local timezone using browser-reported offset."""
    try:
        offset = st.session_state.get("user_tz_offset")
        if isinstance(offset, (int, float)):
            return datetime.utcnow() + timedelta(minutes=int(offset))
    except Exception:
        pass
    return datetime.now()


# ─────────────────────────────────────────────
# Time parsing
# ─────────────────────────────────────────────

def _parse_time(time_str: str) -> datetime | None:
    """
    Parse natural language → datetime in local time.
    Strips timezone labels (IST, EST, UTC etc.) before parsing.
    """
    if not time_str or time_str.strip().lower() in ("not set", "tbd", ""):
        return None

    s = time_str.strip().lower()

    # Strip timezone labels
    s = re.sub(r'\([a-z]{2,5}[+-]?\d*:?\d*\)', '', s)
    s = re.sub(r'\b(ist|utc|gmt|est|pst|cst|mst|cet|jst|aest|nzst|bst|eet)\b', '', s)
    s = re.sub(r'[+-]\d{1,2}:\d{2}', '', s)
    s = re.sub(r'\bat\b', '', s)
    s = re.sub(r'\s+', ' ', s).strip()

    now = local_now()
    base = now.replace(second=0, microsecond=0)

    # "in X minutes/hours"
    m = re.search(r'in\s+(\d+)\s*(min|minute|minutes|hour|hours|hr)', s)
    if m:
        val = int(m.group(1))
        unit = m.group(2)
        delta = timedelta(hours=val) if 'hour' in unit or unit == 'hr' else timedelta(minutes=val)
        return base + delta

    day_offset = 0
    if 'tomorrow' in s:
        day_offset = 1
        s = s.replace('tomorrow', '').strip()
    elif 'today' in s:
        s = s.replace('today', '').strip()

    for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            pass

    m = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', s)
    if m:
        hour   = int(m.group(1))
        minute = int(m.group(2) or 0)
        ampm   = m.group(3)
        if ampm == 'pm' and hour < 12:
            hour += 12
        elif ampm == 'am' and hour == 12:
            hour = 0
        if ampm is None and 1 <= hour <= 12:
            cam = (base + timedelta(days=day_offset)).replace(hour=hour, minute=minute, second=0, microsecond=0)
            cpm_h = hour + 12 if hour < 12 else hour
            try:
                cpm = (base + timedelta(days=day_offset)).replace(hour=cpm_h, minute=minute, second=0, microsecond=0)
                if cam < base and cpm >= base:
                    hour = cpm_h
            except ValueError:
                pass
        try:
            return (base + timedelta(days=day_offset)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            pass

    return None


# ─────────────────────────────────────────────
# Background scheduler — fires alerts in real time
# ─────────────────────────────────────────────

# Global dict: session_id → list of pending jobs
# Each job: {"id": str, "type": "reminder"|"event", "due_dt": datetime, "label": str, "fired": bool}
_PENDING_JOBS: dict[str, list] = {}
_SCHEDULER_STARTED = False
_LOCK = threading.Lock()


def _scheduler_loop():
    """Background thread: checks every 15 seconds if any job is due."""
    while True:
        _time.sleep(15)
        now_utc = datetime.utcnow()
        with _LOCK:
            for session_id, jobs in list(_PENDING_JOBS.items()):
                for job in jobs:
                    if job.get("fired"):
                        continue
                    due = job.get("due_dt")
                    if due and now_utc >= due:
                        job["fired"] = True
                        # Write to a shared fired list that the UI reads
                        if session_id not in _FIRED_ALERTS:
                            _FIRED_ALERTS[session_id] = []
                        _FIRED_ALERTS[session_id].append({
                            "type": job["type"],
                            "label": job["label"],
                            "job_id": job["id"],
                        })


_FIRED_ALERTS: dict[str, list] = {}


def _start_scheduler():
    global _SCHEDULER_STARTED
    if not _SCHEDULER_STARTED:
        t = threading.Thread(target=_scheduler_loop, daemon=True)
        t.start()
        _SCHEDULER_STARTED = True


def _schedule_job(session_id: str, job_id: str, job_type: str,
                  label: str, due_local: datetime, tz_offset: int | None):
    """Convert local due time → UTC and register with the background scheduler."""
    _start_scheduler()
    # Convert local time to UTC for the scheduler (which uses UTC)
    offset_mins = tz_offset if isinstance(tz_offset, (int, float)) else 0
    due_utc = due_local - timedelta(minutes=int(offset_mins))

    with _LOCK:
        if session_id not in _PENDING_JOBS:
            _PENDING_JOBS[session_id] = []
        # Remove any existing job with same id
        _PENDING_JOBS[session_id] = [j for j in _PENDING_JOBS[session_id] if j["id"] != job_id]
        _PENDING_JOBS[session_id].append({
            "id": job_id,
            "type": job_type,
            "label": label,
            "due_dt": due_utc,
            "fired": False,
        })


def get_session_id() -> str:
    """Get or create a unique ID for this browser session."""
    if "_session_uid" not in st.session_state:
        st.session_state["_session_uid"] = str(uuid.uuid4())[:12]
    return st.session_state["_session_uid"]


def poll_fired_alerts() -> list:
    """
    Call this on every Streamlit rerun to collect any alerts the
    background thread has fired. Clears them after reading.
    """
    sid = get_session_id()
    with _LOCK:
        alerts = _FIRED_ALERTS.pop(sid, [])
    return alerts


def snooze_job(session_id: str, job_id: str, minutes: int = 10):
    """Push a job's due time forward by `minutes`."""
    with _LOCK:
        for job in _PENDING_JOBS.get(session_id, []):
            if job["id"] == job_id:
                job["due_dt"] = datetime.utcnow() + timedelta(minutes=minutes)
                job["fired"] = False
                break


def cancel_job(session_id: str, job_id: str):
    with _LOCK:
        if session_id in _PENDING_JOBS:
            _PENDING_JOBS[session_id] = [
                j for j in _PENDING_JOBS[session_id] if j["id"] != job_id
            ]


# ─────────────────────────────────────────────
# Tasks
# ─────────────────────────────────────────────

def add_task(task: str, deadline: str = "", priority: str = "Medium") -> dict:
    init_stores()
    item = {
        "id": _id(), "task": task, "deadline": deadline or "",
        "priority": priority, "status": "pending",
        "created_at": _now(), "completed_at": None,
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
        "content": content, "tag": tag, "created_at": _now(),
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
# Reminders — with real background scheduling
# ─────────────────────────────────────────────

def add_reminder(text: str, time_str: str = "") -> dict:
    init_stores()
    due_dt = _parse_time(time_str)
    rid = _id()
    item = {
        "id": rid,
        "reminder": text,
        "time": time_str or "Not set",
        "due_dt": due_dt.strftime("%Y-%m-%d %H:%M") if due_dt else None,
        "status": "active",
        "created_at": _now(),
    }
    st.session_state.reminders.insert(0, item)

    # Schedule background alert if time is set
    if due_dt:
        tz_offset = st.session_state.get("user_tz_offset")
        _schedule_job(
            session_id=get_session_id(),
            job_id=rid,
            job_type="reminder",
            label=f"🔔 {text}",
            due_local=due_dt,
            tz_offset=tz_offset,
        )

    return item


def dismiss_reminder(reminder_id: str):
    init_stores()
    for r in st.session_state.reminders:
        if r["id"] == reminder_id:
            r["status"] = "dismissed"
    cancel_job(get_session_id(), reminder_id)


def get_reminders(active_only: bool = True) -> list:
    init_stores()
    if active_only:
        return [r for r in st.session_state.reminders if r["status"] == "active"]
    return st.session_state.reminders


def get_reminder_status(r: dict) -> str:
    due_str = r.get("due_dt")
    if not due_str:
        return "no-time"
    try:
        due_dt = datetime.strptime(due_str, "%Y-%m-%d %H:%M")
        now = local_now()
        diff = (due_dt - now).total_seconds() / 60
        if diff < -30:  return "overdue"
        if diff < 0:    return "due-soon"
        if diff <= 15:  return "due-soon"
        return "upcoming"
    except ValueError:
        return "no-time"


# ─────────────────────────────────────────────
# Calendar Events — with real background scheduling
# ─────────────────────────────────────────────

def add_calendar_event(title: str, date: str = "", time: str = "", notes: str = "") -> dict:
    init_stores()
    date_str = date or datetime.now().strftime("%Y-%m-%d")
    due_dt = None
    if time:
        due_dt = _parse_time(f"{date_str} {time}") or _parse_time(time)
    if due_dt is None and date_str:
        try:
            due_dt = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=9, minute=0)
        except ValueError:
            pass

    eid = _id()
    item = {
        "id": eid, "title": title,
        "date": date_str, "time": time or "", "notes": notes,
        "due_dt": due_dt.strftime("%Y-%m-%d %H:%M") if due_dt else None,
        "status": "active", "created_at": _now(),
    }
    st.session_state.calendar_events.insert(0, item)

    # Schedule alert 15 min before event (or at event time if < 15 min away)
    if due_dt:
        alert_time = due_dt - timedelta(minutes=15)
        if alert_time < local_now():
            alert_time = due_dt  # alert at event time if < 15 min away
        tz_offset = st.session_state.get("user_tz_offset")
        _schedule_job(
            session_id=get_session_id(),
            job_id=eid,
            job_type="event",
            label=f"📅 {title} — {date_str} {time}".strip(),
            due_local=alert_time,
            tz_offset=tz_offset,
        )

    return item


def get_calendar_events() -> list:
    init_stores()
    return sorted(st.session_state.calendar_events, key=lambda x: x.get("date", ""))


def delete_calendar_event(event_id: str):
    init_stores()
    st.session_state.calendar_events = [
        e for e in st.session_state.calendar_events if e["id"] != event_id
    ]
    cancel_job(get_session_id(), event_id)


def get_event_status(e: dict) -> str:
    due_str = e.get("due_dt")
    today = local_now().strftime("%Y-%m-%d")
    event_date = e.get("date", "")
    if not due_str:
        if event_date == today: return "today"
        if event_date and event_date < today: return "past"
        return "upcoming"
    try:
        due_dt = datetime.strptime(due_str, "%Y-%m-%d %H:%M")
        now = local_now()
        diff = (due_dt - now).total_seconds() / 60
        if diff < -60:   return "past"
        if diff < 0:     return "starting-now"
        if diff <= 15:   return "soon"
        if event_date == today: return "today"
        return "upcoming"
    except ValueError:
        return "upcoming"


# ─────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────

def get_analytics() -> dict:
    init_stores()
    tasks     = st.session_state.tasks
    notes     = st.session_state.notes
    reminders = st.session_state.reminders
    events    = st.session_state.calendar_events

    pending = sum(1 for t in tasks if t["status"] == "pending")
    done    = sum(1 for t in tasks if t["status"] == "done")
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
