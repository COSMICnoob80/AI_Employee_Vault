#!/usr/bin/env python3
"""
Cloud Agent — Draft-Only Zone Agent for Platinum Tier

Scans Inbox/ and Needs_Action/ for unclaimed tasks, generates template-based
drafts, and writes them to Pending_Approval/. NEVER sends, posts, or approves.
Writes status to Updates/cloud_status.md (NOT Dashboard.md).

Usage:
    python Scripts/cloud_agent.py                # Continuous loop
    python Scripts/cloud_agent.py --once         # Single iteration
    python Scripts/cloud_agent.py --scan-only    # List unclaimed tasks
    python Scripts/cloud_agent.py --dry-run      # Classify without moving

Stop mechanism:
    touch .cloud_stop
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
INBOX_DIR = VAULT_ROOT / "Inbox"
NEEDS_ACTION_DIR = VAULT_ROOT / "Needs_Action"
PENDING_APPROVAL_DIR = VAULT_ROOT / "Pending_Approval"
UPDATES_DIR = VAULT_ROOT / "Updates"
LOG_DIR = VAULT_ROOT / "Logs"
STOP_SENTINEL = VAULT_ROOT / ".cloud_stop"
PID_FILE = VAULT_ROOT / "cloud_agent.pid"

LOOP_INTERVAL = 30

# Setup logging
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "cloud_agent.log"),
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


def get_body(filepath: Path) -> str:
    """Extract body content after frontmatter."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""

    if not content.startswith("---"):
        return content

    parts = content.split("---", 2)
    return parts[2].strip() if len(parts) >= 3 else ""


# ---------------------------------------------------------------------------
# DraftGenerator — template-based drafts
# ---------------------------------------------------------------------------

class DraftGenerator:
    """Generate drafts from task files using templates (no LLM needed)."""

    def classify_task(self, filename: str, frontmatter: dict) -> str:
        """Classify task type from filename and frontmatter."""
        action_type = frontmatter.get("action_type", "")
        task_type = frontmatter.get("type", "")

        if filename.startswith("EMAIL_") or action_type == "email_send" or task_type == "email":
            return "email"
        if action_type in ("linkedin_post", "social_media") or task_type == "social_media":
            return "social"
        if action_type in ("financial", "accounting") or task_type == "financial":
            return "accounting"
        return "generic"

    def draft_email_reply(self, source_file: Path, frontmatter: dict, body: str) -> tuple[str, str]:
        """Generate an email reply draft. Returns (filename, content)."""
        subject = frontmatter.get("subject", "Re: " + source_file.stem)
        sender = frontmatter.get("from", frontmatter.get("sender", "unknown"))
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        draft_name = f"cloud_draft_email_{source_file.stem}.md"
        content = f"""---
type: approval_request
action_type: email_send
status: pending_approval
origin: cloud_agent
source_file: {source_file.name}
requires_local: true
created: {datetime.now().isoformat(timespec='seconds')}
subject: "{subject}"
to: "{sender}"
priority: normal
---

# Draft Email Reply

**To:** {sender}
**Subject:** {subject}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')} by Cloud Agent

---

Thank you for your email regarding "{subject}".

I have reviewed the contents and will follow up with a detailed response shortly.

Best regards,
AI Employee

---

*Original message from {sender}:*

> {body[:500] if body else '(no body content)'}

---

**Cloud Agent Note:** This is an auto-generated draft. Requires local agent approval before sending.
"""
        return draft_name, content

    def draft_social_post(self, source_file: Path, frontmatter: dict, body: str) -> tuple[str, str]:
        """Generate a social media post draft. Returns (filename, content)."""
        platform = frontmatter.get("platform", "linkedin")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        draft_name = f"cloud_draft_social_{source_file.stem}.md"
        topic = frontmatter.get("topic", frontmatter.get("subject", source_file.stem))
        content = f"""---
type: approval_request
action_type: social_media
status: pending_approval
origin: cloud_agent
source_file: {source_file.name}
requires_local: true
created: {datetime.now().isoformat(timespec='seconds')}
platform: {platform}
priority: normal
---

# Draft Social Media Post

**Platform:** {platform}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')} by Cloud Agent

---

{body[:280] if body else f'Sharing an update about {topic}. Stay tuned for more details!'}

---

**Cloud Agent Note:** This is an auto-generated draft. Requires local agent approval before posting.
"""
        return draft_name, content

    def draft_accounting_summary(self, source_file: Path, frontmatter: dict, body: str) -> tuple[str, str]:
        """Generate an accounting summary draft. Returns (filename, content)."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        draft_name = f"cloud_draft_accounting_{ts}.md"
        amount = frontmatter.get("amount", "N/A")
        content = f"""---
type: approval_request
action_type: financial
status: pending_approval
origin: cloud_agent
source_file: {source_file.name}
requires_local: true
created: {datetime.now().isoformat(timespec='seconds')}
amount: "{amount}"
priority: normal
---

# Draft Accounting Summary

**Source:** {source_file.name}
**Amount:** {amount}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')} by Cloud Agent

---

Financial action detected from {source_file.name}. Review required before execution.

{body[:300] if body else '(no additional details)'}

---

**Cloud Agent Note:** This is an auto-generated draft. Requires local agent approval.
"""
        return draft_name, content

    def draft_generic(self, source_file: Path, frontmatter: dict, body: str) -> tuple[str, str]:
        """Generate a generic task draft. Returns (filename, content)."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_type = frontmatter.get("type", "task")

        draft_name = f"cloud_draft_task_{source_file.stem}.md"
        content = f"""---
type: approval_request
action_type: generic
status: pending_approval
origin: cloud_agent
source_file: {source_file.name}
requires_local: true
created: {datetime.now().isoformat(timespec='seconds')}
priority: normal
---

# Draft Task Processing

**Source:** {source_file.name}
**Type:** {task_type}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')} by Cloud Agent

---

Task detected: {source_file.stem}

{body[:500] if body else '(no body content)'}

---

**Cloud Agent Note:** This is an auto-generated draft. Requires local agent review.
"""
        return draft_name, content

    def generate_draft(self, source_file: Path, frontmatter: dict, body: str) -> tuple[str, str]:
        """Route to appropriate draft generator based on classification."""
        task_type = self.classify_task(source_file.name, frontmatter)

        if task_type == "email":
            return self.draft_email_reply(source_file, frontmatter, body)
        elif task_type == "social":
            return self.draft_social_post(source_file, frontmatter, body)
        elif task_type == "accounting":
            return self.draft_accounting_summary(source_file, frontmatter, body)
        else:
            return self.draft_generic(source_file, frontmatter, body)


# ---------------------------------------------------------------------------
# CloudAgent — main loop
# ---------------------------------------------------------------------------

class CloudAgent:
    """Cloud zone agent: scan, claim, draft, write to Pending_Approval/."""

    def __init__(self, dry_run=False, once=False, scan_only=False):
        self.dry_run = dry_run
        self.once = once
        self.scan_only = scan_only
        self.claim_mgr = ClaimManager("cloud_agent", VAULT_ROOT)
        self.drafter = DraftGenerator()
        self.error_tracker = ErrorTracker("cloud_agent", threshold=10,
                                          window_seconds=300, cooldown=60)
        self.tasks_processed = 0
        self.drafts_created = 0
        self._running = True

    def scan_sources(self) -> list[Path]:
        """Scan Inbox/ and Needs_Action/ for unclaimed .md files."""
        candidates = []
        for scan_dir in [INBOX_DIR, NEEDS_ACTION_DIR]:
            if not scan_dir.exists():
                continue
            for f in sorted(scan_dir.iterdir()):
                if not f.is_file() or f.name.startswith("."):
                    continue
                if not f.suffix in (".md", ".txt"):
                    continue
                if not self.claim_mgr.is_claimed(f.name):
                    candidates.append(f)
        return candidates

    def process_task(self, source_path: Path) -> bool:
        """Claim -> classify -> draft -> write to Pending_Approval/."""
        filename = source_path.name
        logger.info(f"Processing: {filename}")

        # Claim
        claimed_path = self.claim_mgr.claim(source_path)
        if claimed_path is None:
            logger.info(f"Skip {filename}: could not claim")
            return False

        # Read frontmatter and body
        fm = parse_frontmatter(claimed_path)
        body = get_body(claimed_path)

        # Generate draft
        draft_name, draft_content = self.drafter.generate_draft(
            claimed_path, fm, body
        )
        task_type = self.drafter.classify_task(filename, fm)

        # Write draft to Pending_Approval/
        PENDING_APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
        draft_path = PENDING_APPROVAL_DIR / draft_name
        safe_write(draft_path, draft_content)
        self.drafts_created += 1

        logger.info(f"Draft created: {draft_name} (type={task_type})")
        audit_log("cloud_draft_created", "cloud_agent", {
            "source": filename,
            "draft": draft_name,
            "type": task_type,
        })

        # Release original to Pending_Approval/ as well (for reference)
        self.claim_mgr.release(filename, PENDING_APPROVAL_DIR)
        self.tasks_processed += 1
        return True

    def write_status(self):
        """Write status to Updates/cloud_status.md (NOT Dashboard.md)."""
        UPDATES_DIR.mkdir(parents=True, exist_ok=True)
        now = datetime.now()
        claimed = self.claim_mgr.list_claimed()

        status_content = f"""---
type: agent_status
agent: cloud_agent
updated: {now.isoformat(timespec='seconds')}
---

# Cloud Agent Status

| Metric | Value |
|--------|-------|
| Status | {'Running' if self._running else 'Stopped'} |
| Last Update | {now.strftime('%Y-%m-%d %H:%M:%S')} |
| Tasks Processed | {self.tasks_processed} |
| Drafts Created | {self.drafts_created} |
| In Progress | {len(claimed)} |
| Mode | {'dry-run' if self.dry_run else 'live'} |
"""
        safe_write(UPDATES_DIR / "cloud_status.md", status_content)

    def check_stop(self) -> bool:
        """Check for .cloud_stop sentinel."""
        if STOP_SENTINEL.exists():
            logger.info("Stop sentinel detected — cloud agent shutting down")
            audit_log("cloud_stop", "cloud_agent", {
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
        """Write PID file."""
        PID_FILE.write_text(str(os.getpid()))
        logger.info(f"PID {os.getpid()} written to {PID_FILE}")

    def cleanup(self):
        """Remove PID file and write final status."""
        self._running = False
        self.write_status()
        try:
            PID_FILE.unlink(missing_ok=True)
        except OSError:
            pass
        audit_log("cloud_shutdown", "cloud_agent", {
            "tasks_processed": self.tasks_processed,
            "drafts_created": self.drafts_created,
        })
        logger.info(
            f"Cloud agent stopped. Tasks: {self.tasks_processed}, "
            f"Drafts: {self.drafts_created}"
        )

    def _handle_signal(self, signum, frame):
        """Handle SIGTERM/SIGINT for graceful shutdown."""
        logger.info(f"Signal {signum} received, shutting down...")
        self._running = False

    def run(self):
        """Main loop: scan -> claim -> draft -> status."""
        self.write_pid()
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        logger.info("=" * 50)
        logger.info("Cloud Agent Starting (Draft-Only Zone)")
        logger.info(f"Mode: dry_run={self.dry_run}, once={self.once}, "
                     f"scan_only={self.scan_only}")
        logger.info("=" * 50)
        audit_log("cloud_start", "cloud_agent", {
            "dry_run": self.dry_run, "once": self.once,
            "scan_only": self.scan_only,
        })

        try:
            while self._running:
                if self.check_stop():
                    break

                self._iterate()
                self.write_status()

                if self.once or self.scan_only:
                    break

                if not self.error_tracker.check():
                    continue

                logger.info(f"Sleeping {LOOP_INTERVAL}s until next scan...")
                time.sleep(LOOP_INTERVAL)
        finally:
            self.cleanup()

    def _iterate(self):
        """Single iteration: scan and process."""
        candidates = self.scan_sources()
        logger.info(f"Found {len(candidates)} unclaimed tasks")

        audit_log("cloud_scan", "cloud_agent", {
            "candidates": len(candidates),
            "sources": [c.name for c in candidates[:10]],
        })

        if self.scan_only:
            for c in candidates:
                fm = parse_frontmatter(c)
                task_type = self.drafter.classify_task(c.name, fm)
                logger.info(f"  {c.parent.name}/{c.name} -> {task_type}")
            return

        for candidate in candidates:
            if self.check_stop():
                break

            if self.dry_run:
                fm = parse_frontmatter(candidate)
                task_type = self.drafter.classify_task(candidate.name, fm)
                logger.info(
                    f"[DRY-RUN] Would draft: {candidate.name} "
                    f"(type={task_type})"
                )
                audit_log("cloud_dry_run", "cloud_agent", {
                    "file": candidate.name,
                    "type": task_type,
                })
                self.tasks_processed += 1
                continue

            try:
                self.process_task(candidate)
            except Exception as e:
                logger.error(f"Error processing {candidate.name}: {e}")
                self.error_tracker.record_error(str(e))
                audit_log("cloud_error", "cloud_agent", {
                    "file": candidate.name,
                }, status="error", error=str(e))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Cloud Agent — Draft-Only Zone (Platinum Tier)"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Scan and classify without creating drafts")
    parser.add_argument("--once", action="store_true",
                        help="Run a single iteration then exit")
    parser.add_argument("--scan-only", action="store_true",
                        help="List unclaimed tasks without processing")

    args = parser.parse_args()

    agent = CloudAgent(
        dry_run=args.dry_run,
        once=args.once,
        scan_only=args.scan_only,
    )
    agent.run()


if __name__ == "__main__":
    main()
