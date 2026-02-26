#!/usr/bin/env bash
# cron_setup.sh — Idempotent crontab installer for AI Employee Vault
# Supports: install | remove | status

set -euo pipefail

VAULT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCHEDULE_SCRIPT="$VAULT_ROOT/Scripts/schedule_watchers.sh"
TAG="# AI_Employee_Vault"

log() {
    local level="$1"; shift
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $*"
}

cmd_install() {
    # Check if already installed
    if crontab -l 2>/dev/null | grep -q "$TAG"; then
        log "INFO" "Cron entries already installed, skipping"
        cmd_status
        return 0
    fi

    local existing
    existing="$(crontab -l 2>/dev/null || true)"

    local new_entries
    new_entries="$(cat <<EOF
@reboot bash $SCHEDULE_SCRIPT start $TAG
*/5 * * * * bash $SCHEDULE_SCRIPT start $TAG
EOF
)"

    if [[ -n "$existing" ]]; then
        echo "$existing"$'\n'"$new_entries" | crontab -
    else
        echo "$new_entries" | crontab -
    fi

    log "INFO" "Cron entries installed successfully"
    cmd_status
}

cmd_remove() {
    if ! crontab -l 2>/dev/null | grep -q "$TAG"; then
        log "INFO" "No AI Employee cron entries found"
        return 0
    fi

    crontab -l 2>/dev/null | grep -v "$TAG" | crontab - || {
        # If all entries were ours, crontab might be empty
        crontab -r 2>/dev/null || true
    }

    log "INFO" "Cron entries removed"
}

cmd_status() {
    echo "AI Employee Vault cron entries:"
    echo "--------------------------------"
    local entries
    entries="$(crontab -l 2>/dev/null | grep "$TAG" || true)"
    if [[ -z "$entries" ]]; then
        echo "  (none installed)"
    else
        echo "$entries" | sed 's/^/  /'
    fi
}

case "${1:-status}" in
    install) cmd_install ;;
    remove)  cmd_remove ;;
    status)  cmd_status ;;
    *)
        echo "Usage: $0 {install|remove|status}"
        exit 1
        ;;
esac
