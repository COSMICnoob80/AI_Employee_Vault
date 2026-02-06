# AI Employee Architecture

**Version**: 1.0 (Bronze Tier)  
**Last Updated**: 2026-02-04

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI EMPLOYEE VAULT                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     🔭 PERCEPTION LAYER                              │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │    │
│  │  │ filesystem_     │  │ [future]        │  │ [future]        │      │    │
│  │  │ watcher.py      │  │ email_watcher   │  │ calendar_watch  │      │    │
│  │  └────────┬────────┘  └─────────────────┘  └─────────────────┘      │    │
│  └───────────┼──────────────────────────────────────────────────────────┘    │
│              │                                                               │
│              ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     💾 MEMORY LAYER (Vault)                          │    │
│  │                                                                      │    │
│  │  ┌──────────┐   ┌──────────────┐   ┌─────────────────┐              │    │
│  │  │  Inbox   │──▶│ Needs_Action │──▶│ Pending_Approval│              │    │
│  │  └──────────┘   └──────────────┘   └────────┬────────┘              │    │
│  │                                              │                       │    │
│  │                                    ┌─────────▼────────┐              │    │
│  │  ┌──────────┐   ┌──────────────┐   │    Approved      │              │    │
│  │  │   Done   │◀──│    Plans     │◀──└──────────────────┘              │    │
│  │  └──────────┘   └──────────────┘                                     │    │
│  │                                                                      │    │
│  │  ┌──────────┐   ┌──────────────┐   ┌─────────────────┐              │    │
│  │  │  Skills  │   │    Logs      │   │ Core Docs (.md) │              │    │
│  │  └──────────┘   └──────────────┘   └─────────────────┘              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│              │                                                               │
│              ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     🧠 REASONING LAYER                               │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                      Claude Code                             │    │    │
│  │  │    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐    │    │    │
│  │  │    │ Inbox         │ │ Task          │ │ Report        │    │    │    │
│  │  │    │ Processor     │ │ Planner       │ │ Generator     │    │    │    │
│  │  │    │ (Agent 1)     │ │ (Agent 2)     │ │ (Agent 3)     │    │    │    │
│  │  │    └───────────────┘ └───────────────┘ └───────────────┘    │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│              │                                                               │
│              ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     ⚡ ACTION LAYER [Silver Tier]                    │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │    │
│  │  │ [placeholder]   │  │ [placeholder]   │  │ [placeholder]   │      │    │
│  │  │ MCP: Email      │  │ MCP: Calendar   │  │ MCP: Database   │      │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│              │                                                               │
│              ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     👤 APPROVAL LAYER                                │    │
│  │                                                                      │    │
│  │       Human reviews Pending_Approval → moves to Approved             │    │
│  │       Human can override any decision at any stage                   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Sub-Agents

### Agent 1: Inbox Processor

**Purpose**: Triages incoming files and creates structured task records.

| Property | Value |
|----------|-------|
| **Skill** | `Skills/email_classifier.md` |
| **Reads** | `Inbox/`, `Skills/` |
| **Writes** | `Needs_Action/`, `Logs/` |
| **Triggers** | New file detected in `Inbox/` by `filesystem_watcher.py` |

**Behavior**:
1. Detects new file via watcher
2. Reads content and applies classification skill
3. Creates task file with YAML frontmatter in `Needs_Action/`
4. Logs activity to `Logs/watcher.log`

---

### Agent 2: Task Planner

**Purpose**: Analyzes tasks and creates execution plans.

| Property | Value |
|----------|-------|
| **Skill** | *(built-in reasoning)* |
| **Reads** | `Needs_Action/`, `Company_Handbook.md`, `Business_Goals.md` |
| **Writes** | `Plans/`, `Pending_Approval/`, `Dashboard.md` |
| **Triggers** | New task in `Needs_Action/` with `status: pending` |

**Behavior**:
1. Reads pending task and extracts requirements
2. Consults `Company_Handbook.md` for rules
3. Creates detailed plan in `Plans/`
4. If action requires approval → moves to `Pending_Approval/`
5. Updates `Dashboard.md` with task status

---

### Agent 3: Report Generator

**Purpose**: Produces summaries, updates metrics, and maintains documentation.

| Property | Value |
|----------|-------|
| **Skill** | *(built-in summarization)* |
| **Reads** | `Done/`, `Logs/`, `Business_Goals.md` |
| **Writes** | `Dashboard.md`, `Business_Goals.md`, `Logs/` |
| **Triggers** | Daily schedule, task completion, or on-demand request |

**Behavior**:
1. Aggregates completed tasks from `Done/`
2. Updates metrics in `Business_Goals.md`
3. Refreshes `Dashboard.md` status table
4. Generates periodic summary reports

---

## Data Flow

```
                    ┌─────────────┐
                    │  External   │
                    │   Input     │
                    │ (files/data)│
                    └──────┬──────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                          Inbox/                                   │
│                  (Landing zone for all inputs)                    │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           │ [Watcher detects]
                           │ [Agent 1 processes]
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                       Needs_Action/                               │
│              (Structured tasks awaiting processing)               │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           │ [Agent 2 creates plan]
                           ▼
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
┌───────────────────┐         ┌───────────────────┐
│      Plans/       │         │ Pending_Approval/ │
│ (Execution plans) │         │ (Needs human OK)  │
└─────────┬─────────┘         └─────────┬─────────┘
          │                             │
          │                             │ 👤 HUMAN REVIEWS
          │                             │
          │                             ▼
          │                   ┌───────────────────┐
          │                   │     Approved/     │
          │                   │ (Ready to execute)│
          │                   └─────────┬─────────┘
          │                             │
          └─────────────┬───────────────┘
                        │
                        │ [Execution complete]
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│                          Done/                                    │
│                  (Completed with notes)                           │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           │ [Agent 3 aggregates]
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                  Dashboard.md / Business_Goals.md                 │
│                     (Updated metrics & status)                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Human-in-the-Loop

### When Humans Must Intervene

Per `Company_Handbook.md`, human approval is **required** for:

| Action Type | Threshold | Flow |
|-------------|-----------|------|
| Financial transactions | Any amount >$0 | `Pending_Approval/` → Human → `Approved/` |
| External communications | Any outgoing | `Pending_Approval/` → Human → `Approved/` |
| Data deletion | Any permanent | `Pending_Approval/` → Human → `Approved/` |
| System changes | Config/install | `Pending_Approval/` → Human → `Approved/` |

### Approval Workflow

```
Task requires approval?
        │
        ├─── NO ──▶ Execute autonomously ──▶ Done/
        │
        └─── YES ─▶ Move to Pending_Approval/
                            │
                            ▼
                    Human reviews task
                            │
                    ┌───────┴───────┐
                    │               │
                    ▼               ▼
               APPROVED         REJECTED
                    │               │
                    ▼               ▼
           Move to Approved/   Return to Needs_Action/
                    │           (with feedback)
                    ▼
              Execute task
                    │
                    ▼
              Move to Done/
```

### Override Capability

Humans can intervene at **any stage**:
- Move files directly between folders
- Edit task files to change priority/status
- Cancel tasks by moving to `Done/` with `status: cancelled`
- Modify plans before execution

---

## File Ownership Map

### Write Permissions by Agent

| Folder                | Agent 1 (Inbox) | Agent 2 (Planner) | Agent 3 (Reports) | Human |
| --------------------- | :-------------: | :---------------: | :---------------: | :---: |
| `Inbox/`              |        ❌        |         ❌         |         ❌         |   ✅   |
| `Needs_Action/`       |   ✅ (create)    |    ✅ (update)     |         ❌         |   ✅   |
| `Pending_Approval/`   |        ❌        |    ✅ (move to)    |         ❌         |   ✅   |
| `Approved/`           |        ❌        |         ❌         |         ❌         |   ✅   |
| `Done/`               |        ❌        |    ✅ (move to)    |         ❌         |   ✅   |
| `Plans/`              |        ❌        |         ✅         |         ❌         |   ✅   |
| `Skills/`             |        ❌        |         ❌         |         ❌         |   ✅   |
| `Logs/`               |        ✅        |         ✅         |         ✅         |   ✅   |
| `Dashboard.md`        |        ❌        |         ✅         |         ✅         |   ✅   |
| `Business_Goals.md`   |        ❌        |         ❌         |         ✅         |   ✅   |
| `Company_Handbook.md` |        ❌        |         ❌         |         ❌         |   ✅   |
|                       |                 |                   |                   |       |

### Conflict Prevention Rules

1. **Single writer per task**: Only one agent operates on a task file at a time
2. **Status-based locking**: Task `status` field indicates current owner:
   - `pending` → Agent 1 finished, Agent 2 can claim
   - `planned` → Agent 2 finished, awaiting execution
   - `awaiting_approval` → Locked for human review
   - `approved` → Ready for execution
   - `in_progress` → Being executed
   - `done` → Closed, read-only

3. **Timestamp ordering**: Files processed in `received` order (FIFO)

4. **Folder atomicity**: Moving between folders = ownership transfer

---

## Future Enhancements (Silver/Gold Tiers)

| Tier | Enhancement | Impact |
|------|-------------|--------|
| Silver | MCP Email Server | Agent can send emails (with approval) |
| Silver | MCP Calendar Integration | Scheduling and reminders |
| Silver | MCP Database Connector | Persistent storage queries |
| Gold | Multi-agent coordination | Parallel task processing |
| Gold | Learning from feedback | Improve classification over time |

---

*Architecture document for AI Employee Vault v1.0*
