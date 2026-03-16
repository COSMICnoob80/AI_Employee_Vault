---
id: 011
title: G7 Social Media FB IG Twitter Integration
stage: general
date: 2026-03-14
surface: agent
model: claude-opus-4-6
feature: none
branch: master
user: cosmicnoob
command: implement plan
labels: ["social-media", "g7", "gold-tier", "mcp", "playwright", "facebook", "instagram", "twitter"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - Scripts/social_poster.py
  - MCP/social_media_server.py
  - Skills/social_media_poster.md
  - .claude/skills/social-check/SKILL.md
  - .claude/mcp.json
  - Scripts/schedule_watchers.sh
  - Scripts/ceo_briefing.py
  - Dashboard.md
  - SPEC.md
  - .gitignore
tests:
  - python3 Scripts/social_poster.py --help (shows --platform, --dry-run, --once, --summary)
  - python3 Scripts/social_poster.py --platform all --dry-run --once (exit 0)
  - Twitter 280-char validation (warns about 342-char post)
  - MCP server imports OK
  - bash Scripts/schedule_watchers.sh status (shows social_poster)
  - python3 Scripts/ceo_briefing.py --dry-run (contains Social Media Activity)
  - python3 Scripts/social_poster.py --summary (generates Logs/social_summary.md)
  - SPEC.md tier_progress 7/7, G7 checked
  - Dashboard.md contains Social Media Status
  - .gitignore contains .social_sessions/
  - Skills/social_media_poster.md has 7 sections
  - .claude/skills/social-check/SKILL.md has triggers + instructions
---

## Prompt

Implement the following plan:

# G7: Social Media (FB/IG/Twitter) — Implementation Plan

## Context

G7 is the last Gold tier item (currently 6/7). Completing it brings the project to Gold 7/7. The task is to build a unified social media posting system for Facebook, Instagram, and Twitter/X, extending the existing Playwright-based linkedin_poster.py pattern, with full HITL approval, audit logging, MCP server, and CEO Briefing integration.

[Full plan provided with 5 phases: P1 social_poster.py, P2 MCP server, P3 skill docs, P4 integration updates, P5 spec/config updates]

## Response

Implemented all 5 phases of the G7 Social Media integration plan:

**P1: Scripts/social_poster.py** — Core social poster with PlatformAdapter ABC + FacebookAdapter, InstagramAdapter, TwitterAdapter. CLI with --platform, --dry-run, --once, --summary. Reuses vault_audit utilities (audit_log, retry, ErrorTracker, safe_write). Per-platform session management in .social_sessions/{platform}/state.json. Screenshots to Logs/screenshots/social/. Audit events: social_post_started, social_post_success, social_post_failed, social_session_expired.

**P2: MCP/social_media_server.py** — FastMCP server with 4 tools: post_facebook, post_instagram, post_twitter, get_social_summary. All default dry_run=True. Tools create HITL approval requests in Pending_Approval/, not direct posts.

**P3: Skill docs** — Skills/social_media_poster.md (7 sections) + .claude/skills/social-check/SKILL.md (triggers + numbered instructions).

**P4: Integration updates** — .claude/mcp.json (social-media entry), schedule_watchers.sh (social_poster in WATCHERS + session-check), ceo_briefing.py (collect_social_media_data() + Social Media Activity section + metrics), Dashboard.md (Social Media Status panel + system status row).

**P5: Spec/config** — SPEC.md (tier_progress 7/7, Gold ✅ 7/7, G7 checked, tables updated), .gitignore (.social_sessions/).

All 13 verification checks passed. Gold tier is now 7/7 complete.
