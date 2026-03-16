#!/usr/bin/env bash
# schedule_watchers.sh — Master launcher for AI Employee Vault watchers
# Supports: start | stop | status
# PID files stored at vault root, logs to Logs/scheduler.log

set -euo pipefail

# Explicit PATH for cron compatibility
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

VAULT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$VAULT_ROOT/Logs"
LOG_FILE="$LOG_DIR/scheduler.log"
PYTHON="python3"

WATCHERS=(filesystem_watcher gmail_watcher approval_watcher linkedin_poster ralph_loop social_poster)

mkdir -p "$LOG_DIR"

log() {
    local level="$1"; shift
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $*" | tee -a "$LOG_FILE"
}

pid_file() {
    echo "$VAULT_ROOT/${1}.pid"
}

is_alive() {
    local pf
    pf="$(pid_file "$1")"
    if [[ -f "$pf" ]]; then
        local pid
        pid="$(cat "$pf")"
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
        # Stale PID file — clean up
        rm -f "$pf"
    fi
    return 1
}

start_watcher() {
    local name="$1"
    local script="$VAULT_ROOT/Watchers/${name}.py"
    # Fallback to Scripts/ directory
    if [[ ! -f "$script" ]]; then
        script="$VAULT_ROOT/Scripts/${name}.py"
    fi

    if is_alive "$name"; then
        local pid
        pid="$(cat "$(pid_file "$name")")"
        log "INFO" "$name already running (PID $pid), skipping"
        return 0
    fi

    # Gmail special case: skip if credentials missing
    if [[ "$name" == "gmail_watcher" ]] && [[ ! -f "$VAULT_ROOT/credentials.json" ]]; then
        log "WARN" "$name skipped — credentials.json not found"
        return 0
    fi

    # LinkedIn special case: skip if no saved session
    if [[ "$name" == "linkedin_poster" ]] && [[ ! -f "$VAULT_ROOT/.linkedin_session/state.json" ]]; then
        log "WARN" "$name skipped — no session (run manually first)"
        return 0
    fi

    # Social poster special case: skip if no social sessions exist
    if [[ "$name" == "social_poster" ]]; then
        local has_session=false
        for platform_dir in "$VAULT_ROOT/.social_sessions"/*/; do
            if [[ -f "${platform_dir}state.json" ]]; then
                has_session=true
                break
            fi
        done
        if [[ "$has_session" == "false" ]]; then
            log "WARN" "$name skipped — no social sessions (run manually first per platform)"
            return 0
        fi
    fi

    if [[ ! -f "$script" ]]; then
        log "ERROR" "$name script not found: $script"
        return 1
    fi

    $PYTHON "$script" >> "$LOG_DIR/${name}.log" 2>&1 &
    local pid=$!
    echo "$pid" > "$(pid_file "$name")"
    log "INFO" "$name started (PID $pid)"
}

stop_watcher() {
    local name="$1"
    local pf
    pf="$(pid_file "$name")"

    if ! is_alive "$name"; then
        log "INFO" "$name not running"
        rm -f "$pf"
        return 0
    fi

    local pid
    pid="$(cat "$pf")"
    kill "$pid" 2>/dev/null || true
    # Wait briefly for graceful shutdown
    for i in 1 2 3 4 5; do
        if ! kill -0 "$pid" 2>/dev/null; then
            break
        fi
        sleep 1
    done
    rm -f "$pf"
    log "INFO" "$name stopped (was PID $pid)"
}

cmd_start() {
    log "INFO" "=== Starting watchers ==="
    for w in "${WATCHERS[@]}"; do
        start_watcher "$w"
    done
    log "INFO" "=== Startup complete ==="
}

cmd_stop() {
    log "INFO" "=== Stopping watchers ==="
    for w in "${WATCHERS[@]}"; do
        stop_watcher "$w"
    done
    log "INFO" "=== All watchers stopped ==="
}

cmd_status() {
    printf "%-22s %-10s %s\n" "WATCHER" "STATUS" "PID"
    printf "%-22s %-10s %s\n" "-------" "------" "---"
    for w in "${WATCHERS[@]}"; do
        if is_alive "$w"; then
            local pid
            pid="$(cat "$(pid_file "$w")")"
            printf "%-22s %-10s %s\n" "$w" "running" "$pid"
        else
            printf "%-22s %-10s %s\n" "$w" "stopped" "-"
        fi
    done
}

case "${1:-start}" in
    start)  cmd_start ;;
    stop)   cmd_stop ;;
    status) cmd_status ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac
