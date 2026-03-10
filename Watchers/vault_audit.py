#!/usr/bin/env python3
"""
Vault Audit & Error Recovery Utilities

Shared module providing:
- JSON Lines audit logging (Logs/audit.jsonl)
- Atomic file writes (safe_write)
- Retry decorator with exponential backoff
- Error tracking with circuit breaker
"""

import os
import json
import time
import fcntl
import random
import logging
import functools
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path.home() / "AI_Employee_Vault"
AUDIT_LOG_PATH = VAULT_ROOT / "Logs" / "audit.jsonl"

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. JSON Lines Audit Logger
# ---------------------------------------------------------------------------

def audit_log(event: str, source: str, details: dict = None, status: str = "ok",
              error: str = None):
    """Append a single JSON line to Logs/audit.jsonl.

    Uses file locking (fcntl.flock) so multiple watchers can write safely.

    Args:
        event:   e.g. watcher_start, email_processed, file_detected, error
        source:  e.g. gmail_watcher, filesystem_watcher, approval_watcher
        details: arbitrary dict with context
        status:  ok | error | retry
        error:   error message string (optional)
    """
    entry = {
        "ts": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "event": event,
        "source": source,
        "details": details or {},
        "status": status,
    }
    if error:
        entry["error"] = error

    line = json.dumps(entry, separators=(",", ":")) + "\n"

    try:
        AUDIT_LOG_PATH.parent.mkdir(exist_ok=True)
        fd = os.open(str(AUDIT_LOG_PATH), os.O_WRONLY | os.O_CREAT | os.O_APPEND)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            os.write(fd, line.encode("utf-8"))
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
    except Exception as exc:
        # Audit must never crash the caller
        logger.warning(f"Audit write failed: {exc}")


# ---------------------------------------------------------------------------
# 2. Atomic File Write
# ---------------------------------------------------------------------------

def safe_write(path: Path, content: str, encoding: str = "utf-8"):
    """Write content atomically via tmp + os.replace.

    Writes to path.tmp first, then replaces. This prevents partial writes
    on crash (the file is either the old version or the new one, never half).
    """
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(content, encoding=encoding)
    os.replace(str(tmp_path), str(path))


# ---------------------------------------------------------------------------
# 3. Retry Decorator
# ---------------------------------------------------------------------------

def retry(max_retries: int = 3, backoff_base: float = 2.0,
          retryable: tuple = (ConnectionError, TimeoutError, OSError)):
    """Decorator: retry on transient errors with exponential backoff + jitter.

    Logs each retry attempt to the audit log. Raises after max_retries.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        delay = (backoff_base ** attempt) + random.uniform(0, 1)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__}: "
                            f"{exc} (waiting {delay:.1f}s)"
                        )
                        audit_log(
                            "retry",
                            func.__module__ or "unknown",
                            {"function": func.__name__, "attempt": attempt + 1},
                            status="retry",
                            error=str(exc),
                        )
                        time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# 4. Error Tracker / Circuit Breaker
# ---------------------------------------------------------------------------

class ErrorTracker:
    """Track error rates and pause processing if threshold exceeded.

    If more than `threshold` errors occur within `window_seconds`, the tracker
    trips and calls to `check()` will sleep for `cooldown` seconds before
    allowing processing to resume.
    """

    def __init__(self, name: str, threshold: int = 10, window_seconds: int = 300,
                 cooldown: int = 60):
        self.name = name
        self.threshold = threshold
        self.window = window_seconds
        self.cooldown = cooldown
        self._errors: list[float] = []
        self._tripped = False

    def record_error(self, error_msg: str = ""):
        """Record an error occurrence."""
        now = time.time()
        self._errors.append(now)
        # Prune old entries
        cutoff = now - self.window
        self._errors = [t for t in self._errors if t > cutoff]

        if len(self._errors) >= self.threshold and not self._tripped:
            self._tripped = True
            logger.critical(
                f"ErrorTracker[{self.name}]: {len(self._errors)} errors in "
                f"{self.window}s — circuit breaker tripped"
            )
            audit_log(
                "circuit_breaker_tripped",
                self.name,
                {"error_count": len(self._errors), "window": self.window},
                status="error",
                error=error_msg,
            )

    def check(self) -> bool:
        """Check if processing should continue. Sleeps if tripped.

        Returns True if OK to proceed, False if still in cooldown.
        """
        if not self._tripped:
            return True

        logger.warning(
            f"ErrorTracker[{self.name}]: cooling down for {self.cooldown}s"
        )
        time.sleep(self.cooldown)

        # Reset after cooldown
        self._tripped = False
        self._errors.clear()
        audit_log(
            "circuit_breaker_reset",
            self.name,
            {"cooldown": self.cooldown},
            status="ok",
        )
        return True
