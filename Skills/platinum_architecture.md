---
type: skill
name: Platinum Architecture
version: 1.0
created: 2026-03-19
---

# Platinum Architecture

## 1. Description

Cloud/Local work-zone split architecture for the AI Employee Vault Platinum tier. Two agents — a cloud agent (draft-only) and a local agent (approve+execute) — coordinate via claim-by-move file locking, single-writer Dashboard rule, and commit-based sync checkpoints. Secrets never leave the local zone.

## 2. Capabilities

- **Cloud Agent:** Scans Inbox/ and Needs_Action/ for unclaimed tasks, generates template-based drafts (email replies, social posts, accounting summaries), writes drafts to Pending_Approval/, writes own status to Updates/cloud_status.md
- **Local Agent:** Merges cloud status into Dashboard.md (sole Dashboard writer), scans Approved/ for cloud drafts, executes approved actions via MCP servers or dry-run logging, archives to Done/
- **Claim Manager:** Atomic claim-by-move coordination preventing duplicate processing across agents
- **Vault Sync:** Git-based commit checkpoints for cloud-push and local-pull operations
- **Demo Orchestrator:** End-to-end 9-step demo proving the full pipeline

## 3. Input

| Input | Source | Format |
|-------|--------|--------|
| New tasks | Inbox/*.md, Needs_Action/*.md | Markdown with YAML frontmatter |
| Approved drafts | Approved/cloud_draft_*.md | Markdown with approval_request frontmatter |
| Cloud status | Updates/cloud_status.md | Markdown with agent_status frontmatter |
| Stop signals | .cloud_stop, .local_stop | Empty sentinel files |

## 4. Output

| Output | Destination | Format |
|--------|------------|--------|
| Draft replies | Pending_Approval/cloud_draft_*.md | approval_request frontmatter |
| Cloud status | Updates/cloud_status.md | agent_status frontmatter |
| Executed results | Done/cloud_draft_*.md | Updated status: done |
| Dashboard section | Dashboard.md (PLATINUM_STATUS markers) | Markdown table |
| Audit trail | Logs/audit.jsonl | JSON Lines (task_claimed, task_released, etc.) |

## 5. Rules

1. **Cloud NEVER sends:** Cloud agent generates drafts only. No email sends, no social posts, no approvals.
2. **Single-writer Dashboard:** Only the local agent writes to Dashboard.md. Cloud writes to Updates/cloud_status.md.
3. **Claim-by-move:** Files are claimed by moving to In_Progress/{agent}/. No two agents process the same file.
4. **Secrets stay local:** Credentials, tokens, and .env files never sync to cloud. Cloud operates on markdown only.
5. **HITL gate preserved:** Cloud drafts go to Pending_Approval/. Human must move to Approved/ before local executes.
6. **Graceful shutdown:** Both agents honor stop sentinels (.cloud_stop, .local_stop) and SIGTERM/SIGINT.
7. **Dry-run support:** All scripts and agents support --dry-run for safe demo and testing.

## 6. Examples

### Email Pipeline (Demo Gate)
```
1. Email lands in Inbox/EMAIL_001.md
2. Cloud agent claims → In_Progress/cloud_agent/EMAIL_001.md
3. Cloud generates → Pending_Approval/cloud_draft_email_EMAIL_001.md
4. Cloud releases original → Pending_Approval/EMAIL_001.md
5. Human approves → moves cloud_draft to Approved/
6. Local agent claims → In_Progress/local_agent/cloud_draft_email_EMAIL_001.md
7. Local executes (MCP gmail-send or dry-run)
8. Local releases → Done/cloud_draft_email_EMAIL_001.md
```

### Running the Demo
```bash
# Full interactive demo
bash Scripts/platinum_demo.sh

# Automated (no pauses)
bash Scripts/platinum_demo.sh --auto

# Dry-run preview
bash Scripts/platinum_demo.sh --dry-run
```

### Individual Agent Commands
```bash
# Cloud agent — single pass
python Scripts/cloud_agent.py --once

# Local agent — dry run
python Scripts/local_agent.py --once --dry-run

# Sync status
bash Scripts/vault_sync.sh status
```

## 7. Integration

| Component | Interaction |
|-----------|------------|
| `Scripts/claim_manager.py` | Imported by both agents for claim/release |
| `Watchers/vault_audit.py` | Imported for audit_log(), safe_write(), ErrorTracker |
| `Scripts/ralph_loop.py` | Pattern source for loop control, PID, signals |
| `Watchers/approval_watcher.py` | Monitors Pending_Approval/ transitions |
| `Scripts/schedule_watchers.sh` | Manages cloud_agent and local_agent lifecycle |
| `Scripts/vault_sync.sh` | Git checkpoint management |
| `Dashboard.md` | Platinum section between HTML comment markers |
| `Logs/audit.jsonl` | All claim/release/draft/execute events logged |
