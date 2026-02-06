#!/usr/bin/env python3
"""
Gmail Watcher for AI Employee Vault

Monitors Gmail for important/urgent emails and creates task files
in Needs_Action with YAML frontmatter metadata.

Usage:
    python gmail_watcher.py              # Live mode
    python gmail_watcher.py --dry-run    # Test without creating files

Dependencies:
    pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""

import os
import sys
import time
import json
import logging
import argparse
import socket
from datetime import datetime
from pathlib import Path
from email.utils import parsedate_to_datetime
import base64
import re

# Force IPv4 — httplib2 fails on IPv6-only DNS resolution
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_getaddrinfo(*args, **kwargs):
    results = _orig_getaddrinfo(*args, **kwargs)
    ipv4 = [r for r in results if r[0] == socket.AF_INET]
    return ipv4 if ipv4 else results
socket.getaddrinfo = _ipv4_getaddrinfo

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    import httplib2
    from google_auth_httplib2 import AuthorizedHttp
except ImportError:
    print("Error: Google API libraries not installed.")
    print("Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# Configuration
VAULT_ROOT = Path.home() / "AI_Employee_Vault"
CREDENTIALS_FILE = VAULT_ROOT / "credentials.json"
TOKEN_FILE = VAULT_ROOT / ".gmail_token.json"
NEEDS_ACTION_DIR = VAULT_ROOT / "Needs_Action"
LOG_DIR = VAULT_ROOT / "Logs"
PROCESSED_IDS_FILE = VAULT_ROOT / ".gmail_processed_ids.json"

# Gmail API scope (read-only)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Keywords to watch for
PRIORITY_KEYWORDS = [
    "urgent", "asap", "invoice", "payment", "deadline",
    "critical", "important", "action required", "immediate",
    "time sensitive", "overdue", "final notice"
]

CHECK_INTERVAL = 120  # seconds

# Setup logging
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "gmail_watcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GmailWatcher:
    """Monitors Gmail for important/urgent emails."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.service = None
        self.processed_ids = self._load_processed_ids()
        self.retry_delay = 1  # For exponential backoff

    def _load_processed_ids(self) -> set:
        """Load previously processed message IDs."""
        if PROCESSED_IDS_FILE.exists():
            try:
                data = json.loads(PROCESSED_IDS_FILE.read_text())
                return set(data.get("processed_ids", []))
            except Exception as e:
                logger.warning(f"Could not load processed IDs: {e}")
        return set()

    def _save_processed_ids(self):
        """Save processed message IDs."""
        if not self.dry_run:
            data = {"processed_ids": list(self.processed_ids)}
            PROCESSED_IDS_FILE.write_text(json.dumps(data, indent=2))

    def authenticate(self) -> bool:
        """Authenticate with Gmail API using OAuth2."""
        creds = None

        # Load existing token
        if TOKEN_FILE.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            except Exception as e:
                logger.warning(f"Could not load token: {e}")

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Token refreshed successfully")
                except Exception as e:
                    logger.warning(f"Token refresh failed: {e}")
                    creds = None

            if not creds:
                if not CREDENTIALS_FILE.exists():
                    logger.error(f"Credentials file not found: {CREDENTIALS_FILE}")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_FILE), SCOPES
                )
                auth_port = 8090
                logger.info(f"Starting OAuth flow on port {auth_port}...")
                logger.info(f"If browser doesn't open, visit: http://localhost:{auth_port}")
                try:
                    creds = flow.run_local_server(
                        port=auth_port,
                        open_browser=True,
                        access_type="offline",
                        prompt="consent"
                    )
                except OSError:
                    # Port in use, try alternate
                    auth_port = 8091
                    logger.info(f"Port busy, retrying on {auth_port}...")
                    creds = flow.run_local_server(
                        port=auth_port,
                        open_browser=True,
                        access_type="offline",
                        prompt="consent"
                    )
                logger.info("OAuth authentication successful")

            # Always save token (even in dry-run, auth is real)
            TOKEN_FILE.write_text(creds.to_json())
            logger.info(f"Token saved to {TOKEN_FILE}")

        try:
            authed_http = AuthorizedHttp(creds, http=httplib2.Http(timeout=30))
            self.service = build("gmail", "v1", http=authed_http, cache_discovery=False)
            logger.info("Gmail API service built, testing connection...")
            profile = self.service.users().getProfile(userId="me").execute()
            logger.info(f"Connected as: {profile.get('emailAddress', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Gmail API: {e}")
            logger.info("Token is saved - try running again, network may have been slow.")
            return False

    def _check_keywords(self, text: str) -> list:
        """Check text for priority keywords."""
        text_lower = text.lower()
        matched = []
        for keyword in PRIORITY_KEYWORDS:
            if keyword in text_lower:
                matched.append(keyword)
        return matched

    def _get_email_body(self, payload: dict) -> str:
        """Extract email body from payload."""
        body = ""

        if "body" in payload and payload["body"].get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        elif "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain" and part["body"].get("data"):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                    break
                elif part["mimeType"] == "text/html" and part["body"].get("data") and not body:
                    html = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                    body = re.sub(r"<[^>]+>", "", html)  # Strip HTML tags

        return body.strip()

    def _get_header(self, headers: list, name: str) -> str:
        """Get header value by name."""
        for header in headers:
            if header["name"].lower() == name.lower():
                return header["value"]
        return ""

    def fetch_important_emails(self) -> list:
        """Fetch unread important emails."""
        emails = []

        try:
            # Query for unread emails that are important OR match keywords
            queries = [
                "is:unread is:important",
                "is:unread label:important"
            ]

            message_ids = set()

            for query in queries:
                results = self.service.users().messages().list(
                    userId="me", q=query, maxResults=20
                ).execute()
                for msg in results.get("messages", []):
                    message_ids.add(msg["id"])

            # Also check recent unread for keywords
            results = self.service.users().messages().list(
                userId="me", q="is:unread newer_than:1d", maxResults=50
            ).execute()

            for msg in results.get("messages", []):
                if msg["id"] not in message_ids:
                    # Fetch to check keywords
                    full_msg = self.service.users().messages().get(
                        userId="me", id=msg["id"], format="metadata",
                        metadataHeaders=["Subject"]
                    ).execute()
                    subject = self._get_header(full_msg.get("payload", {}).get("headers", []), "Subject")
                    if self._check_keywords(subject):
                        message_ids.add(msg["id"])

            # Fetch full details for each message
            for msg_id in message_ids:
                if msg_id in self.processed_ids:
                    continue

                full_msg = self.service.users().messages().get(
                    userId="me", id=msg_id, format="full"
                ).execute()
                emails.append(full_msg)

            self.retry_delay = 1  # Reset on success
            return emails

        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            # Exponential backoff
            self.retry_delay = min(self.retry_delay * 2, 300)
            return []

    def create_task(self, email: dict):
        """Create a task file for an email."""
        headers = email.get("payload", {}).get("headers", [])
        msg_id = email["id"]

        sender = self._get_header(headers, "From")
        subject = self._get_header(headers, "Subject")
        date_str = self._get_header(headers, "Date")

        try:
            received = parsedate_to_datetime(date_str)
        except Exception:
            received = datetime.now()

        body = self._get_email_body(email.get("payload", {}))
        keywords_matched = self._check_keywords(f"{subject} {body}")

        # Determine priority
        priority = "high" if keywords_matched else "normal"
        if any(kw in ["urgent", "critical", "immediate", "asap"] for kw in keywords_matched):
            priority = "urgent"

        timestamp = datetime.now()
        task_filename = f"EMAIL_{msg_id[:8]}_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
        task_path = NEEDS_ACTION_DIR / task_filename

        # Gmail link
        gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{msg_id}"

        task_content = f"""---
type: email
message_id: {msg_id}
from: "{sender}"
subject: "{subject.replace('"', "'")}"
received: {received.isoformat()}
priority: {priority}
status: pending
keywords_matched: {json.dumps(keywords_matched)}
---

# Email: {subject[:50]}{'...' if len(subject) > 50 else ''}

## Details
- **From**: {sender}
- **Subject**: {subject}
- **Received**: {received.strftime('%Y-%m-%d %H:%M:%S')}
- **Priority**: {priority.upper()}
- **Keywords**: {', '.join(keywords_matched) if keywords_matched else 'none'}

## Email Preview

{body[:500]}{'...[truncated]' if len(body) > 500 else ''}

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Create follow-up task
- [ ] Archive after processing

## Links
- [Open in Gmail]({gmail_link})
- Related: [[Dashboard]] | [[gmail_processor]]
"""

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would create task: {task_filename}")
            logger.info(f"  From: {sender}")
            logger.info(f"  Subject: {subject}")
            logger.info(f"  Priority: {priority}")
        else:
            task_path.write_text(task_content, encoding="utf-8")
            logger.info(f"Task created: {task_filename}")

        self.processed_ids.add(msg_id)

    def run_once(self) -> dict:
        """Run a single check cycle. Returns stats."""
        stats = {"checked": 0, "new_tasks": 0, "errors": 0}

        emails = self.fetch_important_emails()
        stats["checked"] = len(emails)

        for email in emails:
            try:
                self.create_task(email)
                stats["new_tasks"] += 1
            except Exception as e:
                logger.error(f"Failed to process email: {e}")
                stats["errors"] += 1

        self._save_processed_ids()
        return stats

    def run(self):
        """Run continuous monitoring loop."""
        logger.info("=" * 50)
        logger.info("Gmail Watcher Starting")
        logger.info(f"Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        logger.info(f"Check interval: {CHECK_INTERVAL}s")
        logger.info(f"Output to: {NEEDS_ACTION_DIR}")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 50)

        try:
            while True:
                stats = self.run_once()
                logger.info(f"Check complete: {stats['checked']} emails, {stats['new_tasks']} new tasks")

                if self.retry_delay > 1:
                    logger.info(f"Backing off for {self.retry_delay}s due to errors")
                    time.sleep(self.retry_delay)
                else:
                    time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Stopping Gmail watcher...")
            self._save_processed_ids()
            logger.info("Gmail watcher stopped.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Gmail Watcher for AI Employee Vault")
    parser.add_argument("--dry-run", action="store_true", help="Test without creating files")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    # Ensure directories exist
    NEEDS_ACTION_DIR.mkdir(exist_ok=True)

    watcher = GmailWatcher(dry_run=args.dry_run)

    if not watcher.authenticate():
        logger.error("Authentication failed. Exiting.")
        sys.exit(1)

    if args.once:
        stats = watcher.run_once()
        logger.info(f"Single run complete: {stats}")
    else:
        watcher.run()


if __name__ == "__main__":
    main()
