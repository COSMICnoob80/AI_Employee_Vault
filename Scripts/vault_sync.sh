#!/usr/bin/env bash
# vault_sync.sh — Git-based sync simulation for Platinum cloud/local split
#
# Simplified commit-based checkpoints (both agents share same filesystem).
#
# Usage:
#   bash Scripts/vault_sync.sh cloud-push [--dry-run]
#   bash Scripts/vault_sync.sh local-pull  [--dry-run]
#   bash Scripts/vault_sync.sh status

set -euo pipefail

VAULT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$VAULT_ROOT/Logs"
LOG_FILE="$LOG_DIR/vault_sync.log"
DRY_RUN=false

mkdir -p "$LOG_DIR"

log() {
    local level="$1"; shift
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $*" | tee -a "$LOG_FILE"
}

# Parse --dry-run from any position
for arg in "$@"; do
    if [[ "$arg" == "--dry-run" ]]; then
        DRY_RUN=true
    fi
done

cmd_cloud_push() {
    log "INFO" "=== Cloud Push: staging cloud agent outputs ==="

    cd "$VAULT_ROOT"

    # Stage cloud-owned paths
    local files_to_add=(
        "Updates/"
        "Pending_Approval/cloud_draft_*"
        "In_Progress/cloud_agent/"
    )

    local staged=0
    for pattern in "${files_to_add[@]}"; do
        # shellcheck disable=SC2086
        if compgen -G "$pattern" > /dev/null 2>&1; then
            if [[ "$DRY_RUN" == "true" ]]; then
                log "INFO" "[DRY-RUN] Would stage: $pattern"
            else
                git add $pattern 2>/dev/null || true
            fi
            ((staged++)) || true
        fi
    done

    if [[ "$staged" -eq 0 ]]; then
        log "INFO" "Nothing to push — no cloud agent outputs found"
        return 0
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY-RUN] Would commit cloud checkpoint"
        git status --short Updates/ Pending_Approval/ In_Progress/cloud_agent/ 2>/dev/null || true
    else
        local ts
        ts="$(date '+%Y%m%d_%H%M%S')"
        if git diff --cached --quiet 2>/dev/null; then
            log "INFO" "No staged changes to commit"
        else
            git commit -m "cloud-push checkpoint $ts" 2>/dev/null || true
            log "INFO" "Cloud checkpoint committed: $ts"
        fi
    fi
}

cmd_local_pull() {
    log "INFO" "=== Local Pull: syncing from cloud ==="

    cd "$VAULT_ROOT"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY-RUN] Would pull latest changes"
        log "INFO" "(Single-dir simulation — no actual pull needed)"
    else
        # In single-dir mode, this is a no-op
        # In real deployment, this would be: git pull --ff-only
        log "INFO" "Single-directory mode — sync is implicit"
    fi

    # Show what's available from cloud
    log "INFO" "Cloud status file:"
    if [[ -f "$VAULT_ROOT/Updates/cloud_status.md" ]]; then
        head -15 "$VAULT_ROOT/Updates/cloud_status.md"
    else
        log "INFO" "  (no cloud status yet)"
    fi

    log "INFO" "Cloud drafts in Pending_Approval/:"
    # shellcheck disable=SC2086
    if compgen -G "$VAULT_ROOT/Pending_Approval/cloud_draft_*" > /dev/null 2>&1; then
        ls -1 "$VAULT_ROOT/Pending_Approval/cloud_draft_"* 2>/dev/null | while read -r f; do
            log "INFO" "  $(basename "$f")"
        done
    else
        log "INFO" "  (none)"
    fi
}

cmd_status() {
    log "INFO" "=== Vault Sync Status ==="

    cd "$VAULT_ROOT"

    echo ""
    echo "Cloud Agent Outputs:"
    echo "  Updates/cloud_status.md: $([ -f Updates/cloud_status.md ] && echo 'exists' || echo 'missing')"
    echo "  In_Progress/cloud_agent/: $(ls In_Progress/cloud_agent/ 2>/dev/null | wc -l) files"
    echo ""
    echo "Local Agent Outputs:"
    echo "  In_Progress/local_agent/: $(ls In_Progress/local_agent/ 2>/dev/null | wc -l) files"
    echo ""
    echo "Pending Cloud Drafts:"
    # shellcheck disable=SC2086
    if compgen -G "Pending_Approval/cloud_draft_*" > /dev/null 2>&1; then
        ls -1 Pending_Approval/cloud_draft_* 2>/dev/null
    else
        echo "  (none)"
    fi
    echo ""
    echo "Approved Cloud Drafts:"
    # shellcheck disable=SC2086
    if compgen -G "Approved/cloud_draft_*" > /dev/null 2>&1; then
        ls -1 Approved/cloud_draft_* 2>/dev/null
    else
        echo "  (none)"
    fi
    echo ""
    echo "Done Cloud Drafts:"
    # shellcheck disable=SC2086
    if compgen -G "Done/cloud_draft_*" > /dev/null 2>&1; then
        ls -1 Done/cloud_draft_* 2>/dev/null
    else
        echo "  (none)"
    fi
}

case "${1:-status}" in
    cloud-push)  cmd_cloud_push ;;
    local-pull)  cmd_local_pull ;;
    status)      cmd_status ;;
    *)
        echo "Usage: $0 {cloud-push|local-pull|status} [--dry-run]"
        exit 1
        ;;
esac
