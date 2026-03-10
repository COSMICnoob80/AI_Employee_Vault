---
id: 7
title: "G4 Additional MCP Servers"
stage: general
date: 2026-03-07
surface: agent
model: claude-opus-4-6
feature: none
branch: master
user: cosmicnoob
command: "implement G4 additional MCP servers"
labels: ["gold-tier", "mcp", "filesystem", "calendar", "oauth2", "audit"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - MCP/filesystem_server.py
  - MCP/calendar_server.py
  - Skills/mcp_vault_fs.md
  - Skills/mcp_vault_calendar.md
  - .claude/skills/vault-fs/SKILL.md
  - .claude/skills/vault-calendar/SKILL.md
  - .claude/mcp.json
  - .gitignore
  - SPEC.md
  - Dashboard.md
  - Skills/README.md
tests:
  - "python3 -c ast.parse filesystem_server.py — pass (syntax OK)"
  - "python3 -c ast.parse calendar_server.py — pass (syntax OK)"
  - "python3 -c import vault_audit — pass (audit_log, safe_write, ErrorTracker, retry all resolve)"
  - "consistency check — pass (mcp.json=3 servers, SPEC tier_progress=4/7, G4 checked, .gitignore has .calendar_token.json)"
---

## Prompt

Implement the G4: Additional MCP Servers plan. Create a vault filesystem MCP server (5 tools: read_file, write_file, move_file, list_folder, search_vault) and a Google Calendar MCP server (3 tools: list_events, create_event, check_availability). Both servers follow the existing FastMCP pattern from gmail_send_server.py and integrate with vault_audit infrastructure. Update all documentation (SPEC.md, Dashboard.md, Skills/README.md), register in mcp.json, create skill docs and Claude Code skill triggers.

## Response

Implemented G4 by creating 6 new files and updating 5 existing files:

**Filesystem MCP Server** (`MCP/filesystem_server.py`, ~190 lines):
- 5 tools with path validation preventing traversal outside vault
- write_file uses safe_write() for atomic writes
- read_file truncates at 50K chars, search_vault limited to 20 matches
- All operations audit-logged, ErrorTracker for circuit breaking

**Calendar MCP Server** (`MCP/calendar_server.py`, ~210 lines):
- 3 tools matching gmail_send_server.py OAuth2 pattern
- Separate token (.calendar_token.json), OAuth port 8093
- @retry decorator on API calls, ErrorTracker for circuit breaking
- No delete_event in v1 (limits blast radius)
- Input validation: summary non-empty, end > start, ISO 8601 format

**Documentation**: Skill docs (7-section format), SKILL.md trigger files, mcp.json registration (3 servers total), .gitignore updated, SPEC.md tier_progress 4/7 with G4 checked, Dashboard.md with 2 new status rows, Skills/README.md updated to 12 skills.

All verification checks passed: syntax, imports, and cross-file consistency.
