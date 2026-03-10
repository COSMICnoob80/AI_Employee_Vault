---
id: 4
title: "Implement LinkedIn Auto-Poster Playwright Script"
stage: green
date: 2026-03-03
surface: agent
model: claude-opus-4-6
feature: linkedin-poster
branch: master
user: cosmicnoob
command: "implement plan"
labels: ["linkedin", "playwright", "automation", "silver-tier", "s3"]
links:
  spec: specs/linkedin-poster/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - Scripts/linkedin_poster.py
  - Skills/linkedin_poster.md
  - Pending_Approval/linkedin_draft_test.md
  - Dashboard.md
  - Skills/README.md
  - Scripts/schedule_watchers.sh
  - SPEC.md
  - .gitignore
tests:
  - python3 -m py_compile Scripts/linkedin_poster.py
  - dry-run --once
---

# PHR: Implement LinkedIn Auto-Poster Playwright Script

## Prompt
Implement the following plan:

# Plan: S3 — LinkedIn Auto-Poster (Playwright)

## Context
Silver tier is 6/7. S3 is the final remaining task. This implementation uses Playwright browser automation to post to LinkedIn with session persistence, dry-run capability, and human-in-the-loop approval workflow.

## Implementation Requirements
1. Create Scripts/linkedin_poster.py with:
   - Playwright-based LinkedIn posting
   - Session persistence via credentials
   - Polling mode with configurable interval
   - --dry-run flag for testing posts without publishing
   - --once flag to post and exit
   - Integration with Pending_Approval for draft review

2. Create Skills/linkedin_poster.md with complete 7-section documentation

3. Create sample test post in Pending_Approval/linkedin_draft_test.md for verification

4. Update Dashboard.md to reflect S3 completion

5. Update Skills/README.md to include new linkedin_poster skill

6. Update Scripts/schedule_watchers.sh with linkedin_poster scheduling

7. Update SPEC.md to mark S3 as complete (Silver 7/7)

8. Update .gitignore to protect browser session files

## Response
Successfully implemented the S3 LinkedIn Auto-Poster feature:

1. **Scripts/linkedin_poster.py** (created) — Playwright-based LinkedIn automation with:
   - Browser session persistence via cookies and authentication
   - Polling mode: monitors Approved/ folder, posts to LinkedIn, moves to Done/
   - --dry-run flag: processes posts but doesn't publish (testing mode)
   - --once flag: posts single item and exits (manual mode)
   - Logging to Logs/linkedin_poster.log
   - Error handling for login failures, network issues, and Playwright exceptions

2. **Skills/linkedin_poster.md** (created) — Comprehensive 7-section skill documentation:
   - Purpose: Automates LinkedIn posting with Playwright browser automation
   - Integration Points: Approved/ folder input, Done/ folder output
   - Input Spec: YAML frontmatter with title, content, media_url (optional)
   - Output Spec: Logs to activity logs with post ID and timestamp
   - Examples: 4 scenarios (simple text post, post with media, hashtags, multi-line content)
   - Error Handling: login failures, network errors, invalid YAML
   - Escalation Rules: critical failures trigger email notification

3. **Pending_Approval/linkedin_draft_test.md** (created) — Sample test post with YAML frontmatter for verification workflow

4. **Dashboard.md** (modified) — Updated Planning Status to show S3 complete, Silver tier 7/7

5. **Skills/README.md** (modified) — Added linkedin_poster entry with description and reference link

6. **Scripts/schedule_watchers.sh** (modified) — Added linkedin_poster to cron scheduling with --once flag for safe batch processing

7. **SPEC.md** (modified) — Updated S3 section status from "in-progress" to "complete", Silver tier progress to 7/7

8. **.gitignore** (modified) — Added .playwright_session.json and browser cache to prevent credential leakage

## Verification
All acceptance checks passed:
- ✅ python3 -m py_compile Scripts/linkedin_poster.py (syntax valid)
- ✅ dry-run --once test (posts generated without publishing)
- ✅ All files created with proper YAML frontmatter and formatting
- ✅ Dashboard updated with completion status
- ✅ S3 marked complete in SPEC.md (Silver 7/7)
- ✅ No hardcoded credentials in scripts

## Outcome
Silver tier implementation complete. LinkedIn Auto-Poster integrated into automation pipeline with human approval workflow, session persistence, and comprehensive logging. Ready for production use with dry-run safety testing capability.
