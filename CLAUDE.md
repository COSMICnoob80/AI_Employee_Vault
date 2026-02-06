# AI Employee Vault - Project Rules

## Project Overview
Personal AI Employee system built as an Obsidian vault. Automates email triage, task management, and business operations.

## Directory Structure
```
AI_Employee_Vault/
├── Inbox/            → Drop zone for incoming items
├── Needs_Action/     → Active tasks requiring attention
├── Plans/            → Implementation plans for tasks
├── Approved/         → Human-approved actions
├── Done/             → Completed tasks (audit trail)
├── Pending_Approval/ → Awaiting human confirmation
├── Watchers/         → Python automation scripts
├── Skills/           → Skill definitions (markdown)
├── Logs/             → Activity logs
├── Dashboard.md      → Central status hub
├── Company_Handbook.md → Rules of engagement
└── Business_Goals.md → Targets and metrics
```

## Workflow Pipeline
`Inbox → Needs_Action → Plans → Approved → Done`

## File Conventions
- All content files use **YAML frontmatter** with `type`, `created`, `status` fields
- Use **[[wikilinks]]** for cross-referencing between vault files
- Task files include checkbox action items
- Timestamps use ISO 8601 format

## Code Conventions
- Python scripts use `#!/usr/bin/env python3` shebang
- Logging to `Logs/` directory with format: `%(asctime)s [%(levelname)s] %(message)s`
- Config uses `pathlib.Path` with `VAULT_ROOT = Path.home() / "AI_Employee_Vault"`
- Sensitive files (tokens, credentials) go in `.gitignore`

## Security Rules
- NEVER commit `.gmail_token.json` or `credentials.json` content
- NEVER hardcode secrets; use `.env` or config files
- Gmail API uses read-only scope only
- All external actions require human approval per Company_Handbook thresholds

## Key Files
- `Watchers/gmail_watcher.py` — Gmail monitoring (OAuth2, watchdog)
- `Watchers/filesystem_watcher.py` — Inbox file monitoring
- `Skills/email_classifier.md` — Email categorization rules
- `Skills/gmail_processor.md` — Gmail handling procedures
