#!/usr/bin/env bash
# platinum_demo.sh — End-to-end Platinum tier demo orchestrator
#
# Demonstrates: "Email arrives while local offline → cloud drafts → local approves → local sends"
#
# Usage:
#   bash Scripts/platinum_demo.sh            # Interactive (pauses between steps)
#   bash Scripts/platinum_demo.sh --auto     # No pauses
#   bash Scripts/platinum_demo.sh --dry-run  # Preview only

set -euo pipefail

VAULT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="python3"
AUTO=false
DRY_RUN=false

for arg in "$@"; do
    case "$arg" in
        --auto)    AUTO=true ;;
        --dry-run) DRY_RUN=true ;;
    esac
done

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

step() {
    local num="$1"; shift
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Step $num:${NC} $*"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

pause() {
    if [[ "$AUTO" == "false" ]]; then
        echo ""
        echo -e "${YELLOW}Press Enter to continue...${NC}"
        read -r
    fi
}

cleanup_demo_files() {
    # Clean up demo artifacts only
    rm -f "$VAULT_ROOT/Inbox/EMAIL_PLATINUM_DEMO.md"
    rm -f "$VAULT_ROOT/Pending_Approval/cloud_draft_email_EMAIL_PLATINUM_DEMO.md"
    rm -f "$VAULT_ROOT/Pending_Approval/EMAIL_PLATINUM_DEMO.md"
    rm -f "$VAULT_ROOT/Approved/cloud_draft_email_EMAIL_PLATINUM_DEMO.md"
    rm -f "$VAULT_ROOT/Done/cloud_draft_email_EMAIL_PLATINUM_DEMO.md"
    rm -f "$VAULT_ROOT/In_Progress/cloud_agent/EMAIL_PLATINUM_DEMO.md"
    rm -f "$VAULT_ROOT/In_Progress/local_agent/cloud_draft_email_EMAIL_PLATINUM_DEMO.md"
}

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     PLATINUM TIER DEMO: Cloud/Local Split       ║${NC}"
echo -e "${GREEN}║                                                  ║${NC}"
echo -e "${GREEN}║  Demo gate: Email arrives while local offline    ║${NC}"
echo -e "${GREEN}║  → cloud drafts → local approves → local sends  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo "Mode: auto=$AUTO, dry_run=$DRY_RUN"

# ─── Step 1: Setup ───
step 1 "Setup directories, show initial state"

cleanup_demo_files
mkdir -p "$VAULT_ROOT/In_Progress/cloud_agent" \
         "$VAULT_ROOT/In_Progress/local_agent" \
         "$VAULT_ROOT/Updates" \
         "$VAULT_ROOT/Approved" \
         "$VAULT_ROOT/Done"

echo "Directory structure:"
echo "  In_Progress/cloud_agent/  ($(ls "$VAULT_ROOT/In_Progress/cloud_agent/" 2>/dev/null | wc -l) files)"
echo "  In_Progress/local_agent/  ($(ls "$VAULT_ROOT/In_Progress/local_agent/" 2>/dev/null | wc -l) files)"
echo "  Updates/                  ($(ls "$VAULT_ROOT/Updates/" 2>/dev/null | wc -l) files)"
echo "  Pending_Approval/         ($(ls "$VAULT_ROOT/Pending_Approval/" 2>/dev/null | wc -l) files)"
echo "  Approved/                 ($(ls "$VAULT_ROOT/Approved/" 2>/dev/null | wc -l) files)"

pause

# ─── Step 2: Drop test email ───
step 2 "Drop test email in Inbox/ (simulates email arrival while local is offline)"

cat > "$VAULT_ROOT/Inbox/EMAIL_PLATINUM_DEMO.md" << 'EMAILEOF'
---
type: email
action_type: email_send
from: client@example.com
subject: Q1 Report Review Request
priority: high
created: 2026-03-19
status: needs_action
---

# Q1 Report Review Request

Hi team,

Could you please review the attached Q1 report and provide feedback by end of week?

Key areas to focus on:
- Revenue projections vs actuals
- Customer acquisition costs
- Churn rate analysis

Best regards,
Client
EMAILEOF

echo -e "${GREEN}Email dropped:${NC} Inbox/EMAIL_PLATINUM_DEMO.md"
echo "  From: client@example.com"
echo "  Subject: Q1 Report Review Request"
echo "  Priority: high"

pause

# ─── Step 3: Cloud agent drafts ───
step 3 "Cloud agent scans and creates draft reply (local is 'offline')"

if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}[DRY-RUN]${NC} Would run: $PYTHON Scripts/cloud_agent.py --once"
    $PYTHON "$VAULT_ROOT/Scripts/cloud_agent.py" --once --dry-run
else
    $PYTHON "$VAULT_ROOT/Scripts/cloud_agent.py" --once
fi

pause

# ─── Step 4: Show draft ───
step 4 "Show draft in Pending_Approval/"

echo "Files in Pending_Approval/:"
ls -1 "$VAULT_ROOT/Pending_Approval/" 2>/dev/null | grep -E "cloud_draft|EMAIL_PLATINUM" || echo "  (none found)"

DRAFT_FILE="$VAULT_ROOT/Pending_Approval/cloud_draft_email_EMAIL_PLATINUM_DEMO.md"
if [[ -f "$DRAFT_FILE" ]]; then
    echo ""
    echo -e "${GREEN}Draft content (first 20 lines):${NC}"
    head -20 "$DRAFT_FILE"
else
    echo -e "${YELLOW}Draft file not found (expected in dry-run mode)${NC}"
fi

pause

# ─── Step 5: Local comes online ───
step 5 "Local agent comes online (zone separation demonstrated)"

echo "Scenario: Local machine was offline during email arrival."
echo "Cloud agent handled the draft. Now local agent comes online."
echo ""
echo "Cloud status:"
if [[ -f "$VAULT_ROOT/Updates/cloud_status.md" ]]; then
    head -15 "$VAULT_ROOT/Updates/cloud_status.md"
else
    echo "  (no status file — expected in dry-run mode)"
fi

pause

# ─── Step 6: Approve the draft ───
step 6 "Move draft to Approved/ (simulates human HITL approval)"

if [[ -f "$DRAFT_FILE" ]]; then
    mkdir -p "$VAULT_ROOT/Approved"
    cp "$DRAFT_FILE" "$VAULT_ROOT/Approved/"
    rm "$DRAFT_FILE"
    echo -e "${GREEN}Approved:${NC} cloud_draft_email_EMAIL_PLATINUM_DEMO.md"
    echo "  Moved from Pending_Approval/ -> Approved/"
else
    echo -e "${YELLOW}No draft to approve (dry-run mode)${NC}"
fi

pause

# ─── Step 7: Local agent executes ───
step 7 "Local agent processes approved draft"

if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}[DRY-RUN]${NC} Would run: $PYTHON Scripts/local_agent.py --once --dry-run"
    $PYTHON "$VAULT_ROOT/Scripts/local_agent.py" --once --dry-run
else
    $PYTHON "$VAULT_ROOT/Scripts/local_agent.py" --once --dry-run
fi

pause

# ─── Step 8: Show completion ───
step 8 "Show Done/ and audit log"

echo "Files in Done/:"
ls -1 "$VAULT_ROOT/Done/" 2>/dev/null | grep "cloud_draft" || echo "  (none — check In_Progress/)"

echo ""
echo "Recent audit entries (last 5):"
if [[ -f "$VAULT_ROOT/Logs/audit.jsonl" ]]; then
    tail -5 "$VAULT_ROOT/Logs/audit.jsonl" | while read -r line; do
        echo "  $line"
    done
else
    echo "  (no audit log)"
fi

pause

# ─── Step 9: Dashboard ───
step 9 "Show Dashboard Platinum section"

if grep -q "PLATINUM_STATUS_START" "$VAULT_ROOT/Dashboard.md" 2>/dev/null; then
    echo -e "${GREEN}Platinum section in Dashboard.md:${NC}"
    sed -n '/PLATINUM_STATUS_START/,/PLATINUM_STATUS_END/p' "$VAULT_ROOT/Dashboard.md"
else
    echo "Platinum section not yet in Dashboard (will appear after local agent runs)"
fi

# ─── Done ───
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          PLATINUM DEMO COMPLETE                  ║${NC}"
echo -e "${GREEN}║                                                  ║${NC}"
echo -e "${GREEN}║  Demonstrated:                                   ║${NC}"
echo -e "${GREEN}║  1. Claim-by-move coordination                   ║${NC}"
echo -e "${GREEN}║  2. Cloud drafts (never sends)                   ║${NC}"
echo -e "${GREEN}║  3. Single-writer Dashboard rule                 ║${NC}"
echo -e "${GREEN}║  4. HITL approval gate                           ║${NC}"
echo -e "${GREEN}║  5. Local execution + audit                      ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"

cleanup_demo_files
