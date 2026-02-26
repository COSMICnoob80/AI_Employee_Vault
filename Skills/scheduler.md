# Scheduler Skill

## Description
Manages automated startup, self-healing, and cron integration for AI Employee Vault watchers. Ensures all watchers (filesystem, Gmail, approval) run unattended with PID-file guards, graceful shutdown, and idempotent cron scheduling.

## Capabilities
- Start all watchers with PID-file deduplication (no double-launches)
- Stop watchers gracefully via SIGTERM (matches Python KeyboardInterrupt handlers)
- Report live status of all watchers with PID details
- Self-heal crashed watchers via 5-minute cron keep-alive
- Skip Gmail watcher gracefully when credentials are missing
- Install/remove cron entries idempotently using comment tags
- Log all scheduler actions to `Logs/scheduler.log`

## Input Format
```
Command: {start | stop | status}
Target: {all | filesystem_watcher | gmail_watcher | approval_watcher}
```

## Output Format
```
Action: [What was done]
Watchers: [List of affected watchers and their states]
Log: [Path to scheduler log]
```

## Rules

### Starting Watchers
1. Always check PID file before launching — skip if process is alive (`kill -0`)
2. Clean up stale PID files when process is no longer running
3. Gmail watcher requires `credentials.json` at vault root — skip with warning if missing
4. Each watcher logs to its own file: `Logs/<watcher_name>.log`
5. PID files are stored at vault root: `<watcher_name>.pid`

### Stopping Watchers
1. Send SIGTERM for graceful shutdown (Python watchers handle KeyboardInterrupt)
2. Wait up to 5 seconds for graceful exit before giving up
3. Always remove PID file after stop, even if process was already gone
4. Log each stop action with the previous PID

### Cron Management
1. Use `# AI_Employee_Vault` comment tag to identify managed entries
2. Never duplicate entries — check for tag before installing
3. Install two entries: `@reboot` (startup) and `*/5 * * * *` (keep-alive)
4. Remove only tagged entries — never touch other cron jobs
5. Show current status after install/remove operations

### Health & Self-Healing
1. The 5-minute cron job calls `schedule_watchers.sh start`
2. `start` is idempotent — only launches watchers that aren't already running
3. If a watcher crashes, next cron cycle restarts it automatically
4. All health actions are logged to `Logs/scheduler.log`

## Examples

### Example 1: Start All Watchers
**Input:**
```
bash Scripts/schedule_watchers.sh start
```

**Output:**
```
2026-02-26 10:00:00 [INFO] === Starting watchers ===
2026-02-26 10:00:00 [INFO] filesystem_watcher started (PID 12345)
2026-02-26 10:00:00 [INFO] gmail_watcher started (PID 12346)
2026-02-26 10:00:01 [INFO] approval_watcher started (PID 12347)
2026-02-26 10:00:01 [INFO] === Startup complete ===
```

### Example 2: Check Status
**Input:**
```
bash Scripts/schedule_watchers.sh status
```

**Output:**
```
WATCHER                STATUS     PID
-------                ------     ---
filesystem_watcher     running    12345
gmail_watcher          running    12346
approval_watcher       running    12347
```

### Example 3: Gmail Credentials Missing
**Input:**
```
bash Scripts/schedule_watchers.sh start
```

**Output:**
```
2026-02-26 10:00:00 [INFO] === Starting watchers ===
2026-02-26 10:00:00 [INFO] filesystem_watcher started (PID 12345)
2026-02-26 10:00:00 [WARN] gmail_watcher skipped — credentials.json not found
2026-02-26 10:00:01 [INFO] approval_watcher started (PID 12347)
2026-02-26 10:00:01 [INFO] === Startup complete ===
```

### Example 4: Install Cron
**Input:**
```
bash Scripts/cron_setup.sh install
```

**Output:**
```
2026-02-26 10:05:00 [INFO] Cron entries installed successfully
AI Employee Vault cron entries:
--------------------------------
  @reboot bash /home/user/AI_Employee_Vault/Scripts/schedule_watchers.sh start # AI_Employee_Vault
  */5 * * * * bash /home/user/AI_Employee_Vault/Scripts/schedule_watchers.sh start # AI_Employee_Vault
```

## Integration

- Updates [[Dashboard]] Scheduler Status section
- Follows [[Company_Handbook]] guidelines for automated actions
- Manages [[filesystem_watcher]], [[gmail_watcher]], and [[approval_watcher]]
- Logs to `Logs/scheduler.log` in standard vault logging format
