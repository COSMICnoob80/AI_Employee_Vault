# Security Overview — AI Employee Vault

---

## Credential Handling

All sensitive files are excluded from version control via `.gitignore`:

| Entry | Purpose |
|-------|---------|
| `.env` | API keys, secrets, configuration tokens |
| `.env.odoo` | Odoo database credentials (admin password, DB name) |
| `*.pid` | Runtime process ID files |
| `__pycache__/` | Python bytecode cache |
| `.gmail_token.json` | Gmail OAuth2 token (read-only watcher) |
| `.gmail_token_send.json` | Gmail OAuth2 token (send server) |
| `.gmail_processed_ids.json` | Processed email ID cache |
| `.calendar_token.json` | Google Calendar OAuth2 token |
| `credentials.json` | Google API OAuth2 client credentials |
| `.linkedin_session/` | Playwright LinkedIn session state |
| `.social_sessions/` | Playwright social media session state (FB/IG/Twitter) |
| `Logs/audit.jsonl` | Runtime audit log (contains action details) |
| `Reports/*.md` | Generated reports (may contain sensitive data) |

**No credentials are hardcoded.** All secrets are loaded from `.env` files at runtime.

---

## Human-in-the-Loop (HITL) Safeguards

The Company Handbook defines mandatory approval thresholds:

| Action Type | Threshold | Approval Required |
|-------------|-----------|-------------------|
| External Email | Any outbound | Always |
| Financial | > 500 PKR | Always |
| Financial | <= 500 PKR | Autonomous (tracking/reporting only) |
| Social Media | Any post | Always |
| Data Deletion | Any permanent | Always |
| System Changes | Config/install | Always |

### Approval Workflow

```
1. Detection    — AI identifies action matching a threshold
2. Request      — Structured YAML file created in Pending_Approval/
3. Human Review — User sees request in Obsidian
4. Decision     — User moves to Approved/ (approve) or deletes (reject)
5. Execution    — Approval watcher detects decision, executes, archives to Done/
```

All transitions are logged to `Logs/approval.log`. The approval watcher (`Watchers/approval_watcher.py`) monitors both `Pending_Approval/` and `Approved/` directories.

### What the AI Can Do Autonomously

- Read and organize files
- Generate reports and summaries
- Schedule reminders
- Track metrics and goals
- Research and information gathering
- Create new task/plan files

---

## Vault Boundary Enforcement

The filesystem MCP server (`MCP/filesystem_server.py`) enforces path security:

- **`_validate_path()`** resolves all paths to `VAULT_ROOT` (`~/AI_Employee_Vault/`)
- Symlink traversal is blocked — resolved paths must remain within vault
- Path traversal attempts (`../`) are caught after resolution
- All file operations are logged to the audit system

### File Ownership Map

| Owner | Scope |
|-------|-------|
| **Claude Code** | `Needs_Action/*`, `Plans/*`, `Done/*`, `Skills/*`, `Logs/*`, `Dashboard.md` metrics |
| **Human** | `Approved/*` (move-to-approve), `Business_Goals.md`, `Company_Handbook.md`, `credentials.json`, `.env` |
| **Watchers** | `Logs/*.log`, `.gmail_token*.json` (auto-refresh), `*.pid` |
| **Shared** | `Inbox/` (human drops, watcher reads), `Pending_Approval/` (Claude creates, human reviews) |

---

## Audit Logging

The audit system (`Scripts/vault_audit.py`) provides:

- **JSON Lines format** — structured, parseable audit trail
- **`fcntl` file locking** — prevents concurrent write corruption
- **Atomic writes** — `safe_write()` uses temp file + rename
- **`@retry` decorator** — exponential backoff for transient failures
- **`ErrorTracker` circuit breaker** — prevents cascade failures when a subsystem is unhealthy

### PostToolUse Hook

`Scripts/ralph_hooks.sh` runs as a Claude Code `PostToolUse` hook, logging every tool invocation (file reads, writes, moves, MCP calls) to `Logs/audit.jsonl` with timestamps, tool name, and parameters.

---

## Docker Isolation

Odoo 19 Community and PostgreSQL 16 run in Docker containers:

- **No direct database access** — all Odoo interaction is via JSON-RPC through `MCP/odoo_server.py`
- **Container network isolation** — Odoo and PostgreSQL communicate on an internal Docker network
- **Credentials in `.env.odoo`** — gitignored, not in container images
- **Dry-run mode** — `python MCP/odoo_server.py --dry-run` prevents real writes

---

## Responsible Disclosure

This is a **hackathon project** built for the Personal AI Employee Hackathon 0 (PIAIC). It is designed for single-user, local operation and has not been audited for production deployment.

**Known limitations:**
- OAuth2 tokens are stored as local JSON files (standard for Google API client libraries)
- Playwright sessions persist browser state to disk
- No network encryption between local services (localhost only)

**Contact:** Open an issue on the repository for security concerns.
