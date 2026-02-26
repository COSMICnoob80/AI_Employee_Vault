---
type: dashboard
created: 2026-02-02
last_updated: 2026-02-25 14:30
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

## Quick Links

- [[Company_Handbook]] — Rules & guidelines
- [[Business_Goals]] — Targets & metrics
- [[gmail_processor]] — Email handling rules

