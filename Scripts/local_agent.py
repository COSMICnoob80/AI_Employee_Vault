#!/usr/bin/env python3
"""
Local Agent — Approve+Execute Zone Agent for Platinum Tier

Merges cloud agent status into Dashboard.md, scans Approved/ for cloud drafts,
claims and executes them (MCP calls or dry-run logging), and archives to Done/.
Owns Dashboard.md writes (single-writer rule).

Usage:
    python Scripts/local_agent.py                # Continuous loop
    python Scripts/local_agent.py --once         # Single iteration
    python Scripts/local_agent.py --dry-run      # Process without executing

Stop mechanism:
    touch .local_stop
"""

import os
import sys
import time
import signal
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Watchers"))

from claim_manager import ClaimManager
from vault_audit import audit_log, safe_write, ErrorTracker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VAULT_ROOT = Path.home() / "AI_Employee_Vault"
APPROVED_DIR = VAULT_ROOT / "Approved"
DONE_DIR = VAULT_ROOT / "Done"
UPDATES_DIR = VAULT_ROOT / "Updates"
DASHBOARD_PATH = VAULT_ROOT / "Dashboard.md"
LOG_DIR = VAULT_ROOT / "Logs"
STOP_SENTINEL = VAULT_ROOT / ".local_stop"
PID_FILE = VAULT_ROOT / "local_agent.pid"

LOOP_INTERVAL = 30

PLATINUM_START = "<!-- PLATINUM_STATUS_START -->"
PLATINUM_END = "<!-- PLATINUM_STATUS_END -->"

# Setup logging
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "local_agent.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# YAML frontmatter parser
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
# DashboardMerger — updates Dashboard.md Platinum section
# ---------------------------------------------------------------------------

class DashboardMerger:
    """Read Updates/cloud_status.md and merge into Dashboard.md."""

    def merge_cloud_status(self, local_tasks: int, local_executed: int,
                           dry_run: bool) -> bool:
        """Update Dashboard.md between PLATINUM_STATUS markers."""
        cloud_status_path = UPDATES_DIR / "cloud_status.md"

        # Parse cloud status
        cloud_metrics = {}
        if cloud_status_path.exists():
            fm = parse_frontmatter(cloud_status_path)
            try:
                content = cloud_status_path.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if "|" in line and "Value" not in line and "---" not in line and "Metric" not in line:
                        parts = [p.strip() for p in line.split("|") if p.strip()]
                        if len(parts) == 2:
                            cloud_metrics[parts[0]] = parts[1]
            except (OSError, UnicodeDecodeError):
                pass

        cloud_status = cloud_metrics.get("Status", "Offline")
        cloud_updated = cloud_metrics.get("Last Update", "Never")
        cloud_processed = cloud_metrics.get("Tasks Processed", "0")
        cloud_drafts = cloud_metrics.get("Drafts Created", "0")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        section = f"""
## Platinum Status (Cloud/Local Split)

| Agent | Zone | Status | Tasks | Last Update |
|-------|------|--------|-------|-------------|
| Cloud Agent | Draft-only | {cloud_status} | {cloud_processed} processed, {cloud_drafts} drafts | {cloud_updated} |
| Local Agent | Approve+Execute | Running | {local_tasks} scanned, {local_executed} executed | {now} |

**Coordination:** Claim-by-move via `In_Progress/{{agent}}/`
**Sync:** Commit-based checkpoints (`Scripts/vault_sync.sh`)
**Mode:** {'dry-run' if dry_run else 'live'}

**Commands:**
- Cloud agent: `python Scripts/cloud_agent.py --once`
- Local agent: `python Scripts/local_agent.py --once`
- Full demo: `bash Scripts/platinum_demo.sh --auto`
"""

        if not DASHBOARD_PATH.exists():
            logger.warning("Dashboard.md not found, skipping merge")
            return False

        try:
            dashboard = DASHBOARD_PATH.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Cannot read Dashboard.md: {e}")
            return False

        if PLATINUM_START in dashboard and PLATINUM_END in dashboard:
            before = dashboard.split(PLATINUM_START)[0]
            after = dashboard.split(PLATINUM_END)[1]
            updated = before + PLATINUM_START + section + PLATINUM_END + after
        elif PLATINUM_START in dashboard:
            before = dashboard.split(PLATINUM_START)[0]
            updated = before + PLATINUM_START + section + PLATINUM_END + "\n"
        else:
            updated = dashboard.rstrip() + "\n\n" + PLATINUM_START + section + PLATINUM_END + "\n"

        safe_write(DASHBOARD_PATH, updated)
        logger.info("Dashboard.md Platinum section updated")
        return True


# ---------------------------------------------------------------------------
# ActionExecutor — executes approved cloud drafts
# ---------------------------------------------------------------------------

class ActionExecutor:
    """Execute approved cloud drafts."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run

    def execute(self, filepath: Path, frontmatter: dict) -> bool:
        """Route to appropriate executor based on action_type."""
        action_type = frontmatter.get("action_type", "generic")

        if action_type == "email_send":
            return self.execute_email_send(filepath, frontmatter)
        elif action_type == "social_media":
            return self.execute_social_post(filepath, frontmatter)
        else:
            return self.execute_generic(filepath, frontmatter)

    def execute_email_send(self, filepath: Path, frontmatter: dict) -> bool:
        """Execute email send (MCP call or dry-run log)."""
        to = frontmatter.get("to", "unknown")
        subject = frontmatter.get("subject", "No subject")

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would send email: to={to}, subject={subject}")
            audit_log("local_dry_run_email", "local_agent", {
                "file": filepath.name, "to": to, "subject": subject,
            })
            return True

        # In production, this would invoke MCP gmail-send
        logger.info(f"EXECUTE email send: to={to}, subject={subject}")
        audit_log("local_email_executed", "local_agent", {
            "file": filepath.name, "to": to, "subject": subject,
        })
        return True

    def execute_social_post(self, filepath: Path, frontmatter: dict) -> bool:
        """Execute social media post (MCP call or dry-run log)."""
        platform = frontmatter.get("platform", "unknown")

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would post to {platform}")
            audit_log("local_dry_run_social", "local_agent", {
                "file": filepath.name, "platform": platform,
            })
            return True

        logger.info(f"EXECUTE social post: platform={platform}")
        audit_log("local_social_executed", "local_agent", {
            "file": filepath.name, "platform": platform,
        })
        return True

    def execute_generic(self, filepath: Path, frontmatter: dict) -> bool:
        """Execute generic action (log and archive)."""
        action_type = frontmatter.get("action_type", "generic")

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would execute: {action_type} for {filepath.name}")
            audit_log("local_dry_run_generic", "local_agent", {
                "file": filepath.name, "action_type": action_type,
            })
            return True

        logger.info(f"EXECUTE generic: {action_type} for {filepath.name}")
        audit_log("local_generic_executed", "local_agent", {
            "file": filepath.name, "action_type": action_type,
        })
        return True


# ---------------------------------------------------------------------------
# LocalAgent — main loop
# ---------------------------------------------------------------------------

class LocalAgent:
    """Local zone agent: merge status, scan approved, execute, archive."""

    def __init__(self, dry_run=False, once=False):
        self.dry_run = dry_run
        self.once = once
        self.claim_mgr = ClaimManager("local_agent", VAULT_ROOT)
        self.merger = DashboardMerger()
        self.executor = ActionExecutor(dry_run=dry_run)
        self.error_tracker = ErrorTracker("local_agent", threshold=10,
                                          window_seconds=300, cooldown=60)
        self.tasks_scanned = 0
        self.tasks_executed = 0
        self._running = True

    def scan_approved(self) -> list[Path]:
        """Find cloud_draft_* files in Approved/ that are unclaimed."""
        if not APPROVED_DIR.exists():
            return []
        drafts = []
        for f in sorted(APPROVED_DIR.iterdir()):
            if not f.is_file() or not f.name.startswith("cloud_draft_"):
                continue
            if not self.claim_mgr.is_claimed(f.name):
                drafts.append(f)
        return drafts

    def process_approved(self, filepath: Path) -> bool:
        """Claim -> execute -> release to Done/."""
        filename = filepath.name
        logger.info(f"Processing approved draft: {filename}")

        # Claim
        claimed_path = self.claim_mgr.claim(filepath)
        if claimed_path is None:
            logger.info(f"Skip {filename}: could not claim")
            return False

        # Read frontmatter
        fm = parse_frontmatter(claimed_path)

        # Execute
        success = self.executor.execute(claimed_path, fm)
        if not success:
            logger.error(f"Execution failed for {filename}")
            # Release back to Approved/ on failure
            self.claim_mgr.release(filename, APPROVED_DIR)
            return False

        # Update status in file before archiving
        try:
            content = claimed_path.read_text(encoding="utf-8")
            content = content.replace("status: pending_approval", "status: done")
            content = content.replace("status: approved", "status: done")
            safe_write(claimed_path, content)
        except (OSError, UnicodeDecodeError):
            pass

        # Release to Done/
        DONE_DIR.mkdir(parents=True, exist_ok=True)
        self.claim_mgr.release(filename, DONE_DIR)
        self.tasks_executed += 1

        audit_log("local_task_completed", "local_agent", {
            "file": filename,
            "action_type": fm.get("action_type", "unknown"),
            "dry_run": self.dry_run,
        })
        return True

    def check_stop(self) -> bool:
        """Check for .local_stop sentinel."""
        if STOP_SENTINEL.exists():
            logger.info("Stop sentinel detected — local agent shutting down")
            audit_log("local_stop", "local_agent", {
                "reason": "stop_sentinel",
                "tasks_executed": self.tasks_executed,
            })
            try:
                STOP_SENTINEL.unlink()
            except OSError:
                pass
            return True
        return False

    def write_pid(self):
        """Write PID file."""
        PID_FILE.write_text(str(os.getpid()))
        logger.info(f"PID {os.getpid()} written to {PID_FILE}")

    def cleanup(self):
        """Remove PID file and write final audit."""
        self._running = False
        try:
            PID_FILE.unlink(missing_ok=True)
        except OSError:
            pass
        audit_log("local_shutdown", "local_agent", {
            "tasks_scanned": self.tasks_scanned,
            "tasks_executed": self.tasks_executed,
        })
        logger.info(
            f"Local agent stopped. Scanned: {self.tasks_scanned}, "
            f"Executed: {self.tasks_executed}"
        )

    def _handle_signal(self, signum, frame):
        """Handle SIGTERM/SIGINT for graceful shutdown."""
        logger.info(f"Signal {signum} received, shutting down...")
        self._running = False

    def run(self):
        """Main loop: merge status -> scan approved -> execute -> archive."""
        self.write_pid()
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        logger.info("=" * 50)
        logger.info("Local Agent Starting (Approve+Execute Zone)")
        logger.info(f"Mode: dry_run={self.dry_run}, once={self.once}")
        logger.info("=" * 50)
        audit_log("local_start", "local_agent", {
            "dry_run": self.dry_run, "once": self.once,
        })

        try:
            while self._running:
                if self.check_stop():
                    break

                self._iterate()

                if self.once:
                    break

                if not self.error_tracker.check():
                    continue

                logger.info(f"Sleeping {LOOP_INTERVAL}s until next scan...")
                time.sleep(LOOP_INTERVAL)
        finally:
            self.cleanup()

    def _iterate(self):
        """Single iteration: merge, scan, process."""
        # Merge cloud status into Dashboard
        self.merger.merge_cloud_status(
            self.tasks_scanned, self.tasks_executed, self.dry_run
        )

        # Scan Approved/ for cloud drafts
        drafts = self.scan_approved()
        self.tasks_scanned += len(drafts)
        logger.info(f"Found {len(drafts)} approved cloud drafts")

        audit_log("local_scan", "local_agent", {
            "approved_drafts": len(drafts),
            "files": [d.name for d in drafts[:10]],
        })

        # Process each
        for draft in drafts:
            if self.check_stop():
                break

            try:
                self.process_approved(draft)
            except Exception as e:
                logger.error(f"Error processing {draft.name}: {e}")
                self.error_tracker.record_error(str(e))
                audit_log("local_error", "local_agent", {
                    "file": draft.name,
                }, status="error", error=str(e))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Local Agent — Approve+Execute Zone (Platinum Tier)"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Process without executing actions")
    parser.add_argument("--once", action="store_true",
                        help="Run a single iteration then exit")

    args = parser.parse_args()

    agent = LocalAgent(
        dry_run=args.dry_run,
        once=args.once,
    )
    agent.run()


if __name__ == "__main__":
    main()
