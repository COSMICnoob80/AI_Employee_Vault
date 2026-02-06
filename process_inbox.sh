#!/bin/bash
# Process Inbox - Batch planning for AI Employee Vault
# Runs the orchestration script to plan all pending tasks
#
# Usage:
#   ./process_inbox.sh            # Live mode
#   ./process_inbox.sh --dry-run  # Preview only

VAULT_DIR="$HOME/AI_Employee_Vault"

echo "=================================="
echo "AI Employee Vault - Batch Planner"
echo "=================================="

# Count pending tasks
PENDING=$(grep -rl 'status: pending' "$VAULT_DIR/Needs_Action/" 2>/dev/null | wc -l)
echo "Pending tasks found: $PENDING"

if [ "$PENDING" -eq 0 ]; then
    echo "No pending tasks. Exiting."
    exit 0
fi

echo "Starting orchestrator..."
python3 "$VAULT_DIR/orchestrate_planning.py" "$@"

echo ""
echo "=== Summary ==="
echo "Plans dir: $(ls "$VAULT_DIR/Plans/"*.md 2>/dev/null | wc -l) files"
echo "Needs_Action: $(ls "$VAULT_DIR/Needs_Action/"*.md 2>/dev/null | wc -l) files"
echo "Done."
