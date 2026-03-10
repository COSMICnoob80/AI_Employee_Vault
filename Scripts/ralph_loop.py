#!/usr/bin/env python3
"""
Ralph Wiggum Task Loop — Autonomous Task Execution Engine

Scans the vault's task queue (Needs_Action/, Plans/), prioritizes work,
classifies tasks as autonomous or approval-required, executes or routes
accordingly, verifies completion, and reports.

Usage:
    python ralph_loop.py                  # Run continuous loop
    python ralph_loop.py --once           # Single iteration
    python ralph_loop.py --scan-only      # Produce queue manifest only
    python ralph_loop.py --dry-run        # Scan and classify without executing
    python ralph_loop.py --max 5          # Process at most 5 tasks then exit

Stop mechanism:
    touch .ralph_stop                     # Graceful halt at next iteration
"""

import os
import sys
import json
import time
import signal
import argparse
import logging
import shutil
from datetime import datetime
from pathlib import Path

# Add Watchers/ to path for vault_audit imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Watchers"))

from vault_audit import audit_log, safe_write, ErrorTracker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_ROOT = Path.home() / "AI_Employee_Vault"
NEEDS_ACTION_DIR = VAULT_ROOT / "Needs_Action"
PLANS_DIR = VAULT_ROOT / "Plans"
DONE_DIR = VAULT_ROOT / "Done"
PENDING_APPROVAL_DIR = VAULT_ROOT / "Pending_Approval"
LOG_DIR = VAULT_ROOT / "Logs"
QUEUE_MANIFEST = LOG_DIR / "ralph_queue.json"
STOP_SENTINEL = VAULT_ROOT / ".ralph_stop"
PID_FILE = VAULT_ROOT / "ralph_loop.pid"

LOOP_INTERVAL = 30  # seconds between iterations

# Setup logging
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "ralph_loop.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# YAML frontmatter parser (reused pattern from approval_watcher.py)
# ---------------------------------------------------------------------------

try:
    import yaml
except ImportError:
    yaml = None


def parse_frontmatter(filepath: Path) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        logger.warning(f"Could not read {filepath.name}: {e}")
        return {}

    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    raw = parts[1]
    if yaml is not None:
        try:
            data = yaml.safe_load(raw)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning(f"YAML parse error in {filepath.name}: {e}")
            return {}
    else:
        result = {}
        for line in raw.strip().splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                result[key.strip()] = value.strip()
        return result


# ---------------------------------------------------------------------------
# TaskQueue — scan and prioritize
# ---------------------------------------------------------------------------

PRIORITY_SCORES = {"urgent": 3, "high": 2, "normal": 1, "low": 0}
TYPE_SCORES = {"email": 2, "file_drop": 1, "manual": 0}


class TaskQueue:
    """Scans Needs_Action/ and Plans/, builds a prioritized queue."""

    def scan(self) -> list[dict]:
        """Read all .md files from Needs_Action/, enrich with plan info."""
        tasks = []
        if not NEEDS_ACTION_DIR.exists():
            return tasks

        for f in sorted(NEEDS_ACTION_DIR.iterdir()):
            if not f.is_file() or not f.suffix == ".md":
                continue
            fm = parse_frontmatter(f)
            # Determine task type from filename or frontmatter
            task_type = fm.get("type", "manual")
            if f.name.startswith("EMAIL_"):
                task_type = "email"
            elif "file_drop" in f.name or fm.get("source") == "file_watcher":
                task_type = "file_drop"

            # Check for matching plan
            plan_path = PLANS_DIR / f"plan_{f.name}"
            has_plan = plan_path.exists()
            if not has_plan:
                # Try alternative plan naming
                plan_path = PLANS_DIR / f.name
                has_plan = plan_path.exists()

            # Parse age from filename or frontmatter
            created = fm.get("created", "")
            try:
                if isinstance(created, str) and len(created) >= 10:
                    age_days = (datetime.now() - datetime.fromisoformat(
                        created[:10]
                    )).days
                else:
                    age_days = 0
            except (ValueError, TypeError):
                age_days = 0

            tasks.append({
                "file": f.name,
                "path": str(f),
                "priority": fm.get("priority", "normal"),
                "type": task_type,
                "status": fm.get("status", "unknown"),
                "has_plan": has_plan,
                "plan_path": str(plan_path) if has_plan else None,
                "age_days": age_days,
                "frontmatter": fm,
            })

        return tasks

    def prioritize(self, tasks: list[dict]) -> list[dict]:
        """Sort tasks by priority score, plan availability, age, type."""

        def score(t):
            p = PRIORITY_SCORES.get(t["priority"], 1)
            plan_bonus = 1 if t["has_plan"] else 0
            type_bonus = TYPE_SCORES.get(t["type"], 0)
            age = t["age_days"]
            # Higher score = processed first
            return (p, plan_bonus, age, type_bonus)

        return sorted(tasks, key=score, reverse=True)

    def write_manifest(self, queue: list[dict]):
        """Write the current queue state to Logs/ralph_queue.json."""
        manifest = {
            "generated": datetime.now().astimezone().isoformat(),
            "total_tasks": len(queue),
            "queue": queue,
        }
        safe_write(QUEUE_MANIFEST, json.dumps(manifest, indent=2, default=str))
        logger.info(f"Queue manifest written: {QUEUE_MANIFEST} ({len(queue)} tasks)")


# ---------------------------------------------------------------------------
# ActionClassifier — autonomous vs approval-required
# ---------------------------------------------------------------------------

class ActionClassifier:
    """Classify tasks as autonomous or requiring human approval."""

    APPROVAL_KEYWORDS = {
        "email_send", "financial", "social_media", "linkedin_post",
        "payment", "subscription", "external_api", "delete",
    }

    APPROVAL_TYPES = {"email", "financial", "social_media"}

    def classify(self, task: dict) -> str:
        """Return 'autonomous' or 'needs_approval'."""
        fm = task.get("frontmatter", {})
        action_type = fm.get("action_type", "")
        task_type = task.get("type", "")

        # Check action_type against approval keywords
        if action_type in self.APPROVAL_KEYWORDS:
            return "needs_approval"

        # Check if type requires approval
        if task_type in self.APPROVAL_TYPES:
            return "needs_approval"

        # Check for approval-related frontmatter flags
        if fm.get("requires_approval", False):
            return "needs_approval"

        return "autonomous"


# ---------------------------------------------------------------------------
# TaskExecutor — execute or route tasks
# ---------------------------------------------------------------------------

class TaskExecutor:
    """Execute autonomous tasks or route approval-required ones."""

    def execute_autonomous(self, task: dict) -> bool:
        """Process an autonomous task: update status, archive to Done/."""
        src = Path(task["path"])
        if not src.exists():
            logger.warning(f"Task file missing: {src}")
            return False

        try:
            content = src.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            logger.error(f"Cannot read {src.name}: {e}")
            return False

        # Update status in frontmatter
        updated = content.replace("status: pending", "status: done")
        updated = updated.replace("status: planned", "status: done")
        updated = updated.replace("status: needs_action", "status: done")
        updated = updated.replace("status: unknown", "status: done")
        if "status: done" not in updated:
            # Add status if none exists
            if updated.startswith("---"):
                updated = updated.replace("---\n", "---\nstatus: done\n", 1)

        # Write to Done/
        dest = DONE_DIR / src.name
        DONE_DIR.mkdir(exist_ok=True)
        safe_write(dest, updated)

        # Remove from Needs_Action
        src.unlink()

        # Also move plan if it exists
        if task.get("plan_path"):
            plan_src = Path(task["plan_path"])
            if plan_src.exists():
                plan_dest = DONE_DIR / plan_src.name
                shutil.move(str(plan_src), str(plan_dest))

        logger.info(f"Completed: {src.name} -> Done/")
        audit_log("task_completed", "ralph_loop", {
            "file": src.name, "type": task["type"],
            "priority": task["priority"],
        })
        return True

    def route_to_approval(self, task: dict) -> bool:
        """Move task to Pending_Approval/ for human review."""
        src = Path(task["path"])
        if not src.exists():
            logger.warning(f"Task file missing: {src}")
            return False

        try:
            content = src.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            logger.error(f"Cannot read {src.name}: {e}")
            return False

        # Update status
        updated = content.replace("status: pending", "status: pending_approval")
        updated = updated.replace("status: planned", "status: pending_approval")
        updated = updated.replace("status: needs_action", "status: pending_approval")
        if "status: pending_approval" not in updated and "status:" in updated:
            pass  # keep existing status
        elif "status:" not in updated and updated.startswith("---"):
            updated = updated.replace("---\n", "---\nstatus: pending_approval\n", 1)

        # Write to Pending_Approval/
        dest = PENDING_APPROVAL_DIR / src.name
        PENDING_APPROVAL_DIR.mkdir(exist_ok=True)
        safe_write(dest, updated)

        # Remove from Needs_Action
        src.unlink()

        logger.info(f"Routed to approval: {src.name} -> Pending_Approval/")
        audit_log("task_routed_approval", "ralph_loop", {
            "file": src.name, "type": task["type"],
            "priority": task["priority"],
            "action_type": task.get("frontmatter", {}).get("action_type", "unknown"),
        })
        return True

    def verify_completion(self, task: dict) -> bool:
        """3-point verification check."""
        filename = task["file"]
        done_path = DONE_DIR / filename

        # 1. Task file present in Done/
        if not done_path.exists():
            logger.warning(f"Verify FAIL: {filename} not in Done/")
            return False

        # 2. Frontmatter status is 'done'
        fm = parse_frontmatter(done_path)
        if fm.get("status") != "done":
            logger.warning(f"Verify FAIL: {filename} status != done")
            return False

        # 3. Plan checkboxes all checked (if plan exists)
        if task.get("plan_path"):
            plan_done = DONE_DIR / Path(task["plan_path"]).name
            if plan_done.exists():
                try:
                    plan_content = plan_done.read_text(encoding="utf-8")
                    unchecked = plan_content.count("- [ ]")
                    if unchecked > 0:
                        logger.warning(
                            f"Verify FAIL: {filename} plan has "
                            f"{unchecked} unchecked items"
                        )
                        return False
                except OSError:
                    pass

        logger.info(f"Verify PASS: {filename}")
        return True


# ---------------------------------------------------------------------------
# RalphLoop — main control loop
# ---------------------------------------------------------------------------

class RalphLoop:
    """Main task processing loop."""

    def __init__(self, dry_run=False, once=False, scan_only=False, max_tasks=0):
        self.dry_run = dry_run
        self.once = once
        self.scan_only = scan_only
        self.max_tasks = max_tasks
        self.queue = TaskQueue()
        self.classifier = ActionClassifier()
        self.executor = TaskExecutor()
        self.error_tracker = ErrorTracker("ralph_loop", threshold=10,
                                          window_seconds=300, cooldown=60)
        self.tasks_processed = 0
        self._running = True

    def check_stop(self) -> bool:
        """Check for .ralph_stop sentinel file."""
        if STOP_SENTINEL.exists():
            logger.info("Stop sentinel detected — I'm in danger!")
            audit_log("ralph_stop", "ralph_loop", {
                "reason": "stop_sentinel",
                "tasks_processed": self.tasks_processed,
            })
            try:
                STOP_SENTINEL.unlink()
            except OSError:
                pass
            return True
        return False

    def write_pid(self):
        """Write PID file for schedule_watchers.sh integration."""
        PID_FILE.write_text(str(os.getpid()))
        logger.info(f"PID {os.getpid()} written to {PID_FILE}")

    def cleanup(self):
        """Remove PID file, write final audit."""
        try:
            PID_FILE.unlink(missing_ok=True)
        except OSError:
            pass
        audit_log("ralph_shutdown", "ralph_loop", {
            "tasks_processed": self.tasks_processed,
        })
        logger.info(f"Ralph loop stopped. Tasks processed: {self.tasks_processed}")

    def _handle_signal(self, signum, frame):
        """Handle SIGTERM/SIGINT for graceful shutdown."""
        logger.info(f"Signal {signum} received, shutting down...")
        self._running = False

    def run(self):
        """Main loop: scan -> prioritize -> classify -> exec -> verify."""
        self.write_pid()
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        logger.info("=" * 50)
        logger.info("Ralph Wiggum Task Loop Starting")
        logger.info(f"Mode: dry_run={self.dry_run}, once={self.once}, "
                     f"scan_only={self.scan_only}, max={self.max_tasks}")
        logger.info("=" * 50)
        audit_log("ralph_start", "ralph_loop", {
            "dry_run": self.dry_run, "once": self.once,
            "scan_only": self.scan_only, "max_tasks": self.max_tasks,
        })

        try:
            while self._running:
                if self.check_stop():
                    break

                self._iterate()

                if self.once or self.scan_only:
                    break

                if self.max_tasks and self.tasks_processed >= self.max_tasks:
                    logger.info(f"Max tasks ({self.max_tasks}) reached, exiting")
                    break

                # Circuit breaker check
                if not self.error_tracker.check():
                    continue

                logger.info(f"Sleeping {LOOP_INTERVAL}s until next iteration...")
                time.sleep(LOOP_INTERVAL)
        finally:
            self.cleanup()

    def _iterate(self):
        """Single iteration: scan, prioritize, process."""
        # Scan
        tasks = self.queue.scan()
        prioritized = self.queue.prioritize(tasks)
        self.queue.write_manifest(prioritized)

        logger.info(f"Queue: {len(prioritized)} tasks")
        audit_log("ralph_scan", "ralph_loop", {
            "queue_size": len(prioritized),
        })

        if self.scan_only:
            logger.info("Scan-only mode — skipping execution")
            return

        # Process each task
        for task in prioritized:
            if self.check_stop():
                break

            if self.max_tasks and self.tasks_processed >= self.max_tasks:
                break

            classification = self.classifier.classify(task)
            logger.info(
                f"Processing: {task['file']} "
                f"[{task['priority']}] [{task['type']}] -> {classification}"
            )

            if self.dry_run:
                audit_log("ralph_dry_run", "ralph_loop", {
                    "file": task["file"],
                    "classification": classification,
                    "priority": task["priority"],
                })
                self.tasks_processed += 1
                continue

            try:
                if classification == "needs_approval":
                    success = self.executor.route_to_approval(task)
                else:
                    success = self.executor.execute_autonomous(task)

                if success:
                    if classification == "autonomous":
                        self.executor.verify_completion(task)
                    self.tasks_processed += 1
                else:
                    self.error_tracker.record_error(f"Failed: {task['file']}")
            except Exception as e:
                logger.error(f"Error processing {task['file']}: {e}")
                self.error_tracker.record_error(str(e))
                audit_log("ralph_error", "ralph_loop", {
                    "file": task["file"],
                }, status="error", error=str(e))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Ralph Wiggum Task Loop — Autonomous Task Execution Engine"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Scan and classify without executing")
    parser.add_argument("--once", action="store_true",
                        help="Run a single iteration then exit")
    parser.add_argument("--scan-only", action="store_true",
                        help="Produce queue manifest only, no processing")
    parser.add_argument("--max", type=int, default=0,
                        help="Process at most N tasks then exit")

    args = parser.parse_args()

    loop = RalphLoop(
        dry_run=args.dry_run,
        once=args.once,
        scan_only=args.scan_only,
        max_tasks=args.max,
    )
    loop.run()


if __name__ == "__main__":
    main()
