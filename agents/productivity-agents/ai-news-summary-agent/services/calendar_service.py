"""Google Calendar API service."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from utils.helpers import retry
from utils.logging_config import get_logger

logger = get_logger(__name__)


class CalendarError(Exception):
    pass


@dataclass
class CalendarEvent:
    id: str
    title: str
    start: Optional[datetime]
    end: Optional[datetime]
    location: str = ""
    description: str = ""
    attendees: list[str] = field(default_factory=list)
    organizer: str = ""
    hangout_link: str = ""

    @property
    def when_str(self) -> str:
        if not self.start:
            return "Unscheduled"
        s = self.start.strftime("%a %d %b, %H:%M")
        e = self.end.strftime("%H:%M") if self.end else ""
        return f"{s}–{e}" if e else s


class CalendarService:
    def __init__(self, credentials: Credentials):
        self._service = build("calendar", "v3", credentials=credentials, cache_discovery=False)

    @staticmethod
    def _parse_dt(node: dict) -> Optional[datetime]:
        if not node:
            return None
        raw = node.get("dateTime") or node.get("date")
        if not raw:
            return None
        try:
            if "T" not in raw:  # all-day date
                return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _parse_event(self, item: dict) -> CalendarEvent:
        attendees = [a.get("email", "") for a in item.get("attendees", []) if a.get("email")]
        return CalendarEvent(
            id=item.get("id", ""),
            title=item.get("summary", "(no title)"),
            start=self._parse_dt(item.get("start", {})),
            end=self._parse_dt(item.get("end", {})),
            location=item.get("location", ""),
            description=item.get("description", ""),
            attendees=attendees,
            organizer=item.get("organizer", {}).get("email", ""),
            hangout_link=item.get("hangoutLink", ""),
        )

    @retry(attempts=3, exceptions=(HttpError,))
    def upcoming_events(self, days_ahead: int = 7, max_results: int = 20) -> list[CalendarEvent]:
        now = datetime.now(timezone.utc)
        time_max = now + timedelta(days=days_ahead)
        try:
            resp = (
                self._service.events()
                .list(
                    calendarId="primary",
                    timeMin=now.isoformat(),
                    timeMax=time_max.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                    maxResults=max_results,
                )
                .execute()
            )
        except HttpError as exc:
            raise CalendarError(f"Failed to list events: {exc}") from exc
        return [self._parse_event(i) for i in resp.get("items", [])]

    def todays_events(self) -> list[CalendarEvent]:
        events = self.upcoming_events(days_ahead=1, max_results=20)
        today = datetime.now(timezone.utc).date()
        return [e for e in events if e.start and e.start.date() == today]
