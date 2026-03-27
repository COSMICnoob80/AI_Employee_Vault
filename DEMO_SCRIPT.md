# Demo Script — AI Employee Vault

**Target Duration:** ~8 minutes
**Format:** Screen recording with narration

---

## 0:00–0:30 | Intro + Dashboard

**Talking Point:** "This is the AI Employee Vault — an Obsidian-based autonomous AI employee powered by Claude Code. Everything the AI does is visible as markdown files in this vault."

**Show:**
- Open Obsidian with `Dashboard.md` visible
- Scroll through System Status table showing 15 components
- Point out the approval status section

**Expected Output:** Dashboard renders with component statuses, active tasks, pending approvals.

---

## 0:30–1:30 | Folder Structure + Architecture

**Talking Point:** "The architecture follows a perception → memory → reasoning → execution pipeline. Python watchers detect events, Obsidian vault stores everything as markdown, Claude Code reasons and plans, MCP servers execute actions."

**Command:**
```bash
ls ~/AI_Employee_Vault/
```

**Expected Output:** `Inbox/`, `Needs_Action/`, `Pending_Approval/`, `Approved/`, `Done/`, `Plans/`, `Skills/`, `Watchers/`, `MCP/`, `Scripts/`, `Logs/`

**Show:**
- Architecture diagram from README
- Quick look at `Company_Handbook.md` threshold table
- `Skills/` folder showing 15 skill files

---

## 1:30–3:00 | Filesystem Watcher (Live Demo)

**Talking Point:** "When a file drops into Inbox, the watcher detects it, creates a structured task in Needs_Action, and the task planner generates an execution plan."

**Commands:**
```bash
# Start watchers
bash Scripts/schedule_watchers.sh start

# Check status
bash Scripts/schedule_watchers.sh status

# Drop a test file
echo "Please draft a weekly summary email for the team" > ~/AI_Employee_Vault/Inbox/weekly_summary.txt
```

**Expected Output:**
- Watchers start with PID confirmation
- `Logs/watcher.log` shows: `New file detected: weekly_summary.txt`
- New task file appears in `Needs_Action/` with YAML frontmatter

**Cleanup:**
```bash
bash Scripts/schedule_watchers.sh stop
```

---

## 3:00–4:30 | HITL Approval Workflow

**Talking Point:** "Not all actions are autonomous. The Company Handbook defines thresholds — emails always need approval, financial actions above 500 PKR need approval, social media posts always need approval. The AI creates structured approval requests, and the human approves by moving the file."

**Show:**
- `Company_Handbook.md` — Sensitive Action Thresholds table
- Existing files in `Pending_Approval/` (email send request, 600 PKR subscription)
- Point out YAML frontmatter: `type`, `action_type`, `status`, `priority`
- Explain the flow: `Pending_Approval → Approved → Done`

**Command:**
```bash
# Show pending approval files
ls ~/AI_Employee_Vault/Pending_Approval/
```

**Expected Output:** Approval request files with structured YAML metadata.

---

## 4:30–5:30 | Ralph Wiggum Task Loop

**Talking Point:** "Ralph Wiggum is the autonomous task execution loop. It scans Needs_Action, prioritizes tasks by urgency and age, classifies them as autonomous or approval-required, and processes them — safe tasks go to Done, sensitive ones go to Pending_Approval."

**Commands:**
```bash
# Scan the queue (read-only)
python Scripts/ralph_loop.py --scan-only

# Dry run — shows what would happen without executing
python Scripts/ralph_loop.py --dry-run --once
```

**Expected Output:**
- `--scan-only`: Lists tasks in Needs_Action with priority scores
- `--dry-run --once`: Shows classification (autonomous vs approval-required) and planned actions without executing

---

## 5:30–6:30 | CEO Briefing

**Talking Point:** "The CEO Briefing aggregates data from across the vault — emails, tasks, approvals, system health, KPIs — into a weekly executive report."

**Command:**
```bash
python Scripts/ceo_briefing.py --dry-run
```

**Expected Output:** 9-section report printed to stdout:
- Email digest, task statistics, approval status
- System health, LinkedIn activity, action items
- KPI metrics with week-over-week comparison

---

## 6:30–7:30 | MCP Servers + Odoo + Social Media

**Talking Point:** "MCP servers give Claude structured tools for external services. The Odoo server connects to a Dockerized Odoo 19 instance for accounting. The social media server automates posting to Facebook, Instagram, and Twitter via Playwright."

**Commands:**
```bash
# Test Odoo connection
python MCP/odoo_server.py --test

# Social media dry run
python Scripts/social_poster.py --platform all --dry-run --once
```

**Expected Output:**
- Odoo: Connection status, database info, available models
- Social: Shows what would be posted to each platform without actually posting

**Show:**
- `MCP/` folder with 5 server files
- `.claude/mcp.json` configuration

---

## 7:30–8:00 | Cross-Domain + Wrap-Up

**Talking Point:** "Cross-domain integration gives a unified view across personal and business domains — Gmail and Calendar on the personal side, LinkedIn and tasks on the business side. Everything flows through the same approval gate."

**Command:**
```bash
python Scripts/cross_domain.py --dry-run
```

**Expected Output:** Unified summary showing personal domain (Gmail, Calendar) and business domain (LinkedIn, tasks, MCP actions) data side by side.

**Wrap-Up:**
- "238 verification checks passing across all Gold tier features"
- "Every action is auditable, every decision is visible in markdown"
- "The human stays in control through the HITL approval gate"

---

## 8:00–10:00 | Platinum: Cloud/Local Split

**Talking Point:** "The Platinum tier demonstrates cloud/local work-zone specialization. A cloud agent handles drafting while the local agent handles approval and execution. They coordinate via claim-by-move file locking — no two agents process the same file."

**Command:**
```bash
# Run the full Platinum demo (automated, no pauses)
bash Scripts/platinum_demo.sh --auto
```

**Expected Output (9 steps):**
1. Clean environment setup with In_Progress/, Updates/ directories
2. Test email dropped in Inbox/ (simulates arrival while local offline)
3. Cloud agent claims email, generates draft reply in Pending_Approval/
4. Draft shown with approval_request frontmatter (origin: cloud_agent)
5. Pause demonstrating zone separation
6. Human approves by moving draft to Approved/ (HITL gate)
7. Local agent claims approved draft, executes send (dry-run)
8. Done/ contains completed draft, audit log shows full trail
9. Dashboard.md Platinum section shows both agent statuses

**Key Points:**
- Cloud agent NEVER sends — draft-only zone
- Single-writer rule: only local agent writes Dashboard.md
- Claim-by-move prevents duplicate processing
- Full audit trail in Logs/audit.jsonl

---

## Pre-Demo Checklist

- [ ] Obsidian open with vault loaded
- [ ] Docker running (Odoo + PostgreSQL)
- [ ] `.env` and `credentials.json` in place
- [ ] Terminal ready in `~/AI_Employee_Vault/`
- [ ] Test files cleared from `Inbox/`
- [ ] Watchers stopped (clean start for demo)
