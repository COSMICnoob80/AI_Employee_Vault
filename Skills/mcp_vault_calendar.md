# MCP Vault Calendar Skill

## Description
MCP server exposing 3 tools for Google Calendar operations via the Model Context Protocol. Uses OAuth2 with a dedicated calendar token separate from Gmail tokens. Supports listing events, creating events, and checking availability. Integrates with vault_audit for audit logging.

## Capabilities
- List upcoming calendar events (configurable lookahead)
- Create calendar events with summary, times, and description
- Check availability for a given date and time window
- Dry-run preview mode for list and create operations
- OAuth2 authentication with automatic token refresh
- Retry with exponential backoff on transient API errors
- Circuit breaker via ErrorTracker

## Input Format
MCP tool calls with parameters:
```
list_events(days_ahead: int = 7, max_results: int = 10, dry_run: bool = False)
create_event(summary: str, start: str, end: str, description: str = "", dry_run: bool = False)
check_availability(date: str, start_time: str = "09:00", end_time: str = "17:00")
```

Datetime values use ISO 8601 format (e.g. `2026-03-10T09:00:00+05:00`).
Date values use `YYYY-MM-DD` format.

## Output Format
All tools return a single string:
- **Success**: Operation result with event details
- **Dry run**: Formatted preview block showing what would happen
- **Validation error**: `Error: <description>`
- **Auth error**: `Error: Credentials file not found...`

## Rules
1. No `delete_event` in v1 — limits blast radius of accidental deletions
2. Event creation should follow [[Company_Handbook]] thresholds — use dry-run first
3. Summary must be non-empty; end time must be after start time
4. Uses separate token file (`.calendar_token.json`) — does not affect Gmail tokens
5. OAuth port 8093 (avoids Gmail ports 8090-8092)
6. First run requires browser-based OAuth consent and Calendar API enabled in Google Cloud Console
7. API calls use retry decorator (2 retries) with exponential backoff

## Examples

### Example 1: List Events
```
list_events(days_ahead=3)
-> "Upcoming events (next 3 days):\n  - 2026-03-08T10:00:00+05:00: Team Standup\n  - 2026-03-09T14:00:00+05:00: Client Call"
```

### Example 2: Create Event (Dry Run)
```
create_event(summary="Sprint Review", start="2026-03-10T15:00:00+05:00", end="2026-03-10T16:00:00+05:00", dry_run=True)
-> "--- DRY RUN PREVIEW ---\nWould create event:\n  Summary: Sprint Review\n  Start:   2026-03-10T15:00:00+05:00\n  End:     2026-03-10T16:00:00+05:00\n..."
```

### Example 3: Create Event
```
create_event(summary="Sprint Review", start="2026-03-10T15:00:00+05:00", end="2026-03-10T16:00:00+05:00", description="Review sprint deliverables")
-> "Event created: Sprint Review\nEvent ID: abc123def\nLink: https://calendar.google.com/..."
```

### Example 4: Check Availability
```
check_availability(date="2026-03-10", start_time="09:00", end_time="17:00")
-> "Availability on 2026-03-10 (09:00-17:00):\n\nBusy slots (2):\n  - 10:00 to 11:00: Team Standup\n  - 14:00 to 15:00: 1:1 with Manager"
```

## Integration
- Audit logging: `Watchers/vault_audit.py` (`audit_log`, `ErrorTracker`, `retry`)
- Approval workflow: [[Company_Handbook]] (event creation may need approval)
- System status: [[Dashboard]]
- CEO Briefing: `Scripts/ceo_briefing.py` (can reference calendar data)
