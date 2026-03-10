---
type: dashboard
created: 2026-02-02
last_updated: 2026-03-10 19:58
status: active
pending_tasks: 4
plans_created: 3
---

# 📊 AI Employee Dashboard

## System Status

| Component | Status | Last Activity |
|-----------|--------|---------------|
| File Watcher | 🟢 Active | 2026-02-04 18:52 |
| Gmail Watcher | 🟡 Ready | Not started |
| Approval Watcher | 🟢 Ready | 2026-02-25 |
| Task Processor | 🟢 Active | 2026-02-04 18:52 |
| Goal Tracker | 🟢 Active | 2026-02-04 18:52 |
| Scheduler | 🟢 Ready | 2026-02-26 |
| MCP Gmail Send | 🟡 Ready | Not started |
| LinkedIn Poster | 🟡 Ready | Not started |
| CEO Briefing | 🟢 Ready | Not started |
| Ralph Wiggum Loop | 🟢 Ready | Not started |
| MCP Vault FS | 🟢 Ready | Not started |
| MCP Vault Calendar | 🟡 Ready | Not started |
| Cross-Domain Router | 🟢 Ready | Not started |

## Active Tasks

<!-- Auto-populated by task system -->
| Task | Priority | Due | Status |
|------|----------|-----|--------|
| [[20260204_185223_urgent_email\|Process urgent_email.txt]] | 🔴 high | ASAP | planned |
| [[20260202_220257_test_file\|Process test_file.txt]] | normal | - | planned |

## Recent Completions

| Task | Completed | Notes |
|------|-----------|-------|
| Vault initialization | 2026-02-02 | Foundation created |
| Demo verification | 2026-02-04 | Bronze tier validated |

## Gmail Status

| Metric | Value |
|--------|-------|
| Last Checked | _Not started_ |
| Unread Important | - |
| Pending Responses | - |

_Start watcher: `python ~/AI_Employee_Vault/Watchers/gmail_watcher.py`_

## Planning Status

| Metric | Count |
|--------|-------|
| Tasks awaiting planning | 0 |
| Tasks with plans | 22 |
| Active plans | 22 |
| Skills Documented | 12 |

## Approval Status

| Metric | Value |
|--------|-------|
| Pending Approvals | 2 |
| Approved Today | 0 |
| Rejected Today | 0 |

### Pending Requests
| Request | Type | Priority | Requested |
|---------|------|----------|-----------|
| [[20260225_test_email_send\|Send Project Status Email]] | 📧 Email | 🔴 high | 2026-02-25 |
| [[20260225_test_spend_600pkr\|Software Subscription 600 PKR]] | 💰 Financial | 🟡 normal | 2026-02-25 |

_Monitored by: `python ~/AI_Employee_Vault/Watchers/approval_watcher.py`_

## Scheduler Status

| Metric | Value |
|--------|-------|
| Mode | Cron (5-min keep-alive) |
| Last Health Check | _Not started_ |
| Log File | `Logs/scheduler.log` |

**Commands:**
- Start all: `bash Scripts/schedule_watchers.sh start`
- Stop all: `bash Scripts/schedule_watchers.sh stop`
- Check status: `bash Scripts/schedule_watchers.sh status`
- Install cron: `bash Scripts/cron_setup.sh install`
- Remove cron: `bash Scripts/cron_setup.sh remove`

## CEO Briefing Status

| Metric | Value |
|--------|-------|
| Last Run | _Not started_ |
| Last Report | — |
| Schedule | Manual / Weekly |

**Commands:**
- Generate: `python Scripts/ceo_briefing.py`
- Dry run: `python Scripts/ceo_briefing.py --dry-run`
- Specific week: `python Scripts/ceo_briefing.py --week 2026-W10`

## Ralph Wiggum Status

| Metric | Value |
|--------|-------|
| Queue Size | _Not scanned_ |
| Last Run | _Not started_ |
| Tasks Processed | 0 |
| Status | Idle |

**Commands:**
- Scan queue: `python Scripts/ralph_loop.py --scan-only`
- Dry run: `python Scripts/ralph_loop.py --dry-run --once`
- Single pass: `python Scripts/ralph_loop.py --once`
- Continuous: `python Scripts/ralph_loop.py`
- Stop: `touch .ralph_stop`

## Personal Domain Status

| Metric | Value |
|--------|-------|
| Gmail Inbox Tasks | _Run `python Scripts/cross_domain.py --domain personal`_ |
| Calendar Events (7d) | _Run `python Scripts/cross_domain.py --domain personal`_ |
| Personal Tasks Pending | _Run `python Scripts/cross_domain.py --domain personal`_ |

## Business Domain Status

| Metric | Value |
|--------|-------|
| LinkedIn Posts (week) | _Run `python Scripts/cross_domain.py --domain business`_ |
| Business Tasks Pending | _Run `python Scripts/cross_domain.py --domain business`_ |
| MCP Actions Today | _Run `python Scripts/cross_domain.py --domain business`_ |

## Cross-Domain Health

| Metric | Value |
|--------|-------|
| Domain Coverage | personal + business |
| Last Unified Report | -- |

**Commands:**
- Unified summary: `python Scripts/cross_domain.py --dry-run`
- Personal only: `python Scripts/cross_domain.py --domain personal`
- Business only: `python Scripts/cross_domain.py --domain business`
- Backfill tags: `python Scripts/cross_domain.py --backfill --dry-run`
- JSON output: `python Scripts/cross_domain.py --json`

## Quick Links

- [[Company_Handbook]] — Rules & guidelines
- [[Business_Goals]] — Targets & metrics
- [[gmail_processor]] — Email handling rules

