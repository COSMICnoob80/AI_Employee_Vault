#!/usr/bin/env bash
# AEWACS Command Center — start/stop/status for API + Web servers.
# Usage: bash Scripts/start_dashboard.sh {start|stop|status}

set -euo pipefail

VAULT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_DIR="$VAULT_ROOT/Dashboard/api"
WEB_DIR="$VAULT_ROOT/Dashboard/web"
LOG_DIR="$VAULT_ROOT/Logs"
LOG_FILE="$LOG_DIR/dashboard.log"
VENV_DIR="$API_DIR/.venv"
PYTHON="$VENV_DIR/bin/python3"

API_PID_FILE="$VAULT_ROOT/dashboard_api.pid"
WEB_PID_FILE="$VAULT_ROOT/dashboard_web.pid"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

is_alive() {
    local pf="$1"
    if [[ -f "$pf" ]]; then
        local pid
        pid="$(cat "$pf")"
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
        rm -f "$pf"
    fi
    return 1
}

do_start() {
    mkdir -p "$LOG_DIR"

    # ── API server ───────────────────────────────────────
    if is_alive "$API_PID_FILE"; then
        log "API already running (PID $(cat "$API_PID_FILE"))"
    else
        # Create venv if missing
        if [[ ! -f "$PYTHON" ]]; then
            log "Creating Python venv..."
            uv venv "$VENV_DIR" 2>>"$LOG_FILE"
        fi
        log "Installing Python dependencies..."
        uv pip install --python "$PYTHON" -q -r "$API_DIR/requirements.txt" 2>>"$LOG_FILE"

        log "Starting Flask API on :5001..."
        cd "$API_DIR"
        $PYTHON server.py >> "$LOG_FILE" 2>&1 &
        local api_pid=$!
        echo "$api_pid" > "$API_PID_FILE"
        cd "$VAULT_ROOT"
        log "API started (PID $api_pid)"
    fi

    # ── Web dev server ───────────────────────────────────
    if is_alive "$WEB_PID_FILE"; then
        log "Web already running (PID $(cat "$WEB_PID_FILE"))"
    else
        if [[ ! -d "$WEB_DIR/node_modules" ]]; then
            log "Installing npm dependencies..."
            cd "$WEB_DIR"
            npm install --silent 2>>"$LOG_FILE"
            cd "$VAULT_ROOT"
        fi

        log "Starting Vite dev server on :5173..."
        cd "$WEB_DIR"
        npx vite --host 127.0.0.1 >> "$LOG_FILE" 2>&1 &
        local web_pid=$!
        echo "$web_pid" > "$WEB_PID_FILE"
        cd "$VAULT_ROOT"
        log "Web started (PID $web_pid)"
    fi

    echo ""
    echo "AEWACS Command Center running:"
    echo "  API  → http://localhost:5001"
    echo "  Web  → http://localhost:5173"
}

do_stop() {
    for label_pid in "API:$API_PID_FILE" "Web:$WEB_PID_FILE"; do
        local label="${label_pid%%:*}"
        local pf="${label_pid##*:}"

        if ! is_alive "$pf"; then
            log "$label not running"
            continue
        fi

        local pid
        pid="$(cat "$pf")"
        kill "$pid" 2>/dev/null || true
        for _ in 1 2 3 4 5; do
            kill -0 "$pid" 2>/dev/null || break
            sleep 1
        done
        rm -f "$pf"
        log "$label stopped (was PID $pid)"
    done
}

do_status() {
    echo "AEWACS Command Center Status"
    echo "────────────────────────────"
    for label_pid in "API:$API_PID_FILE" "Web:$WEB_PID_FILE"; do
        local label="${label_pid%%:*}"
        local pf="${label_pid##*:}"
        if is_alive "$pf"; then
            echo "  $label: RUNNING (PID $(cat "$pf"))"
        else
            echo "  $label: STOPPED"
        fi
    done
}

case "${1:-}" in
    start)  do_start ;;
    stop)   do_stop ;;
    status) do_status ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac
