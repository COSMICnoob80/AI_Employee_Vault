#!/usr/bin/env python3
"""
MCP Gmail Send Server for AI Employee Vault

Exposes a single `send_email` tool via the Model Context Protocol.
Uses Gmail API with OAuth2 (gmail.send scope) and a separate token
from the read-only watcher to avoid scope conflicts.

Transport: stdio (standard for Claude Code)

Dependencies:
    pip install mcp google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""

import socket
import base64
from email.mime.text import MIMEText
from pathlib import Path

# Force IPv4 — httplib2 fails on IPv6-only DNS resolution
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_getaddrinfo(*args, **kwargs):
    results = _orig_getaddrinfo(*args, **kwargs)
    ipv4 = [r for r in results if r[0] == socket.AF_INET]
    return ipv4 if ipv4 else results
socket.getaddrinfo = _ipv4_getaddrinfo

from mcp.server.fastmcp import FastMCP
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import httplib2
from google_auth_httplib2 import AuthorizedHttp

# Configuration
VAULT_ROOT = Path.home() / "AI_Employee_Vault"
CREDENTIALS_FILE = VAULT_ROOT / "credentials.json"
TOKEN_FILE = VAULT_ROOT / ".gmail_token_send.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
OAUTH_PORT = 8092

mcp = FastMCP("gmail-send")


def get_gmail_service():
    """Authenticate with Gmail API using OAuth2 (gmail.send scope)."""
    creds = None

    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"Credentials file not found: {CREDENTIALS_FILE}. "
                    "Download from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(
                port=OAUTH_PORT,
                open_browser=True,
                access_type="offline",
                prompt="consent",
            )

        TOKEN_FILE.write_text(creds.to_json())

    authed_http = AuthorizedHttp(creds, http=httplib2.Http(timeout=30))
    return build("gmail", "v1", http=authed_http, cache_discovery=False)


@mcp.tool()
def send_email(to: str, subject: str, body: str, dry_run: bool = False) -> str:
    """Send a plain-text email via Gmail.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Plain-text email body.
        dry_run: If True, returns a preview without sending.

    Returns:
        Success message with message ID, preview string, or error description.
    """
    # Validate inputs
    if not to or "@" not in to:
        return f"Error: Invalid recipient address '{to}'. Must contain '@'."
    if not subject or not subject.strip():
        return "Error: Subject cannot be empty."
    if not body or not body.strip():
        return "Error: Body cannot be empty."

    if dry_run:
        return (
            f"--- DRY RUN PREVIEW ---\n"
            f"To: {to}\n"
            f"Subject: {subject}\n"
            f"Body:\n{body}\n"
            f"--- END PREVIEW (not sent) ---"
        )

    try:
        service = get_gmail_service()
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
        return f"Email sent successfully. Message ID: {result['id']}"
    except FileNotFoundError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error sending email: {e}"


if __name__ == "__main__":
    mcp.run()
