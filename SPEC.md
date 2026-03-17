---
type: spec
project: AI Employee Vault
owner: cosmicnoob
created: 2026-02-28
last_updated: 2026-03-17 20:01
current_tier: gold
tier_progress: 7/7
---

# AI Employee Vault — Project Spec

**Purpose**: Personal AI Employee for the **Personal AI Employee Hackathon 0: Building Autonomous FTEs (Full-Time Equivalent) in 2026** (PIAIC).

**Reference**: [[Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026]]

---

## Architecture Overview

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│  Watchers    │ →  │ Obsidian     │ →  │ Claude Code │ →  │ MCP Servers │
│  (Python)    │    │ Vault (MD)   │    │ (Brain)     │    │ (Actions)   │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
  Perception          Memory             Reasoning           Execution
```

**Pipeline**: `Inbox → Needs_Action → Plans → Approved → Done`

**Approval gate**: `Pending_Approval → Approved → Done` (human-in-the-loop)

---

## Tier Requirements

### Bronze ✅ Complete
- Obsidian vault with [[Dashboard]] and [[Company_Handbook]]
- Email classification skill (7-section format)
- Folder structure: Inbox/, Needs_Action/, Done/
- Filesystem watcher script

### Silver ✅ 8/8
- [x] S1: Gmail watcher (OAuth2, read-only)
- [x] S2: Human-in-the-loop approval workflow
- [x] S3: Auto LinkedIn posting (Playwright)
- [x] S4: Automated task planner
- [x] S5: MCP Gmail Send server
- [x] S6: HITL verification (independent)
- [x] S7: Scheduling/cron system
- [x] S8: All skills documented (7/7)

### Gold ✅ 7/7
- [x] G1: Weekly CEO Briefing Generator
- [x] G2: Error Recovery + Audit Logging
- [x] G3: Ralph Wiggum Task Loop
- [x] G4: Additional MCP Servers
- [x] G5: Cross-Domain Integration
- [x] G6: Odoo Community Integration
- [x] G7: Social Media (FB/IG/Twitter)

### Platinum ⏳ Future
- Cloud 24/7 deployment (Oracle/AWS Free Tier)
- Cloud/Local work-zone split (cloud drafts, local approves)
- Odoo Community on cloud VM with HTTPS + backups
- Secure vault sync (Git or Syncthing, no credentials)
- Multi-agent coordination with claim-by-move rule

---

## Current Components

### Watchers
| Script | Scope |
|--------|-------|
| `Watchers/filesystem_watcher.py` | Monitors Inbox/ for file drops |
| `Watchers/gmail_watcher.py` | Gmail OAuth2 read-only, priority keywords |
| `Watchers/approval_watcher.py` | Dual observer: Pending_Approval/ + Approved/ |

### MCP Servers
| Server | Tool |
|--------|------|
| `MCP/gmail_send_server.py` | `send_email(to, subject, body, dry_run)` |
| `MCP/filesystem_server.py` | `read_file`, `write_file`, `move_file`, `list_folder`, `search_vault` |
| `MCP/calendar_server.py` | `list_events`, `create_event`, `check_availability` |
| `MCP/odoo_server.py` | `list_invoices`, `get_invoice`, `create_invoice`, `list_accounts`, `get_journal_entries`, `accounting_summary` |
| `MCP/social_media_server.py` | `post_facebook`, `post_instagram`, `post_twitter`, `get_social_summary` |

### Scripts
| Script | Purpose |
|--------|---------|
| `Scripts/schedule_watchers.sh` | Start/stop/status for all watchers |
| `Scripts/cron_setup.sh` | Cron install/remove (5-min keep-alive) |
| `Scripts/linkedin_poster.py` | Playwright LinkedIn text auto-poster |
| `Scripts/ceo_briefing.py` | Weekly CEO Briefing report generator |
| `Scripts/ralph_loop.py` | Ralph Wiggum autonomous task execution loop |
| `Scripts/ralph_hooks.sh` | PostToolUse hook for audit logging |
| `Scripts/cross_domain.py` | Cross-domain query, routing, and unified view |
| `Scripts/social_poster.py` | Social media auto-poster (FB/IG/Twitter via Playwright) |
| `Scripts/start_dashboard.sh` | Start/stop/status for AEWACS Command Center (API + Web) |

### AEWACS Command Center

Visual HUD dashboard (React SPA + Flask API) surfacing vault operational state.

**API Endpoints** (`Dashboard/api/server.py`, port 5001):
| Endpoint | Data Source |
|----------|------------|
| `GET /api/status` | `Dashboard.md` frontmatter + component table |
| `GET /api/tasks` | `Needs_Action/*.md` frontmatter |
| `GET /api/approvals` | `Pending_Approval/*.md` frontmatter |
| `GET /api/briefing` | Latest `Reports/CEO_Briefing_*.md` |
| `GET /api/odoo/invoices` | Odoo JSON-RPC (dry-run fallback) |
| `GET /api/odoo/summary` | Odoo JSON-RPC (dry-run fallback) |
| `GET /api/audit?n=10` | `Logs/audit.jsonl` tail |
| `GET /api/mcp` | `.claude/mcp.json` + tool count per server |

**Frontend Components** (`Dashboard/web/`, port 5173):
HeaderBar, TierProgress, MetricCards, StatusGrid, McpServerArray, OdooPanel, ApprovalsTable, GoldMatrix, BriefingPreview, AuditTail

### Skills (15)
| Skill | File |
|-------|------|
| Email Classifier | [[email_classifier]] |
| Gmail Processor | [[gmail_processor]] |
| Inbox Processor | [[inbox_processor]] |
| Approval Requester | [[approval_requester]] |
| Task Planner | [[task_planner]] |
| Scheduler | [[scheduler]] |
| MCP Gmail Send | [[mcp_gmail_send]] |
| LinkedIn Poster | [[linkedin_poster]] |
| CEO Briefing | [[ceo_briefing]] |
| Ralph Wiggum | [[ralph_wiggum]] |
| MCP Vault FS | [[mcp_vault_fs]] |
| MCP Vault Calendar | [[mcp_vault_calendar]] |
| Cross-Domain Integration | [[cross_domain_integration]] |
| Odoo Accounting | [[odoo_accounting]] |
| Social Media Poster | [[social_media_poster]] |

### Core Docs
- [[Dashboard]] — Central status hub
- [[Company_Handbook]] — Rules, thresholds, approval workflow
- [[Business_Goals]] — Targets and metrics

---

## File Ownership Map

| Owner | Scope |
|-------|-------|
| **Claude Code** | Needs_Action/*, Plans/*, Done/*, Skills/*, Logs/*, Dashboard.md metrics |
| **Human** | Approved/* (move-to-approve), Business_Goals.md, Company_Handbook.md, credentials.json, .env |
| **Watchers** | Logs/*.log, .gmail_token*.json (auto-refresh), *.pid |
| **Shared** | Inbox/ (human drops, watcher reads), Pending_Approval/ (Claude creates, human reviews) |

---

## Evaluation Rubric

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Functionality | 30% | Core features complete and working |
| Innovation | 25% | Creative solutions, novel integrations |
| Practicality | 20% | Daily-use viability |
| Security | 15% | Credential handling, HITL safeguards |
| Documentation | 10% | README, setup instructions, demo |
