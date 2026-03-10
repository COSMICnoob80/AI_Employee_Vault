#!/usr/bin/env bash
# ralph_hooks.sh — PostToolUse hook for Claude Code
# Logs every tool action to Logs/audit.jsonl in vault_audit.py format.
# Reads JSON from stdin: {"tool_name": "...", "tool_input": {...}}

set -euo pipefail

VAULT_ROOT="${HOME}/AI_Employee_Vault"
AUDIT_LOG="${VAULT_ROOT}/Logs/audit.jsonl"

mkdir -p "$(dirname "$AUDIT_LOG")"

# Read stdin (Claude Code passes tool use JSON)
INPUT="$(cat)"

# Extract tool_name (simple jq or fallback)
if command -v jq &>/dev/null; then
    TOOL_NAME="$(echo "$INPUT" | jq -r '.tool_name // "unknown"' 2>/dev/null || echo "unknown")"
    TOOL_INPUT="$(echo "$INPUT" | jq -c '.tool_input // {}' 2>/dev/null | head -c 200)"
else
    # Fallback: grep-based extraction
    TOOL_NAME="$(echo "$INPUT" | grep -oP '"tool_name"\s*:\s*"\K[^"]+' 2>/dev/null || echo "unknown")"
    TOOL_INPUT="$(echo "$INPUT" | head -c 200)"
fi

TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')"

# Build JSON line matching vault_audit.py format
ENTRY=$(printf '{"ts":"%s","event":"tool_use","source":"ralph_hook","details":{"tool":"%s","input_preview":"%s"},"status":"ok"}\n' \
    "$TIMESTAMP" \
    "$TOOL_NAME" \
    "$(echo "$TOOL_INPUT" | sed 's/"/\\"/g' | head -c 200)")

# Append with file locking (flock)
(
    flock -x 200
    echo "$ENTRY" >> "$AUDIT_LOG"
) 200>>"$AUDIT_LOG"
