# AI Employee Vault

> **Author:** Shah G | **Tier:** Platinum 5/5 | **Gold Checks:** 238/238 | **Skills:** 16 | **MCP Servers:** 5

---

## What Is This?

An Obsidian-based autonomous AI employee that treats **Claude Code as its brain**, **Python watchers as perception**, **MCP servers as execution hands**, and a **human-in-the-loop (HITL) approval gate** as its conscience. Drop a file in `Inbox/`, and the system detects it, plans the work, routes sensitive actions for human approval, executes safe tasks autonomously, and logs everything — all within a markdown vault you can read in Obsidian.

---

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│  Watchers    │ →  │ Obsidian     │ →  │ Claude Code │ →  │ MCP Servers │
│  (Python)    │    │ Vault (MD)   │    │ (Brain)     │    │ (Actions)   │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
  Perception          Memory             Reasoning           Execution
```

**Pipeline:** `Inbox → Needs_Action → Plans → Approved → Done`
**Approval Gate:** `Pending_Approval → Approved → Done` (human-in-the-loop)

---

## Tech Stack

| Technology | Role |
|-----------|------|
| Claude Code (Opus) | AI brain — reasoning, planning, execution |
| Obsidian | Human-readable vault interface |
| Python 3.10+ | Watchers, scripts, MCP servers |
| FastMCP | Model Context Protocol server framework |
| Playwright | Browser automation (LinkedIn, FB, IG, Twitter) |
| Docker | Container isolation for Odoo + PostgreSQL |
| Odoo 19 Community | Accounting / ERP integration |
| PostgreSQL 16 | Odoo database backend |
| Gmail API (OAuth2) | Email reading + sending |
| Google Calendar API | Calendar operations |

---

## Tier Completion

| Tier | Items | Checks | Details |
|------|-------|--------|---------|
| Bronze | 4/4 | 25/25 | Vault structure, Dashboard, Handbook, email skill, filesystem watcher |
| Silver | 8/8 | S1-S8 | Gmail watcher, HITL workflow, LinkedIn poster, task planner, MCP Gmail, HITL verification, cron system, skills docs |
| **Gold** | **7/7** | **238/238** | G1=45, G2=17, G3=37, G4=14, G5=9, G6=52, G7=64 |
| **Platinum** | **5/5** | — | Cloud/local split, claim-by-move, sync, single-writer, e2e demo |

### Gold Breakdown

| ID | Feature | Checks |
|----|---------|--------|
| G1 | Weekly CEO Briefing Generator | 45 |
| G2 | Error Recovery + Audit Logging | 17 |
| G3 | Ralph Wiggum Task Loop | 37 |
| G4 | Additional MCP Servers (FS + Calendar) | 14 |
| G5 | Cross-Domain Integration | 9 |
| G6 | Odoo Community Integration | 52 |
| G7 | Social Media (FB/IG/Twitter) | 64 |

---

## Component Inventory

### Watchers (3)

| Script | Scope |
|--------|-------|
| `Watchers/filesystem_watcher.py` | Monitors `Inbox/` for file drops |
| `Watchers/gmail_watcher.py` | Gmail OAuth2 read-only, priority keywords |
| `Watchers/approval_watcher.py` | Dual observer: `Pending_Approval/` + `Approved/` |

### MCP Servers (5)

| Server | Tools |
|--------|-------|
| `MCP/gmail_send_server.py` | `send_email` |
| `MCP/filesystem_server.py` | `read_file`, `write_file`, `move_file`, `list_folder`, `search_vault` |
| `MCP/calendar_server.py` | `list_events`, `create_event`, `check_availability` |
| `MCP/odoo_server.py` | `list_invoices`, `get_invoice`, `create_invoice`, `list_accounts`, `get_journal_entries`, `accounting_summary` |
| `MCP/social_media_server.py` | `post_facebook`, `post_instagram`, `post_twitter`, `get_social_summary` |

### Scripts (13)

| Script | Purpose |
|--------|---------|
| `Scripts/schedule_watchers.sh` | Start/stop/status for all watchers |
| `Scripts/cron_setup.sh` | Cron install/remove (5-min keep-alive) |
| `Scripts/linkedin_poster.py` | Playwright LinkedIn auto-poster |
| `Scripts/ceo_briefing.py` | Weekly CEO Briefing report generator |
| `Scripts/ralph_loop.py` | Autonomous task execution loop |
| `Scripts/ralph_hooks.sh` | PostToolUse hook for audit logging |
| `Scripts/cross_domain.py` | Cross-domain query + unified view |
| `Scripts/social_poster.py` | Social media auto-poster (FB/IG/Twitter) |
| `Scripts/claim_manager.py` | Claim-by-move coordination module |
| `Scripts/cloud_agent.py` | Cloud zone: draft-only agent |
| `Scripts/local_agent.py` | Local zone: approve+execute agent |
| `Scripts/vault_sync.sh` | Git-based sync checkpoints |
| `Scripts/platinum_demo.sh` | End-to-end Platinum demo |

### Skills (16)

| Skill | Description |
|-------|-------------|
| Email Classifier | Categorizes emails by urgency/type |
| Gmail Processor | Processes Gmail with response templates |
| Inbox Processor | Creates tasks from file drops |
| Approval Requester | HITL safety gate |
| Task Planner | Step-by-step plans from tasks |
| Scheduler | Watcher startup + self-healing cron |
| MCP Gmail Send | Email sending via MCP |
| LinkedIn Poster | Automated LinkedIn posting |
| CEO Briefing | Weekly executive report |
| Ralph Wiggum | Autonomous task loop |
| MCP Vault FS | Safe vault file operations |
| MCP Vault Calendar | Google Calendar via OAuth2 |
| Cross-Domain Integration | Unified personal + business view |
| Odoo Accounting | Odoo JSON-RPC accounting |
| Social Media Poster | FB/IG/Twitter via Playwright |
| Platinum Architecture | Cloud/local zone split design |

---

## Platinum Tier: Cloud/Local Split

Two-agent architecture simulating cloud+local work-zone specialization:

| Agent | Zone | Capability |
|-------|------|------------|
| Cloud Agent | Draft-only | Scans Inbox/Needs_Action, generates drafts, writes to Pending_Approval/ |
| Local Agent | Approve+Execute | Merges cloud status to Dashboard, executes approved drafts, archives to Done/ |

**Key design patterns:**
- **Claim-by-move:** Atomic file claiming via `In_Progress/{agent}/` prevents duplicate processing
- **Single-writer Dashboard:** Only local agent writes Dashboard.md; cloud writes Updates/
- **Secrets-never-sync:** Credentials stay on local machine
- **HITL preserved:** Cloud drafts require human approval before local execution

```bash
# Run the full Platinum demo
bash Scripts/platinum_demo.sh --auto
```

---

## Setup

### Prerequisites

- Python 3.10+
- Claude Code CLI
- Obsidian
- Docker + Docker Compose
- Playwright (`pip install playwright && playwright install`)

### Quick Start

```bash
# Clone
git clone https://github.com/cosmicnoob/AI_Employee_Vault.git
cd AI_Employee_Vault

# Install Python dependencies
pip install fastmcp google-auth google-auth-oauthlib google-api-python-client playwright watchdog

# Docker for Odoo (optional)
docker compose up -d  # starts Odoo 19 + PostgreSQL 16

# Set up credentials
cp .env.example .env  # edit with your API keys
# Place credentials.json for Gmail/Calendar OAuth

# Start watchers
bash Scripts/schedule_watchers.sh start

# Install cron (optional, 5-min keep-alive)
bash Scripts/cron_setup.sh install

# Start AEWACS Command Center dashboard
bash Scripts/start_dashboard.sh start
# Open http://localhost:5173
```

---

## AEWACS Command Center

Military HUD-style web dashboard surfacing vault operational state — component health, pending tasks, approvals, financials, audit trail, and CEO briefings.

| Layer | Tech | Port |
|-------|------|------|
| API | Flask (Python) | 5001 |
| Frontend | React + Vite | 5173 |
| Design | Share Tech Mono + Outfit, glass-panel HUD | — |

```bash
bash Scripts/start_dashboard.sh start   # start both servers
bash Scripts/start_dashboard.sh status  # check running state
bash Scripts/start_dashboard.sh stop    # clean shutdown
```

---

## Security

All credentials are gitignored. HITL approval gates protect external communications, financial actions, social media posts, data deletion, and system changes. Vault filesystem MCP enforces path boundaries. Audit logging with `fcntl` locking and circuit breaker. Odoo runs in Docker isolation.

See **[SECURITY.md](SECURITY.md)** for full details.

---

## Lessons Learned

- **Markdown as universal interface** — Obsidian vault gives the human full visibility into every AI decision, plan, and action. No black box.
- **HITL is essential, not optional** — Threshold-based approval gates prevent costly mistakes while allowing safe tasks to run autonomously.
- **MCP as capability protocol** — FastMCP servers turn external services (Gmail, Calendar, Odoo, social) into tools Claude can invoke with structured I/O.
- **Watchers as perception layer** — Python filesystem/Gmail watchers give the AI employee senses without polling or manual triggers.

---

## License

MIT
