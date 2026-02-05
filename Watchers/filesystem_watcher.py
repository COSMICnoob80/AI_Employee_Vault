#!/usr/bin/env python3
"""
Filesystem Watcher for AI Employee Vault

Monitors the Inbox directory for new files and automatically creates
task files in Needs_Action with YAML frontmatter metadata.

Usage:
    python filesystem_watcher.py

Dependencies:
    pip install watchdog
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Error: watchdog not installed. Run: pip install watchdog")
    sys.exit(1)

# Configuration
VAULT_ROOT = Path.home() / "AI_Employee_Vault"
INBOX_DIR = VAULT_ROOT / "Inbox"
NEEDS_ACTION_DIR = VAULT_ROOT / "Needs_Action"
LOG_DIR = VAULT_ROOT / "Logs"

# Setup logging
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "watcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class InboxHandler(FileSystemEventHandler):
    """Handles new files dropped in the Inbox directory."""

    def __init__(self):
        self.processed_files = set()

    def on_created(self, event):
        """Called when a file is created in the watched directory."""
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
        """Read file and create task in Needs_Action."""
        logger.info(f"New file detected: {filepath.name}")

        # Read source content
        try:
            content = filepath.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = f"[Binary file - {filepath.stat().st_size} bytes]"
        except Exception as e:
            content = f"[Could not read file: {e}]"

        # Generate task filename
        timestamp = datetime.now()
        task_filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{filepath.stem}.md"
        task_path = NEEDS_ACTION_DIR / task_filename

        # Create task content with YAML frontmatter
        task_content = f"""---
type: file_drop
source: {filepath.name}
received: {timestamp.isoformat()}
status: pending
priority: normal
---

# Task: Process {filepath.name}

## Source File
- **Filename**: {filepath.name}
- **Received**: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- **Size**: {filepath.stat().st_size} bytes

## Original Content

```
{content[:2000]}{'...[truncated]' if len(content) > 2000 else ''}
```

## Actions
- [ ] Review content
- [ ] Categorize appropriately
- [ ] Take required action
- [ ] Move to Done when complete
"""

        # Write task file
        task_path.write_text(task_content, encoding='utf-8')
        logger.info(f"Task created: {task_path.name}")


def main():
    """Main entry point for the filesystem watcher."""
    # Ensure directories exist
    INBOX_DIR.mkdir(exist_ok=True)
    NEEDS_ACTION_DIR.mkdir(exist_ok=True)

    logger.info("=" * 50)
    logger.info("Filesystem Watcher Starting")
    logger.info(f"Monitoring: {INBOX_DIR}")
    logger.info(f"Output to:  {NEEDS_ACTION_DIR}")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 50)

    # Setup watcher
    event_handler = InboxHandler()
    observer = Observer()
    observer.schedule(event_handler, str(INBOX_DIR), recursive=False)

    try:
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping watcher...")
        observer.stop()
    except Exception as e:
        logger.error(f"Watcher error: {e}")
        observer.stop()

    observer.join()
    logger.info("Watcher stopped.")


if __name__ == "__main__":
    main()
