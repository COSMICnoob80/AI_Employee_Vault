#!/usr/bin/env python3
"""
MCP Google Calendar Server for AI Employee Vault

Exposes 3 tools for calendar operations via the Model Context Protocol.
Uses Google Calendar API with OAuth2 and a dedicated token file.
Integrates with vault_audit for audit logging.

Transport: stdio (standard for Claude Code)

Dependencies:
    pip install mcp google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""

import socket
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Force IPv4 — httplib2 fails on IPv6-only DNS resolution
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_getaddrinfo(*args, **kwargs):
    results = _orig_getaddrinfo(*args, **kwargs)
    ipv4 = [r for r in results if r[0] == socket.AF_INET]
    return ipv4 if ipv4 else results
socket.getaddrinfo = _ipv4_getaddrinfo

# Allow importing vault_audit from Watchers/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Watchers"))

from mcp.server.fastmcp import FastMCP
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import httplib2
from google_auth_httplib2 import AuthorizedHttp

from vault_audit import audit_log, ErrorTracker, retry

# Configuration
VAULT_ROOT = Path.home() / "AI_Employee_Vault"
CREDENTIALS_FILE = VAULT_ROOT / "credentials.json"
TOKEN_FILE = VAULT_ROOT / ".calendar_token.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
OAUTH_PORT = 8093

mcp = FastMCP("vault-calendar")
error_tracker = ErrorTracker("vault_calendar_server")


def get_calendar_service():
    """Authenticate with Google Calendar API using OAuth2."""
    creds = None

    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"Credentials file not found: {CREDENTIALS_FILE}. "
                    "Download from Google Cloud Console and enable the Calendar API."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(
                port=OAUTH_PORT,
                open_browser=True,
                access_type="offline",
                prompt="consent",
            )

        TOKEN_FILE.write_text(creds.to_json())

    authed_http = AuthorizedHttp(creds, http=httplib2.Http(timeout=30))
    return build("calendar", "v3", http=authed_http, cache_discovery=False)


@retry(max_retries=2, retryable=(ConnectionError, TimeoutError, OSError))
def _list_events_api(service, time_min, time_max, max_results):
    """Fetch events from Calendar API with retry."""
    return (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )


@retry(max_retries=2, retryable=(ConnectionError, TimeoutError, OSError))
def _insert_event_api(service, body):
    """Insert an event via Calendar API with retry."""
    return service.events().insert(calendarId="primary", body=body).execute()


@mcp.tool()
def list_events(days_ahead: int = 7, max_results: int = 10, dry_run: bool = False) -> str:
    """List upcoming calendar events.

    Args:
        days_ahead: Number of days to look ahead (default 7).
        max_results: Maximum events to return (default 10).
        dry_run: If True, returns the query parameters without calling the API.

    Returns:
        Formatted event list, preview, or error description.
    """
    now = datetime.now(timezone.utc)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()

    if dry_run:
        return (
            f"--- DRY RUN PREVIEW ---\n"
            f"Would list events from: {time_min}\n"
            f"                    to: {time_max}\n"
            f"Max results: {max_results}\n"
            f"--- END PREVIEW (no API call made) ---"
        )

    try:
        error_tracker.check()
        service = get_calendar_service()
        result = _list_events_api(service, time_min, time_max, max_results)
        events = result.get("items", [])

        audit_log("calendar_list_events", "vault_calendar_server", {
            "days_ahead": days_ahead,
            "events_found": len(events),
        })

        if not events:
            return f"No events found in the next {days_ahead} days."

        lines = [f"Upcoming events (next {days_ahead} days):"]
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            summary = event.get("summary", "(No title)")
            lines.append(f"  - {start}: {summary}")
        return "\n".join(lines)
    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error listing events: {e}"


@mcp.tool()
def create_event(
    summary: str,
    start: str,
    end: str,
    description: str = "",
    dry_run: bool = False,
) -> str:
    """Create a calendar event.

    Args:
        summary: Event title (non-empty).
        start: Start time in ISO 8601 format (e.g. "2026-03-10T09:00:00+05:00").
        end: End time in ISO 8601 format (must be after start).
        description: Optional event description.
        dry_run: If True, returns a preview without creating.

    Returns:
        Success message with event link, preview, or error description.
    """
    if not summary or not summary.strip():
        return "Error: Event summary cannot be empty."
    if not start or not end:
        return "Error: Start and end times are required (ISO 8601 format)."

    # Validate that end > start
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        if end_dt <= start_dt:
            return "Error: End time must be after start time."
    except ValueError as e:
        return f"Error: Invalid datetime format: {e}. Use ISO 8601 (e.g. 2026-03-10T09:00:00+05:00)."

    if dry_run:
        return (
            f"--- DRY RUN PREVIEW ---\n"
            f"Would create event:\n"
            f"  Summary: {summary}\n"
            f"  Start:   {start}\n"
            f"  End:     {end}\n"
            f"  Description: {description or '(none)'}\n"
            f"--- END PREVIEW (not created) ---"
        )

    try:
        error_tracker.check()
        service = get_calendar_service()
        event_body = {
            "summary": summary,
            "start": {"dateTime": start},
            "end": {"dateTime": end},
        }
        if description:
            event_body["description"] = description

        created = _insert_event_api(service, event_body)

        audit_log("calendar_create_event", "vault_calendar_server", {
            "summary": summary,
            "start": start,
            "end": end,
            "event_id": created.get("id", ""),
        })

        link = created.get("htmlLink", "")
        return f"Event created: {summary}\nEvent ID: {created['id']}\nLink: {link}"
    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error creating event: {e}"


@mcp.tool()
def check_availability(
    date: str,
    start_time: str = "09:00",
    end_time: str = "17:00",
) -> str:
    """Check calendar availability for a given date and time range.

    Args:
        date: Date to check (YYYY-MM-DD format).
        start_time: Start of window (HH:MM, default "09:00").
        end_time: End of window (HH:MM, default "17:00").

    Returns:
        Availability summary showing busy and free slots.
    """
    try:
        check_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return f"Error: Invalid date format '{date}'. Use YYYY-MM-DD."

    try:
        start_h, start_m = map(int, start_time.split(":"))
        end_h, end_m = map(int, end_time.split(":"))
    except ValueError:
        return f"Error: Invalid time format. Use HH:MM."

    # Build timezone-aware range using local timezone
    from datetime import timezone as tz
    local_tz = datetime.now().astimezone().tzinfo
    range_start = datetime(check_date.year, check_date.month, check_date.day,
                           start_h, start_m, tzinfo=local_tz)
    range_end = datetime(check_date.year, check_date.month, check_date.day,
                         end_h, end_m, tzinfo=local_tz)

    if range_end <= range_start:
        return "Error: End time must be after start time."

    try:
        error_tracker.check()
        service = get_calendar_service()
        result = _list_events_api(
            service,
            range_start.isoformat(),
            range_end.isoformat(),
            50,
        )
        events = result.get("items", [])

        audit_log("calendar_check_availability", "vault_calendar_server", {
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "events_found": len(events),
        })

        if not events:
            return f"Fully available on {date} from {start_time} to {end_time}. No events scheduled."

        lines = [f"Availability on {date} ({start_time}-{end_time}):"]
        lines.append(f"\nBusy slots ({len(events)}):")
        for event in events:
            evt_start = event["start"].get("dateTime", event["start"].get("date"))
            evt_end = event["end"].get("dateTime", event["end"].get("date"))
            summary = event.get("summary", "(No title)")
            lines.append(f"  - {evt_start} to {evt_end}: {summary}")

        return "\n".join(lines)
    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error checking availability: {e}"


if __name__ == "__main__":
    mcp.run()
