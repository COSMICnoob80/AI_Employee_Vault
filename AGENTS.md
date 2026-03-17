# AI Employee Vault — Agent Reference

**Last Updated:** 2026-03-17 20:01
**Project:** AI Employee Vault
**Compatibility:** Any AI coding agent (Claude Code, Antigravity, Cursor, Aider, etc.)

> This is the **universal agent reference**. For Claude Code-specific features (PHR, ADR, memory system), see [`CLAUDE.md`](CLAUDE.md).

---

## Project Overview

An Obsidian-based autonomous AI employee vault. Python watchers perceive events, markdown files store memory, AI agents reason and plan, MCP servers execute actions. Human-in-the-loop approval gates protect sensitive operations.

**Pipeline:** `Inbox → Needs_Action → Plans → Approved → Done`
**Approval:** `Pending_Approval → Approved → Done` (human reviews)

---

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│  Watchers    │ →  │ Obsidian     │ →  │  AI Agent   │ →  │ MCP Servers │
│  (Python)    │    │ Vault (MD)   │    │  (Brain)    │    │ (Actions)   │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
  Perception          Memory             Reasoning           Execution
```

---

## Folder Structure

| Folder | Purpose | Owner |
|--------|---------|-------|
| `Inbox/` | Landing zone for new files | Human drops, Watcher reads |
| `Needs_Action/` | Structured tasks | AI creates, AI updates |
| `Plans/` | Execution plans | AI creates |
| `Pending_Approval/` | Actions needing human OK | AI creates, Human reviews |
| `Approved/` | Human-approved actions | Human moves here |
| `Done/` | Completed items | AI archives |
| `Skills/` | 15 skill files (7-section format) | Human-maintained |
| `Watchers/` | 3 Python watchers | AI/Human |
| `MCP/` | 5 MCP servers (FastMCP, stdio) | AI executes |
| `Scripts/` | 8 automation scripts | AI/Human |
| `Logs/` | Audit + activity logs | Watchers + AI |

---

## MCP Servers (5)

Registered in `.claude/mcp.json`. All use `python3` + `stdio` transport.

| Server | Name in Config | Tools |
|--------|---------------|-------|
| `MCP/gmail_send_server.py` | `gmail-send` | `send_email` |
| `MCP/filesystem_server.py` | `vault-fs` | `read_file`, `write_file`, `move_file`, `list_folder`, `search_vault` |
| `MCP/calendar_server.py` | `vault-calendar` | `list_events`, `create_event`, `check_availability` |
| `MCP/odoo_server.py` | `odoo-accounting` | `list_invoices`, `get_invoice`, `create_invoice`, `list_accounts`, `get_journal_entries`, `accounting_summary` |
| `MCP/social_media_server.py` | `social-media` | `post_facebook`, `post_instagram`, `post_twitter`, `get_social_summary` |

---

## Key Scripts

| Script | Purpose | Quick Test |
|--------|---------|------------|
| `Scripts/schedule_watchers.sh` | Start/stop/status all watchers | `bash Scripts/schedule_watchers.sh status` |
| `Scripts/cron_setup.sh` | Cron install/remove (5-min keep-alive) | `bash Scripts/cron_setup.sh status` |
| `Scripts/ralph_loop.py` | Autonomous task execution loop | `python Scripts/ralph_loop.py --scan-only` |
| `Scripts/ceo_briefing.py` | Weekly CEO Briefing generator | `python Scripts/ceo_briefing.py --dry-run` |
| `Scripts/cross_domain.py` | Cross-domain unified view | `python Scripts/cross_domain.py --dry-run` |
| `Scripts/social_poster.py` | FB/IG/Twitter auto-poster | `python Scripts/social_poster.py --platform all --dry-run --once` |
| `Scripts/linkedin_poster.py` | LinkedIn auto-poster | `python Scripts/linkedin_poster.py --dry-run --once` |

---

## HITL Approval Thresholds

Per `Company_Handbook.md`:

| Action Type | Threshold | Approval |
|-------------|-----------|----------|
| External Email | Any outbound | Always required |
| Financial | > 500 PKR | Always required |
| Financial | ≤ 500 PKR | Autonomous (tracked) |
| Social Media | Any post | Always required |
| Data Deletion | Any permanent | Always required |
| System Changes | Config/install | Always required |

---

## File Ownership

| Owner | Scope |
|-------|-------|
| **AI Agent** | `Needs_Action/*`, `Plans/*`, `Done/*`, `Skills/*`, `Logs/*`, `Dashboard.md` metrics |
| **Human** | `Approved/*`, `Business_Goals.md`, `Company_Handbook.md`, `credentials.json`, `.env` |
| **Watchers** | `Logs/*.log`, `.gmail_token*.json`, `*.pid` |
| **Shared** | `Inbox/` (human drops, watcher reads), `Pending_Approval/` (AI creates, human reviews) |

---

## Key Documents

| File | Purpose |
|------|---------|
| [`SPEC.md`](SPEC.md) | Tier requirements, component inventory |
| [`Dashboard.md`](Dashboard.md) | System status, active tasks, metrics |
| [`Company_Handbook.md`](Company_Handbook.md) | Rules, thresholds, approval workflow |
| [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) | Independent verification of all tiers |
| [`SECURITY.md`](SECURITY.md) | Credential handling, HITL, audit, Docker |
| [`Skills/README.md`](Skills/README.md) | Skills index (15 skills, 7-section format) |

---

## Development Rules

1. **Verify externally** — Use MCP tools and CLI for all information gathering. Never assume.
2. **Smallest viable diff** — Do not refactor unrelated code.
3. **No hardcoded secrets** — Use `.env` files, all gitignored.
4. **HITL for sensitive actions** — Route through `Pending_Approval/` per Company Handbook.
5. **Audit everything** — All tool invocations logged to `Logs/audit.jsonl`.
6. **Dry-run first** — All scripts and MCP servers support `--dry-run`.
7. **Skills as knowledge** — Read `Skills/*.md` before executing domain-specific tasks.
8. **Dashboard as truth** — Update `Dashboard.md` after significant state changes.

---

## Quick Start for Any Agent

```bash
# 1. Check system status
cat Dashboard.md

# 2. Check current tier/progress
head -10 SPEC.md

# 3. Read the handbook rules
cat Company_Handbook.md

# 4. Start watchers
bash Scripts/schedule_watchers.sh start

# 5. Run a dry-run CEO briefing
python Scripts/ceo_briefing.py --dry-run

# 6. Check verification status
head -20 VERIFICATION_REPORT.md
```

---

## Tier Status

| Tier | Status | Items |
|------|--------|-------|
| Bronze | ✅ Complete | 4/4 |
| Silver | ✅ Complete | 8/8 |
| Gold | ✅ Complete | 7/7 (238 verification checks) |
| Platinum | ⏳ Future | Cloud deployment, vault sync, multi-agent |
