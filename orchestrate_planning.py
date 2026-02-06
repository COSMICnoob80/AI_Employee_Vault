#!/usr/bin/env python3
"""
Task Planning Orchestrator for AI Employee Vault

Scans /Needs_Action for unplanned tasks and generates Plan.md files
in /Plans with actionable steps, time estimates, and wikilinks.

Usage:
    python3 orchestrate_planning.py          # Process all pending tasks
    python3 orchestrate_planning.py --dry-run  # Preview without writing
"""

import sys
import logging
import re
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path.home() / "AI_Employee_Vault"
NEEDS_ACTION_DIR = VAULT_ROOT / "Needs_Action"
PLANS_DIR = VAULT_ROOT / "Plans"
DONE_DIR = VAULT_ROOT / "Done"
LOG_DIR = VAULT_ROOT / "Logs"
DASHBOARD_PATH = VAULT_ROOT / "Dashboard.md"

# Setup logging
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "planning.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Keywords for plan step generation
RESPONSE_KEYWORDS = ["reply", "respond", "answer", "confirm", "approve", "review"]
FINANCIAL_KEYWORDS = ["invoice", "payment", "receipt", "billing", "subscription", "charge"]
URGENT_KEYWORDS = ["urgent", "asap", "critical", "immediate", "deadline"]


def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown content."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return {}
    meta = {}
    for line in match.group(1).strip().split('\n'):
        if ':' in line:
            key, _, val = line.partition(':')
            val = val.strip().strip('"').strip("'")
            meta[key.strip()] = val
    return meta


def extract_title(content: str) -> str:
    """Extract title from first markdown heading."""
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    return match.group(1).strip() if match else "Untitled Task"


def estimate_time(task_type: str, priority: str, content_lower: str) -> int:
    """Estimate time in minutes based on task type and content."""
    if task_type == "email":
        if any(kw in content_lower for kw in FINANCIAL_KEYWORDS):
            return 15
        if any(kw in content_lower for kw in RESPONSE_KEYWORDS):
            return 20
        return 5
    if task_type == "file_drop":
        return 15
    return 30


def generate_steps(task_type: str, priority: str, content_lower: str, title: str) -> list:
    """Generate action steps based on task type and content."""
    steps = []

    if task_type == "email":
        needs_response = any(kw in content_lower for kw in RESPONSE_KEYWORDS)
        is_financial = any(kw in content_lower for kw in FINANCIAL_KEYWORDS)

        steps.append("Review email content and assess required action")

        if is_financial:
            steps.append("Log financial details in [[Business_Goals]]")
            steps.append("Verify amounts and payment status")
        elif needs_response:
            steps.append("Draft response to sender")
            steps.append("Review draft (approval required per [[Company_Handbook]])")
        else:
            steps.append("Extract any actionable information")

        steps.append("Archive email task to /Done")
        steps.append(f"Verify: {title} fully processed, no pending actions")

    elif task_type == "file_drop":
        steps.append("Read and understand file content")
        steps.append("Categorize file (use [[email_classifier]] if applicable)")
        steps.append("Process content and take required action")
        steps.append("Archive to /Done with completion note")
        steps.append(f"Verify: File processed, [[Dashboard]] updated")

    else:
        steps.append("Review task context and requirements")
        steps.append("Identify dependencies and blockers")
        steps.append("Execute primary action")
        steps.append("Archive to /Done when complete")
        steps.append(f"Verify: Task objectives met")

    # Cap at 5 steps
    return steps[:5]


def create_plan(task_path: Path, dry_run: bool = False) -> bool:
    """Create a plan for a single task file."""
    content = task_path.read_text(encoding='utf-8')
    meta = parse_frontmatter(content)

    # Skip already planned tasks
    status = meta.get('status', 'pending')
    if status != 'pending':
        logger.info(f"Skipping {task_path.name} (status: {status})")
        return False

    task_type = meta.get('type', 'manual')
    priority = meta.get('priority', 'normal')
    title = extract_title(content)
    content_lower = content.lower()

    est_time = estimate_time(task_type, priority, content_lower)
    steps = generate_steps(task_type, priority, content_lower, title)
    task_stem = task_path.stem

    # Generate plan filename
    plan_filename = f"PLAN_{task_stem}.md"
    plan_path = PLANS_DIR / plan_filename

    # Skip if plan already exists
    if plan_path.exists():
        logger.info(f"Plan already exists: {plan_filename}")
        return False

    timestamp = datetime.now()

    # Build steps markdown
    steps_md = "\n".join(f"- [ ] Step {i+1}: {s}" for i, s in enumerate(steps))

    # Determine notes based on priority
    notes = ""
    if priority in ("urgent", "high"):
        notes = "High priority — complete within same day."
    elif any(kw in content_lower for kw in FINANCIAL_KEYWORDS):
        notes = "Financial item — track in [[Business_Goals]]."

    plan_content = f"""---
type: plan
source_task: "{task_path.name}"
created: {timestamp.isoformat()}
estimated_time: {est_time}
priority: {priority}
status: active
---

# Plan: {title}

## Source
[[{task_stem}]]

## Steps
{steps_md}

## Estimated Time
{est_time} minutes

## Notes
{notes if notes else 'Standard processing.'}

## On Completion
- Move source task to /Done
- Update [[Dashboard]]
"""

    if dry_run:
        logger.info(f"[DRY-RUN] Would create: {plan_filename} ({est_time} min, {len(steps)} steps)")
        return True

    # Write plan
    plan_path.write_text(plan_content, encoding='utf-8')
    logger.info(f"Plan created: {plan_filename} ({est_time} min, {len(steps)} steps)")

    # Update source task status
    updated = content.replace('status: pending', 'status: planned')
    # Add plan_ref if not present
    if 'plan_ref' not in updated:
        updated = updated.replace(
            f'status: planned',
            f'status: planned\nplan_ref: "[[PLAN_{task_stem}]]"'
        )
    task_path.write_text(updated, encoding='utf-8')
    logger.info(f"Updated task status: {task_path.name} → planned")

    return True


def update_dashboard():
    """Update Dashboard.md with planning statistics."""
    if not DASHBOARD_PATH.exists():
        return

    # Count tasks and plans
    pending = sum(1 for f in NEEDS_ACTION_DIR.glob('*.md')
                  if 'status: pending' in f.read_text())
    planned = sum(1 for f in NEEDS_ACTION_DIR.glob('*.md')
                  if 'status: planned' in f.read_text())
    active_plans = sum(1 for f in PLANS_DIR.glob('*.md')
                       if 'status: active' in f.read_text())

    content = DASHBOARD_PATH.read_text()

    section = f"""## Planning Status

| Metric | Count |
|--------|-------|
| Tasks awaiting planning | {pending} |
| Tasks with plans | {planned} |
| Active plans | {active_plans} |"""

    if '## Planning Status' in content:
        content = re.sub(
            r'## Planning Status\n.*?(?=\n## |\Z)',
            section + '\n\n',
            content,
            flags=re.DOTALL
        )
    else:
        # Insert before Quick Links
        content = content.replace(
            '## Quick Links',
            section + '\n\n## Quick Links'
        )

    # Update timestamp
    content = re.sub(
        r'last_updated: .+',
        f'last_updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        content
    )

    DASHBOARD_PATH.write_text(content)
    logger.info(f"Dashboard updated: {pending} pending, {planned} planned, {active_plans} active plans")


def main():
    dry_run = '--dry-run' in sys.argv

    PLANS_DIR.mkdir(exist_ok=True)
    NEEDS_ACTION_DIR.mkdir(exist_ok=True)

    logger.info("=" * 50)
    logger.info(f"Task Planning Orchestrator {'(DRY-RUN)' if dry_run else ''}")
    logger.info(f"Scanning: {NEEDS_ACTION_DIR}")
    logger.info(f"Output:   {PLANS_DIR}")
    logger.info("=" * 50)

    tasks = sorted(NEEDS_ACTION_DIR.glob('*.md'))
    created = 0
    skipped = 0

    for task_path in tasks:
        try:
            if create_plan(task_path, dry_run):
                created += 1
            else:
                skipped += 1
        except Exception as e:
            logger.error(f"Error processing {task_path.name}: {e}")
            skipped += 1

    if not dry_run:
        update_dashboard()

    logger.info("=" * 50)
    logger.info(f"Complete: {created} plans created, {skipped} skipped")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
