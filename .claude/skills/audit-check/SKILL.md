# Audit Health Check

Verify audit log integrity, watcher health, and error patterns.

## Triggers
- "check audit log"
- "audit health check"
- "verify watchers"
- "watcher error report"
- "audit status"

## Instructions

When the user asks for an audit health check:

1. **Validate audit log integrity** - Read `Logs/audit.jsonl` and verify every line is valid JSON. Report total lines, any malformed entries, and the time range covered.

2. **Summarize events** - Count events grouped by `event` type and `source` for the last 24 hours. Present as a table.

3. **Error analysis** - Filter entries where `status` is `"error"`. Group by source and show:
   - Total error count per source
   - Most recent error message
   - Whether circuit breaker was tripped

4. **Watcher health** - Check PID files and process status:
   ```bash
   cd ~/AI_Employee_Vault && for pid in *.pid; do echo "$pid: $(cat "$pid") — $(ps -p $(cat "$pid") -o comm= 2>/dev/null || echo 'NOT RUNNING')"; done
   ```

5. **Report summary** - Output a markdown summary with:
   - Audit log: total entries, date range, integrity status
   - Events: table of event counts by source (last 24h)
   - Errors: count, patterns, circuit breaker status
   - Watchers: running/stopped status per watcher

## Notes
- This skill is read-only; it never modifies the audit log
- If `Logs/audit.jsonl` does not exist, report that audit logging has not yet generated any entries
- Large audit files: only read the last 500 lines for the 24h analysis
