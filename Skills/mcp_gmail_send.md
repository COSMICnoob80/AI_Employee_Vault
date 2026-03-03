# MCP Gmail Send Skill

## Description
MCP server exposing a `send_email` tool via the Gmail API. Allows Claude Code to send plain-text emails on behalf of the user through their authenticated Gmail account. Uses OAuth2 with a dedicated send-scope token separate from the read-only watcher.

## Capabilities
- Send plain-text emails via Gmail API
- Input validation (recipient, subject, body)
- Dry-run preview mode (no email sent)
- OAuth2 authentication with automatic token refresh
- Separate token file (`.gmail_token_send.json`) to avoid breaking the read-only watcher
- All errors returned as strings (never crashes the MCP server)

## Input Format
MCP tool call with parameters:
```
send_email(
    to: str,        # Recipient email address (must contain '@')
    subject: str,   # Email subject line (non-empty)
    body: str,      # Plain-text email body (non-empty)
    dry_run: bool   # Optional, default False. Preview without sending.
)
```

## Output Format
Returns a single string:
- **Success**: `Email sent successfully. Message ID: <id>`
- **Dry run**: Formatted preview block showing To/Subject/Body
- **Validation error**: `Error: <description>`
- **Auth error**: `Error: <description>`

## Rules
1. This tool does NOT enforce approval — Claude must follow [[Company_Handbook]] thresholds before calling `send_email` with `dry_run=False`
2. Recipient must contain `@`; subject and body must be non-empty
3. No CC/BCC support in v1 — single recipient only
4. Uses `gmail.send` scope only (cannot read emails)
5. OAuth port 8092 (avoids watcher ports 8090/8091)
6. First run requires browser-based OAuth consent flow

## Examples

### Example 1: Successful Send
```
send_email(to="client@example.com", subject="Invoice Attached", body="Please find the Q1 invoice attached.")
→ "Email sent successfully. Message ID: 18d4a2b3c5e6f7"
```

### Example 2: Dry Run Preview
```
send_email(to="boss@company.com", subject="Status Update", body="All tasks on track.", dry_run=True)
→ "--- DRY RUN PREVIEW ---\nTo: boss@company.com\nSubject: Status Update\nBody:\nAll tasks on track.\n--- END PREVIEW (not sent) ---"
```

### Example 3: Validation Error
```
send_email(to="not-an-email", subject="Test", body="Hello")
→ "Error: Invalid recipient address 'not-an-email'. Must contain '@'."
```

### Example 4: Auth Error
```
send_email(to="user@example.com", subject="Test", body="Hello")
→ "Error: Credentials file not found: /home/.../credentials.json. Download from Google Cloud Console."
```

## Integration
- Approval workflow: [[Company_Handbook]] (email sends require approval)
- Email handling: [[gmail_processor]]
- System status: [[Dashboard]]
- Related watcher: `Watchers/gmail_watcher.py` (read-only, separate token)
