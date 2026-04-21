"""
Scheduling Skill
================

Calendar and scheduling operations via external calendar APIs:

- **create_event**       – Create a calendar event (Google Calendar / Outlook)
- **list_events**        – List upcoming events within a date range
- **set_reminder**       – Register a time-based reminder
- **check_availability** – Find free slots across a list of attendees
- **cancel_event**       – Cancel / delete an existing event

Configuration keys (``api_config``)::

    {
        "provider":          "google" | "outlook" | "local",
        "google_token":      "ya29...",        # OAuth2 access token
        "google_calendar_id": "primary",
        "outlook_token":     "eyJ...",
        "outlook_user_id":   "me"
    }

When no provider credentials are configured the skill operates in *local* mode,
storing events in memory so the agent remains usable during development.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from achilles.modules.skills import Skill

logger = logging.getLogger(__name__)

_LOCAL_STORE: List[Dict[str, Any]] = []   # in-process event store for local mode


class SchedulingSkill(Skill):
    """Calendar, reminders, and availability management."""

    name: str = "scheduling"
    description: str = (
        "Create and manage calendar events, set reminders, and check attendee availability."
    )

    def _build_action_map(self) -> Dict[str, Callable]:
        return {
            "create_event": self._create_event,
            "list_events": self._list_events,
            "set_reminder": self._set_reminder,
            "check_availability": self._check_availability,
            "cancel_event": self._cancel_event,
        }

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    async def _create_event(
        self,
        title: str,
        start: str,
        end: str,
        attendees: Optional[List[str]] = None,
        description: str = "",
        location: str = "",
        timezone_id: str = "UTC",
    ) -> Dict[str, Any]:
        """
        Create a calendar event.

        Args:
            title:       Event title / summary.
            start:       ISO-8601 start datetime (e.g. ``"2024-06-01T09:00:00"``).
            end:         ISO-8601 end datetime.
            attendees:   Optional list of attendee email addresses.
            description: Optional event description / agenda.
            location:    Optional location string or conference link.
            timezone_id: IANA timezone id (default ``"UTC"``).

        Returns:
            Created event dict.
        """
        provider = self.api_config.get("provider", "local")
        event = {
            "title": title,
            "start": start,
            "end": end,
            "attendees": attendees or [],
            "description": description,
            "location": location,
            "timezone": timezone_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if provider == "google":
            return await self._google_create_event(event)
        elif provider == "outlook":
            return await self._outlook_create_event(event)
        else:
            return self._local_create_event(event)

    async def _list_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_results: int = 20,
    ) -> Dict[str, Any]:
        """
        List calendar events within a date range.

        Args:
            start_date:  ISO-8601 date/datetime for the lower bound (default: now).
            end_date:    ISO-8601 date/datetime for the upper bound (default: +7 days).
            max_results: Maximum number of events to return.

        Returns:
            Dict with ``events`` list and ``count``.
        """
        now = datetime.now(timezone.utc)
        t_start = start_date or now.isoformat()
        t_end = end_date or (now + timedelta(days=7)).isoformat()

        provider = self.api_config.get("provider", "local")

        if provider == "google":
            return await self._google_list_events(t_start, t_end, max_results)
        elif provider == "outlook":
            return await self._outlook_list_events(t_start, t_end, max_results)
        else:
            return self._local_list_events(t_start, t_end, max_results)

    async def _set_reminder(
        self,
        task: str,
        due_at: str,
        remind_before_minutes: int = 15,
        channel: str = "default",
    ) -> Dict[str, Any]:
        """
        Register a reminder for a task.

        The reminder is stored as a minimal event in the local store with a
        ``reminder`` flag.  A background scheduler (e.g. ``AutomationModule``)
        can poll for due reminders and dispatch them via the CommunicationSkill.

        Args:
            task:                   Description of what to be reminded about.
            due_at:                 ISO-8601 datetime when the reminder fires.
            remind_before_minutes:  Minutes before *due_at* to trigger.
            channel:                Notification channel (forwarded to CommunicationSkill).

        Returns:
            Reminder registration receipt.
        """
        remind_dt = datetime.fromisoformat(due_at) - timedelta(minutes=remind_before_minutes)
        reminder = {
            "type": "reminder",
            "task": task,
            "due_at": due_at,
            "remind_at": remind_dt.isoformat(),
            "channel": channel,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _LOCAL_STORE.append(reminder)
        logger.info("Reminder set: '%s' at %s", task, remind_dt.isoformat())
        return {"skill": "scheduling", "action": "set_reminder", "reminder": reminder}

    async def _check_availability(
        self,
        attendees: List[str],
        duration_minutes: int = 60,
        start_after: Optional[str] = None,
        end_before: Optional[str] = None,
        working_hours_start: int = 9,
        working_hours_end: int = 17,
    ) -> Dict[str, Any]:
        """
        Find the first available slot for all attendees.

        In local mode a heuristic is used (next business-hour slot).
        With a Google/Outlook provider the free-busy API is queried.

        Args:
            attendees:              List of attendee emails.
            duration_minutes:       Required meeting length in minutes.
            start_after:            ISO-8601 lower bound (default: now).
            end_before:             ISO-8601 upper bound (default: +7 days).
            working_hours_start:    Start of working hours (hour, 0-23).
            working_hours_end:      End of working hours (hour, 0-23).

        Returns:
            Dict with suggested ``slot_start`` and ``slot_end``.
        """
        now = datetime.now(timezone.utc)
        t_start = datetime.fromisoformat(start_after) if start_after else now
        t_end = datetime.fromisoformat(end_before) if end_before else now + timedelta(days=7)

        provider = self.api_config.get("provider", "local")
        if provider == "google":
            return await self._google_free_busy(
                attendees, t_start, t_end, duration_minutes
            )
        elif provider == "outlook":
            return await self._outlook_free_busy(
                attendees, t_start, t_end, duration_minutes
            )
        else:
            # Local heuristic: return next working-hour slot
            slot = self._next_working_slot(
                t_start, t_end, duration_minutes, working_hours_start, working_hours_end
            )
            return {
                "skill": "scheduling",
                "action": "check_availability",
                "attendees": attendees,
                "suggested_slot": slot,
            }

    async def _cancel_event(self, event_id: str) -> Dict[str, Any]:
        """
        Cancel / delete an event by ID.

        Args:
            event_id: Provider-specific event identifier, or the ``title`` for
                      local-mode events.

        Returns:
            Cancellation receipt.
        """
        provider = self.api_config.get("provider", "local")
        if provider == "google":
            return await self._google_cancel_event(event_id)
        elif provider == "outlook":
            return await self._outlook_cancel_event(event_id)
        else:
            return self._local_cancel_event(event_id)

    # ------------------------------------------------------------------
    # Local (in-memory) implementations
    # ------------------------------------------------------------------

    def _local_create_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        import uuid

        event["id"] = str(uuid.uuid4())
        event["provider"] = "local"
        _LOCAL_STORE.append(event)
        logger.info("[LOCAL] Event created: %s", event["title"])
        return {"skill": "scheduling", "action": "create_event", "event": event}

    def _local_list_events(
        self, start: str, end: str, max_results: int
    ) -> Dict[str, Any]:
        matching = [
            e for e in _LOCAL_STORE
            if e.get("type") != "reminder" and start <= e.get("start", "") <= end
        ][:max_results]
        return {
            "skill": "scheduling",
            "action": "list_events",
            "events": matching,
            "count": len(matching),
        }

    def _local_cancel_event(self, event_id: str) -> Dict[str, Any]:
        global _LOCAL_STORE
        before = len(_LOCAL_STORE)
        _LOCAL_STORE = [
            e for e in _LOCAL_STORE
            if e.get("id") != event_id and e.get("title") != event_id
        ]
        removed = before - len(_LOCAL_STORE)
        return {
            "skill": "scheduling",
            "action": "cancel_event",
            "removed": removed,
            "event_id": event_id,
        }

    @staticmethod
    def _next_working_slot(
        start: datetime,
        end: datetime,
        duration: int,
        wh_start: int,
        wh_end: int,
    ) -> Dict[str, str]:
        """Find the next open working-hour slot (no real busy check)."""
        candidate = start.replace(minute=0, second=0, microsecond=0)
        if candidate.hour < wh_start:
            candidate = candidate.replace(hour=wh_start)
        elif candidate.hour >= wh_end:
            candidate = (candidate + timedelta(days=1)).replace(hour=wh_start)

        # Skip weekends
        while candidate.weekday() >= 5:
            candidate += timedelta(days=1)

        slot_end = candidate + timedelta(minutes=duration)
        if slot_end.hour > wh_end:
            candidate = (candidate + timedelta(days=1)).replace(hour=wh_start)
            slot_end = candidate + timedelta(minutes=duration)

        return {
            "slot_start": candidate.isoformat(),
            "slot_end": slot_end.isoformat(),
        }

    # ------------------------------------------------------------------
    # Google Calendar API stubs
    # ------------------------------------------------------------------

    async def _google_create_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "scheduling", "action": "create_event", "status": "error",
                    "reason": "aiohttp not installed"}

        import aiohttp

        token = self.api_config.get("google_token", "")
        cal_id = self.api_config.get("google_calendar_id", "primary")
        payload = {
            "summary": event["title"],
            "description": event.get("description", ""),
            "location": event.get("location", ""),
            "start": {"dateTime": event["start"], "timeZone": event.get("timezone", "UTC")},
            "end": {"dateTime": event["end"], "timeZone": event.get("timezone", "UTC")},
            "attendees": [{"email": a} for a in event.get("attendees", [])],
        }
        url = f"https://www.googleapis.com/calendar/v3/calendars/{cal_id}/events"
        async with aiohttp.ClientSession() as s:
            async with s.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            ) as resp:
                data = await resp.json()
                return {"skill": "scheduling", "action": "create_event", "event": data}

    async def _google_list_events(
        self, start: str, end: str, max_results: int
    ) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "scheduling", "action": "list_events", "events": [], "count": 0}

        token = self.api_config.get("google_token", "")
        cal_id = self.api_config.get("google_calendar_id", "primary")
        url = (
            f"https://www.googleapis.com/calendar/v3/calendars/{cal_id}/events"
            f"?timeMin={start}Z&timeMax={end}Z&maxResults={max_results}&singleEvents=true"
            f"&orderBy=startTime"
        )
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers={"Authorization": f"Bearer {token}"}) as resp:
                data = await resp.json()
                items = data.get("items", [])
                return {"skill": "scheduling", "action": "list_events",
                        "events": items, "count": len(items)}

    async def _google_free_busy(
        self, attendees: List[str], start: datetime, end: datetime, duration: int
    ) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "scheduling", "action": "check_availability",
                    "suggested_slot": {}}

        import aiohttp

        token = self.api_config.get("google_token", "")
        payload = {
            "timeMin": start.isoformat() + "Z",
            "timeMax": end.isoformat() + "Z",
            "items": [{"id": a} for a in attendees],
        }
        async with aiohttp.ClientSession() as s:
            async with s.post(
                "https://www.googleapis.com/calendar/v3/freeBusy",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            ) as resp:
                data = await resp.json()
                return {"skill": "scheduling", "action": "check_availability",
                        "free_busy": data}

    async def _google_cancel_event(self, event_id: str) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "scheduling", "action": "cancel_event", "status": "error"}

        token = self.api_config.get("google_token", "")
        cal_id = self.api_config.get("google_calendar_id", "primary")
        url = f"https://www.googleapis.com/calendar/v3/calendars/{cal_id}/events/{event_id}"
        async with aiohttp.ClientSession() as s:
            async with s.delete(url, headers={"Authorization": f"Bearer {token}"}) as resp:
                ok = resp.status == 204
                return {"skill": "scheduling", "action": "cancel_event",
                        "status": "cancelled" if ok else "error",
                        "event_id": event_id}

    # ------------------------------------------------------------------
    # Microsoft Graph / Outlook API stubs
    # ------------------------------------------------------------------

    async def _outlook_create_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "scheduling", "action": "create_event", "status": "error"}

        token = self.api_config.get("outlook_token", "")
        user_id = self.api_config.get("outlook_user_id", "me")
        payload = {
            "subject": event["title"],
            "body": {"contentType": "Text", "content": event.get("description", "")},
            "start": {"dateTime": event["start"], "timeZone": event.get("timezone", "UTC")},
            "end": {"dateTime": event["end"], "timeZone": event.get("timezone", "UTC")},
            "location": {"displayName": event.get("location", "")},
            "attendees": [
                {"emailAddress": {"address": a}, "type": "required"}
                for a in event.get("attendees", [])
            ],
        }
        url = f"https://graph.microsoft.com/v1.0/users/{user_id}/events"
        async with aiohttp.ClientSession() as s:
            async with s.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            ) as resp:
                data = await resp.json()
                return {"skill": "scheduling", "action": "create_event", "event": data}

    async def _outlook_list_events(
        self, start: str, end: str, max_results: int
    ) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "scheduling", "action": "list_events", "events": [], "count": 0}

        token = self.api_config.get("outlook_token", "")
        user_id = self.api_config.get("outlook_user_id", "me")
        url = (
            f"https://graph.microsoft.com/v1.0/users/{user_id}/calendarView"
            f"?startDateTime={start}&endDateTime={end}&$top={max_results}"
        )
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers={"Authorization": f"Bearer {token}"}) as resp:
                data = await resp.json()
                items = data.get("value", [])
                return {"skill": "scheduling", "action": "list_events",
                        "events": items, "count": len(items)}

    async def _outlook_free_busy(
        self, attendees: List[str], start: datetime, end: datetime, duration: int
    ) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "scheduling", "action": "check_availability",
                    "suggested_slot": {}}

        import aiohttp

        token = self.api_config.get("outlook_token", "")
        payload = {
            "schedules": attendees,
            "startTime": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "endTime": {"dateTime": end.isoformat(), "timeZone": "UTC"},
            "availabilityViewInterval": duration,
        }
        async with aiohttp.ClientSession() as s:
            async with s.post(
                "https://graph.microsoft.com/v1.0/me/calendar/getSchedule",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            ) as resp:
                data = await resp.json()
                return {"skill": "scheduling", "action": "check_availability",
                        "schedule": data}

    async def _outlook_cancel_event(self, event_id: str) -> Dict[str, Any]:
        try:
            import aiohttp
        except ImportError:
            return {"skill": "scheduling", "action": "cancel_event", "status": "error"}

        token = self.api_config.get("outlook_token", "")
        user_id = self.api_config.get("outlook_user_id", "me")
        url = f"https://graph.microsoft.com/v1.0/users/{user_id}/events/{event_id}"
        async with aiohttp.ClientSession() as s:
            async with s.delete(url, headers={"Authorization": f"Bearer {token}"}) as resp:
                ok = resp.status == 204
                return {"skill": "scheduling", "action": "cancel_event",
                        "status": "cancelled" if ok else "error",
                        "event_id": event_id}


__all__ = ["SchedulingSkill"]
