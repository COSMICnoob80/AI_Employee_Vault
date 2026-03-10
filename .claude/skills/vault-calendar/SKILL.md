# MCP Vault Calendar

Google Calendar operations via MCP tools for the AI Employee system.

## Triggers
- "check my calendar"
- "list events"
- "create calendar event"
- "schedule meeting"
- "check availability"

## Instructions

When the user asks about calendar operations:

1. **List events** - Use `list_events` to show upcoming events. Default is 7 days ahead, up to 10 events. Use `dry_run=True` to preview the query without calling the API.

2. **Create events** - Use `create_event` with summary, start/end times (ISO 8601), and optional description. Always use `dry_run=True` first to preview, then confirm with the user before creating.

3. **Check availability** - Use `check_availability` with a date (YYYY-MM-DD) and optional time window (default 09:00-17:00) to see busy/free slots.

## Notes
- First run requires OAuth consent — user will be prompted to authenticate via browser
- Calendar API must be enabled in the user's Google Cloud Console project
- Uses a separate token file (`.calendar_token.json`) from Gmail tokens
- No delete capability in v1 to limit blast radius
- Follow [[Company_Handbook]] approval thresholds before creating events
- See `Skills/mcp_vault_calendar.md` for full documentation
