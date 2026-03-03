---
type: spec
project: AI Employee Vault
owner: cosmicnoob
created: 2026-02-28
current_tier: silver
tier_progress: 6/7
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

### Silver 🟡 6/7
- [x] S1: Gmail watcher (OAuth2, read-only)
- [x] S2: Human-in-the-loop approval workflow
- [ ] S3: Full inbox → email → task pipeline
- [x] S4: Automated task planner
- [x] S5: MCP Gmail Send server
- [x] S6: HITL verification (independent)
- [x] S7: Scheduling/cron system
- [x] S8: All skills documented (7/7)

### Gold ⏳ Planned
- Odoo Community integration (JSON-RPC MCP server)
- WhatsApp watcher for customer communication
- LinkedIn/Twitter automated posting with scheduling
- Multi-source financial integration (bank CSV, Stripe, PayPal)
- Ralph Wiggum Stop hook for iterative task completion
- Cross-domain integration (Personal + Business)

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

### Scripts
| Script | Purpose |
|--------|---------|
| `Scripts/schedule_watchers.sh` | Start/stop/status for all watchers |
| `Scripts/cron_setup.sh` | Cron install/remove (5-min keep-alive) |

### Skills (7)
| Skill | File |
|-------|------|
| Email Classifier | [[email_classifier]] |
| Gmail Processor | [[gmail_processor]] |
| Inbox Processor | [[inbox_processor]] |
| Approval Requester | [[approval_requester]] |
| Task Planner | [[task_planner]] |
| Scheduler | [[scheduler]] |
| MCP Gmail Send | [[mcp_gmail_send]] |

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
