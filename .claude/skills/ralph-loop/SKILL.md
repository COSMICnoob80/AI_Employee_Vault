# Ralph Wiggum Task Loop

Process the vault task queue autonomously, routing approval-required items to human review.

## Triggers
- "run Ralph"
- "start task loop"
- "process task queue"
- "Ralph Wiggum"
- "stop Ralph"

## Instructions

### Start / Process Queue

When the user asks to run Ralph or process the task queue:

1. **Scan the queue** to see what's pending:
   ```bash
   python3 ~/AI_Employee_Vault/Scripts/ralph_loop.py --scan-only
   ```

2. **Review the manifest** at `Logs/ralph_queue.json` to understand the queue state.

3. **Process tasks** in priority order. Choose the appropriate mode:
   - **Dry run** (preview only): `python3 ~/AI_Employee_Vault/Scripts/ralph_loop.py --dry-run --once`
   - **Single pass**: `python3 ~/AI_Employee_Vault/Scripts/ralph_loop.py --once`
   - **Limited batch**: `python3 ~/AI_Employee_Vault/Scripts/ralph_loop.py --once --max N`
   - **Continuous loop**: `python3 ~/AI_Employee_Vault/Scripts/ralph_loop.py`

4. **Check for stop sentinel** between tasks: `ls ~/AI_Employee_Vault/.ralph_stop`

5. **Update Dashboard.md** after processing with current queue size and last run timestamp.

### Stop Ralph

When the user asks to stop Ralph:

1. Create the stop sentinel:
   ```bash
   touch ~/AI_Employee_Vault/.ralph_stop
   ```
   The loop will detect it on the next iteration, log "I'm in danger", and exit gracefully.

### Task Classification

Ralph classifies each task as:
- **autonomous**: File drops, manual tasks without external side effects -> archived to Done/
- **needs_approval**: Email sends, financial actions, social media posts -> routed to Pending_Approval/

### Queue Priority

Tasks are sorted by: priority (urgent > high > normal > low), has plan (+1), age (older first), type (email > file_drop > manual).

## Notes
- PID file: `ralph_loop.pid` (managed by schedule_watchers.sh)
- Queue manifest: `Logs/ralph_queue.json`
- Audit log: `Logs/audit.jsonl` (tool actions via PostToolUse hook)
- Activity log: `Logs/ralph_loop.log`
- Stop sentinel: `.ralph_stop` (touch to halt, auto-removed after stop)
