# Social Media Poster Skill

## Description
Automated social media posting to Facebook, Instagram, and Twitter/X via Playwright browser automation. Watches the `Approved/` directory for files marked with `action_type: facebook_post | instagram_post | twitter_post`, posts their content to the respective platform, and archives completed posts to `Done/`. Uses persistent browser sessions per platform for headless operation after initial manual login.

## Capabilities
- Post text content to Facebook, Instagram, and Twitter/X via Playwright (Chromium)
- Platform adapter abstraction (FacebookAdapter, InstagramAdapter, TwitterAdapter)
- Per-platform persistent session management (login once, reuse across runs)
- Human-in-the-loop approval gate (posts must be in `Approved/` first)
- Dry-run mode for previewing posts without browser interaction
- Single-check mode for cron integration (`--once`)
- Platform-specific content validation (character limits per platform)
- Automatic archival to `Done/` with posted timestamp
- Human-like delays to reduce automation detection
- Per-platform error tracking with circuit breaker
- Screenshot capture for debugging (`Logs/screenshots/social/`)
- Summary report generation (`--summary`)
- MCP server for creating approval requests programmatically
- Audit logging of all post events to `Logs/audit.jsonl`

## Input Format
Markdown file in `Approved/` with YAML frontmatter:
```yaml
---
type: approval_request
action_type: facebook_post | instagram_post | twitter_post
platform: facebook | instagram | twitter
status: approved
priority: normal
requester: AI_Employee
created: 2026-03-14T12:00:00
---

# Social Media Post — Facebook

## Post Content

Your post text goes here. This section is extracted and posted to the platform.

## Approval Actions
- [x] Approve
```

The `## Post Content` section is extracted as the post body. If no such section exists, all non-heading, non-checkbox body text is used as fallback.

## Output Format
Archived file in `Done/` with updated frontmatter:
```yaml
---
type: approval_request
action_type: facebook_post
platform: facebook
status: done
posted: 2026-03-14T14:30:00.000000
priority: normal
requester: AI_Employee
created: 2026-03-14T12:00:00
---
```

Log entries in `Logs/social_poster.log`:
```
2026-03-14 14:30:00 [INFO] Found 1 facebook post(s) to process
2026-03-14 14:30:05 [INFO] Posting to facebook from fb_update.md...
2026-03-14 14:30:15 [INFO] Facebook post submitted successfully
2026-03-14 14:30:15 [INFO] Archived to Done: fb_update.md
```

## Rules

### Approval Gate
1. Posts MUST be in `Approved/` directory — never post from `Pending_Approval/` or `Inbox/`
2. File must have appropriate `action_type` in frontmatter (`facebook_post`, `instagram_post`, or `twitter_post`)
3. All social media posts require human approval per [[Company_Handbook]] (social media threshold)
4. MCP tools create files in `Pending_Approval/` — human moves to `Approved/` to trigger posting

### Content Validation
1. Post text must not be empty
2. Platform character limits: Facebook 63,206 / Instagram 2,200 / Twitter 280
3. Posts exceeding the limit are skipped with a warning
4. Instagram V1 is text-only — warns if no image provided (image upload planned for future)

### Session Management
1. First run per platform must be interactive (headed browser) for manual login
2. Sessions saved to `.social_sessions/{platform}/state.json` (excluded from git)
3. Session validity checked before each posting batch
4. If session expired, script logs error and exits (re-run interactively to re-login)

### Posting Behavior
1. Human-like delays between actions (2-5 seconds) to reduce detection
2. 30-60 second delay between consecutive posts
3. Failed posts remain in `Approved/` for retry
4. Successfully posted files are archived to `Done/` with `posted:` timestamp
5. Screenshots saved to `Logs/screenshots/social/` for debugging

## Examples

### Example 1: Facebook Post (Dry Run)
```bash
python Scripts/social_poster.py --platform facebook --dry-run --once
```
```
2026-03-14 14:30:00 [INFO] Mode: DRY RUN (no browser)
2026-03-14 14:30:00 [INFO] Found 1 facebook post(s) to process
2026-03-14 14:30:00 [INFO] [DRY RUN] Would post to facebook from fb_update.md: Building an AI Employee...
```

### Example 2: Twitter Post Validation
Create a 300+ character file with `action_type: twitter_post` in Approved/:
```
2026-03-14 14:30:00 [INFO] Found 1 twitter post(s) to process
2026-03-14 14:30:00 [WARNING] twitter post long_tweet.md: Exceeds 280 chars (305 chars) — skipping
```

### Example 3: All Platforms
```bash
python Scripts/social_poster.py --platform all --once
```
Processes Facebook, Instagram, and Twitter posts sequentially.

### Example 4: Summary Report
```bash
python Scripts/social_poster.py --summary
```
Generates `Logs/social_summary.md` with per-platform post counts and history.

### Example 5: MCP Tool Usage
Use `post_twitter` MCP tool with `dry_run=True` to preview, then `dry_run=False` to create approval request.

## Integration

- Requires human approval via [[approval_requester]] before posting
- Follows [[Company_Handbook]] social media approval threshold
- Updates [[Dashboard]] Social Media Poster status
- Archives to `Done/` with audit trail
- Logs to `Logs/social_poster.log` in standard vault format
- Audit events logged to `Logs/audit.jsonl`
- Registered in [[scheduler]] for automated startup via `Scripts/schedule_watchers.sh`
- MCP server registered in `.claude/mcp.json` as `social-media`
- Social media activity included in CEO Briefing reports
