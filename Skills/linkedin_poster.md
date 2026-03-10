# LinkedIn Poster Skill

## Description
Automated LinkedIn text posting via Playwright browser automation. Watches the `Approved/` directory for files marked with `action_type: linkedin_post`, posts their text content to LinkedIn, and archives completed posts to `Done/`. Uses persistent browser sessions for seamless headless operation after initial manual login.

## Capabilities
- Post text content to LinkedIn feed via Playwright (Chromium)
- Persistent session management (login once, reuse across runs)
- Human-in-the-loop approval gate (posts must be in `Approved/` first)
- Dry-run mode for previewing posts without browser interaction
- Single-check mode for cron integration (`--once`)
- Post length validation (max 3000 characters)
- Automatic archival to `Done/` with posted timestamp
- Human-like delays to reduce automation detection

## Input Format
Markdown file in `Approved/` with YAML frontmatter:
```yaml
---
type: approval_request
action_type: linkedin_post
status: approved
priority: normal
requester: AI_Employee
created: 2026-03-03T12:00:00
---

# LinkedIn Post Draft

## Post Content

Your post text goes here. This section is extracted and posted to LinkedIn.

## Approval Actions
- [x] Approve
```

The `## Post Content` section is extracted as the post body. If no such section exists, all non-heading, non-checkbox body text is used as fallback.

## Output Format
Archived file in `Done/` with updated frontmatter:
```yaml
---
type: approval_request
action_type: linkedin_post
status: done
posted: 2026-03-03T14:30:00.000000
priority: normal
requester: AI_Employee
created: 2026-03-03T12:00:00
---
```

Log entries in `Logs/linkedin.log`:
```
2026-03-03 14:30:00 [INFO] Found 1 LinkedIn post(s) to process
2026-03-03 14:30:05 [INFO] Posting from linkedin_draft_test.md...
2026-03-03 14:30:15 [INFO] Post submitted successfully
2026-03-03 14:30:15 [INFO] Archived to Done: linkedin_draft_test.md
```

## Rules

### Approval Gate
1. Posts MUST be in `Approved/` directory — never post from `Pending_Approval/` or `Inbox/`
2. File must have `action_type: linkedin_post` in frontmatter
3. All social media posts require human approval per [[Company_Handbook]] (social media threshold)

### Content Validation
1. Post text must not be empty
2. Maximum 3000 characters (LinkedIn's limit for text posts)
3. Posts exceeding the limit are skipped with a warning
4. Text only — no images, documents, or polls in v1

### Session Management
1. First run must be interactive (headed browser) for manual LinkedIn login
2. Session saved to `.linkedin_session/state.json` (excluded from git)
3. Session validity checked before each posting batch
4. If session expired, script logs error and exits (re-run interactively to re-login)
5. Sessions typically last several weeks

### Posting Behavior
1. Human-like delays between actions (2-5 seconds) to reduce detection
2. 30-60 second delay between consecutive posts
3. Failed posts remain in `Approved/` for retry
4. Successfully posted files are archived to `Done/` with `posted:` timestamp

## Examples

### Example 1: Successful Post
**Input:** `Approved/linkedin_update.md`
```
2026-03-03 14:30:00 [INFO] Found 1 LinkedIn post(s) to process
2026-03-03 14:30:05 [INFO] Posting from linkedin_update.md...
2026-03-03 14:30:15 [INFO] Post submitted successfully
2026-03-03 14:30:15 [INFO] Archived to Done: linkedin_update.md
```
**Result:** File moved to `Done/linkedin_update.md` with `status: done` and `posted:` timestamp.

### Example 2: Dry Run
```bash
python Scripts/linkedin_poster.py --dry-run --once
```
```
2026-03-03 14:30:00 [INFO] Mode: DRY RUN (no browser)
2026-03-03 14:30:00 [INFO] Found 2 LinkedIn post(s) to process
2026-03-03 14:30:00 [INFO] [DRY RUN] Would post from post1.md: Building an AI Employee...
2026-03-03 14:30:00 [INFO] [DRY RUN] Would post from post2.md: Excited to announce...
```
**Result:** No browser launched, no posts made, files unchanged.

### Example 3: Session Expired
```
2026-03-03 14:30:00 [INFO] Found 1 LinkedIn post(s) to process
2026-03-03 14:30:05 [WARNING] LinkedIn session expired or invalid
2026-03-03 14:30:05 [ERROR] LinkedIn session expired. Run script interactively to re-login.
```
**Result:** No posts made. User must run `python Scripts/linkedin_poster.py` interactively.

### Example 4: Post Too Long
```
2026-03-03 14:30:00 [INFO] Found 1 LinkedIn post(s) to process
2026-03-03 14:30:00 [WARNING] Post long_post.md exceeds 3000 chars (4521 chars) — skipping
```
**Result:** File left in `Approved/` for editing.

## Integration

- Requires human approval via [[approval_requester]] before posting
- Follows [[Company_Handbook]] social media approval threshold
- Updates [[Dashboard]] LinkedIn Poster status
- Archives to `Done/` with audit trail
- Logs to `Logs/linkedin.log` in standard vault format
- Registered in [[scheduler]] for automated startup via `Scripts/schedule_watchers.sh`
