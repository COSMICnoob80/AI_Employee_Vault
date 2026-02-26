#!/usr/bin/env python3
"""
Approval Watcher for AI Employee Vault

Monitors Pending_Approval and Approved directories to track approval
workflow transitions and archive completed approvals to Done.

Usage:
    python approval_watcher.py

Dependencies:
    pip install watchdog pyyaml
"""

import os
import sys
import time
import shutil
import logging
from datetime import datetime
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Error: watchdog not installed. Run: pip install watchdog")
    sys.exit(1)

try:
    import yaml
except ImportError:
    yaml = None

# Configuration
VAULT_ROOT = Path.home() / "AI_Employee_Vault"
PENDING_DIR = VAULT_ROOT / "Pending_Approval"
APPROVED_DIR = VAULT_ROOT / "Approved"
DONE_DIR = VAULT_ROOT / "Done"
LOG_DIR = VAULT_ROOT / "Logs"

# Setup logging
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "approval.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def parse_frontmatter(filepath: Path) -> dict:
    """Extract YAML frontmatter from a markdown file.

    Reads content between the first and second '---' delimiters
    and parses it with yaml.safe_load.

    Returns a dict of frontmatter fields, or empty dict on failure.
    """
    try:
        content = filepath.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        logger.warning(f"Could not decode {filepath.name} as UTF-8")
        return {}
    except Exception as e:
        logger.warning(f"Could not read {filepath.name}: {e}")
        return {}

    if not content.startswith('---'):
        return {}

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}

    raw_frontmatter = parts[1]

    if yaml is not None:
        try:
            data = yaml.safe_load(raw_frontmatter)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning(f"YAML parse error in {filepath.name}: {e}")
            return {}
    else:
        # Fallback: simple key: value parsing
        result = {}
        for line in raw_frontmatter.strip().splitlines():
            if ':' in line:
                key, _, value = line.partition(':')
                result[key.strip()] = value.strip()
        return result


class PendingApprovalHandler(FileSystemEventHandler):
    """Handles new files appearing in the Pending_Approval directory."""

    def __init__(self):
        self.processed_files = set()

    def on_created(self, event):
        """Called when a file is created in Pending_Approval."""
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        # Skip hidden files and already processed
        if filepath.name.startswith('.') or filepath in self.processed_files:
            return

        # Small delay to ensure file is fully written
        time.sleep(0.5)

        try:
            self._process_file(filepath)
            self.processed_files.add(filepath)
        except Exception as e:
            logger.error(f"Failed to process {filepath.name}: {e}")

    def _process_file(self, filepath: Path):
        """Log the new pending approval request."""
        frontmatter = parse_frontmatter(filepath)
        action_type = frontmatter.get('action_type', 'unknown')
        priority = frontmatter.get('priority', 'normal')
        requester = frontmatter.get('requester', 'unknown')

        logger.info(
            f"New approval request: {filepath.name} "
            f"| Type: {action_type} | Priority: {priority}"
        )


class ApprovedHandler(FileSystemEventHandler):
    """Handles files appearing in the Approved directory."""

    def __init__(self):
        self.processed_files = set()

    def on_created(self, event):
        """Called when a file is created in Approved."""
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        # Skip hidden files and already processed
        if filepath.name.startswith('.') or filepath in self.processed_files:
            return

        # Small delay to ensure file is fully written
        time.sleep(0.5)

        try:
            self._process_file(filepath)
            self.processed_files.add(filepath)
        except Exception as e:
            logger.error(f"Failed to process {filepath.name}: {e}")

    def _process_file(self, filepath: Path):
        """Log the approval and archive to Done."""
        frontmatter = parse_frontmatter(filepath)
        action_type = frontmatter.get('action_type', 'unknown')

        logger.info(
            f"Approved: {filepath.name} "
            f"| Type: {action_type} | Ready for execution"
        )

        # Copy to Done with status updated
        done_path = DONE_DIR / filepath.name
        try:
            content = filepath.read_text(encoding='utf-8')
            content = content.replace(
                'status: pending_approval', 'status: done'
            )
            done_path.write_text(content, encoding='utf-8')
        except UnicodeDecodeError:
            shutil.copy2(filepath, done_path)
        except Exception as e:
            logger.error(f"Failed to archive {filepath.name}: {e}")
            return

        logger.info(f"Archived to Done: {filepath.name}")


def main():
    """Main entry point for the approval watcher."""
    # Ensure directories exist
    PENDING_DIR.mkdir(exist_ok=True)
    APPROVED_DIR.mkdir(exist_ok=True)
    DONE_DIR.mkdir(exist_ok=True)

    logger.info("=" * 50)
    logger.info("Approval Watcher Starting")
    logger.info(f"Monitoring: {PENDING_DIR}")
    logger.info(f"Monitoring: {APPROVED_DIR}")
    logger.info(f"Archive to: {DONE_DIR}")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 50)

    # Setup watchers
    pending_handler = PendingApprovalHandler()
    approved_handler = ApprovedHandler()

    observer_pending = Observer()
    observer_pending.schedule(pending_handler, str(PENDING_DIR), recursive=False)

    observer_approved = Observer()
    observer_approved.schedule(approved_handler, str(APPROVED_DIR), recursive=False)

    try:
        observer_pending.start()
        observer_approved.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping watcher...")
        observer_pending.stop()
        observer_approved.stop()
    except Exception as e:
        logger.error(f"Watcher error: {e}")
        observer_pending.stop()
        observer_approved.stop()

    observer_pending.join()
    observer_approved.join()
    logger.info("Watcher stopped.")


if __name__ == "__main__":
    main()
