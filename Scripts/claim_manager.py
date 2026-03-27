#!/usr/bin/env python3
"""
Claim Manager — Claim-by-Move Coordination for Multi-Agent Vault

Provides atomic file claiming via filesystem moves to prevent duplicate
processing when multiple agents (cloud, local) operate on the same vault.

Usage (as module):
    from claim_manager import ClaimManager
    cm = ClaimManager("cloud_agent", VAULT_ROOT)
    if not cm.is_claimed("EMAIL_001.md"):
        dest = cm.claim(Path("Needs_Action/EMAIL_001.md"))
        # ... process ...
        cm.release("EMAIL_001.md", Path("Pending_Approval"))
"""

import logging
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Watchers"))

from vault_audit import audit_log

logger = logging.getLogger(__name__)


class ClaimManager:
    """Claim-by-move coordination for multi-agent vault operations.

    Each agent gets its own In_Progress/{agent_name}/ directory.
    Claiming = moving file there. Releasing = moving out.
    """

    def __init__(self, agent_name: str, vault_root: Path):
        self.agent_name = agent_name
        self.vault_root = vault_root
        self.work_dir = vault_root / "In_Progress" / agent_name
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def is_claimed(self, filename: str) -> bool:
        """Check if a file is claimed by ANY agent (scan all In_Progress/*/)."""
        in_progress = self.vault_root / "In_Progress"
        if not in_progress.exists():
            return False
        for agent_dir in in_progress.iterdir():
            if agent_dir.is_dir() and (agent_dir / filename).exists():
                logger.debug(f"{filename} claimed by {agent_dir.name}")
                return True
        return False

    def claim(self, source_path: Path) -> Path | None:
        """Move file to In_Progress/{agent}/.

        Returns destination path on success, None if already claimed or missing.
        """
        if not source_path.exists():
            logger.warning(f"Cannot claim {source_path.name}: file not found")
            return None

        filename = source_path.name
        if self.is_claimed(filename):
            logger.info(f"Skip {filename}: already claimed")
            return None

        dest = self.work_dir / filename
        try:
            shutil.move(str(source_path), str(dest))
        except (OSError, shutil.Error) as e:
            logger.error(f"Claim failed for {filename}: {e}")
            return None

        audit_log("task_claimed", self.agent_name, {
            "file": filename,
            "source": str(source_path.parent.name),
            "dest": str(dest),
        })
        logger.info(f"Claimed: {filename} -> In_Progress/{self.agent_name}/")
        return dest

    def release(self, filename: str, dest_dir: Path) -> Path | None:
        """Move file from In_Progress/{agent}/ to target directory.

        Returns destination path on success, None on failure.
        """
        src = self.work_dir / filename
        if not src.exists():
            logger.warning(f"Cannot release {filename}: not in work dir")
            return None

        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filename
        try:
            shutil.move(str(src), str(dest))
        except (OSError, shutil.Error) as e:
            logger.error(f"Release failed for {filename}: {e}")
            return None

        audit_log("task_released", self.agent_name, {
            "file": filename,
            "dest": str(dest_dir.name),
        })
        logger.info(f"Released: {filename} -> {dest_dir.name}/")
        return dest

    def list_claimed(self) -> list[Path]:
        """List all files currently claimed by this agent."""
        if not self.work_dir.exists():
            return []
        return [f for f in sorted(self.work_dir.iterdir()) if f.is_file()]
