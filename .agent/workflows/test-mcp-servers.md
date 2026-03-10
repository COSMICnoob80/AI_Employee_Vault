---
description: Test the three MCP Servers programmatically via dry-run and audit log verification.
---

# test-mcp-servers

* Run `python MCP/gmail_send_server.py --help` (or `--dry-run`)
* Run `python MCP/filesystem_server.py --dry-run`
* Run `python MCP/calendar_server.py --dry-run`
* Check `Logs/audit.jsonl` for entries from each server
* Report pass/fail for each
