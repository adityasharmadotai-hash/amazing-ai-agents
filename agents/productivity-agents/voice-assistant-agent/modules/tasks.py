"""
tasks.py — In-session task, note, reminder, and calendar event management.
All data stored in st.session_state (no DB required, optional Supabase).
"""

from datetime import datetime, timedelta
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


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _id() -> str:
    return str(uuid.uuid4())[:8]


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
# Reminders
# ─────────────────────────────────────────────

def add_reminder(text: str, time_str: str = "") -> dict:
    init_stores()
    item = {
        "id": _id(),
        "reminder": text,
        "time": time_str or "Not set",
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


def get_reminders(active_only: bool = True) -> list:
    init_stores()
    if active_only:
        return [r for r in st.session_state.reminders if r["status"] == "active"]
    return st.session_state.reminders


# ─────────────────────────────────────────────
# Calendar Events
# ─────────────────────────────────────────────

def add_calendar_event(title: str, date: str = "", time: str = "", notes: str = "") -> dict:
    init_stores()
    item = {
        "id": _id(),
        "title": title,
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "time": time or "",
        "notes": notes,
        "created_at": _now(),
    }
    st.session_state.calendar_events.insert(0, item)
    return item


def get_calendar_events() -> list:
    init_stores()
    # Sort by date
    return sorted(st.session_state.calendar_events, key=lambda x: x.get("date", ""))


def delete_calendar_event(event_id: str):
    init_stores()
    st.session_state.calendar_events = [e for e in st.session_state.calendar_events if e["id"] != event_id]


# ─────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────

def get_analytics() -> dict:
    init_stores()
    tasks = st.session_state.tasks
    notes = st.session_state.notes
    reminders = st.session_state.reminders
    events = st.session_state.calendar_events

    pending = sum(1 for t in tasks if t["status"] == "pending")
    done = sum(1 for t in tasks if t["status"] == "done")
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
