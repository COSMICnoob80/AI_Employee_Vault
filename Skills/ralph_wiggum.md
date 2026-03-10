# Ralph Wiggum Task Loop Skill

## Description
Persistent autonomous task execution loop that scans the vault's task queue, prioritizes work by urgency and age, classifies tasks as autonomous or approval-required, executes safe tasks directly, routes sensitive actions to human review, verifies completion with a 3-point check, and reports results via audit logging.

## Capabilities
- Scan Needs_Action/ and Plans/ directories to build a prioritized task queue
- Score tasks by priority (urgent=3, high=2, normal=1, low=0) with tiebreakers for plan availability, age, and type
- Classify tasks as autonomous (safe to execute) or needs_approval (requires human review)
- Execute autonomous tasks by updating status and archiving to Done/
- Route approval-required tasks to Pending_Approval/ for human review
- Verify completion with 3-point check: status updated, plan checkboxes checked, file in Done/
- Write queue manifests to Logs/ralph_queue.json for inspection
- Log all actions to Logs/audit.jsonl via PostToolUse hooks
- Graceful shutdown via .ralph_stop sentinel file

## Input Format
CLI invocation with optional flags:
```bash
# Continuous loop (30s interval)
python Scripts/ralph_loop.py

# Single iteration
python Scripts/ralph_loop.py --once

# Scan only (produce manifest, no execution)
python Scripts/ralph_loop.py --scan-only

# Dry run (classify without executing)
python Scripts/ralph_loop.py --dry-run

# Process at most N tasks
python Scripts/ralph_loop.py --max 5
```

Stop the loop:
```bash
touch .ralph_stop
```

## Output Format
- **Queue manifest**: `Logs/ralph_queue.json` — JSON with task list, priorities, classifications
- **Audit events**: `Logs/audit.jsonl` — JSON Lines with ralph_start, ralph_scan, task_completed, task_routed_approval, ralph_stop events
- **Activity log**: `Logs/ralph_loop.log` — Human-readable log with timestamps
- **Completed tasks**: Moved to `Done/` with `status: done` in frontmatter
- **Approval-routed tasks**: Moved to `Pending_Approval/` with `status: pending_approval`

## Rules

### Classification
1. Tasks with action_type in {email_send, financial, social_media, linkedin_post, payment, subscription, external_api, delete} require approval
2. Email-type tasks always require approval (external communication)
3. Tasks with `requires_approval: true` in frontmatter always require approval
4. All other tasks are autonomous and can be executed without human review

### Execution
1. Autonomous tasks: update frontmatter status to `done`, move file to Done/, move associated plan if exists
2. Approval tasks: update frontmatter status to `pending_approval`, move to Pending_Approval/
3. Re-scan the queue each iteration to handle concurrent modifications
4. Use safe_write() for atomic file operations
5. Circuit breaker trips after 10 errors in 5 minutes, 60s cooldown

### Stop Mechanism
1. `.ralph_stop` sentinel file checked at start of each iteration and between tasks
2. When detected: log "I'm in danger" audit event, write final queue state, remove sentinel, exit 0
3. SIGTERM/SIGINT also trigger graceful shutdown

## Examples

### Example 1: Scan Queue
```bash
python Scripts/ralph_loop.py --scan-only
```
Output: `Logs/ralph_queue.json` with 27 tasks sorted by priority.

### Example 2: Dry Run
```bash
python Scripts/ralph_loop.py --dry-run --once
```
Logs classification for each task without moving any files.

### Example 3: Process Top 5
```bash
python Scripts/ralph_loop.py --once --max 5
```
Processes 5 highest-priority tasks, archiving autonomous ones and routing approval-required ones.

### Example 4: Stop Running Loop
```bash
touch .ralph_stop
```
Loop detects sentinel, logs shutdown, removes sentinel, exits.

## Integration
- Uses [[vault_audit]] shared infrastructure (audit_log, safe_write, ErrorTracker)
- Feeds [[approval_requester]] workflow by routing tasks to Pending_Approval/
- Managed by [[scheduler]] via schedule_watchers.sh start/stop/status
- PostToolUse hook logs all Claude Code tool actions to audit.jsonl
- Updates [[Dashboard]] Ralph Wiggum status section
- Queue manifest at Logs/ralph_queue.json readable by [[ceo_briefing]]
