---
id: 9
title: "G5 Cross-Domain Integration Implementation"
stage: general
date: 2026-03-10
surface: agent
model: claude-opus-4-6
feature: none
branch: master
user: cosmicnoob
command: "implement G5 cross-domain integration plan"
labels: ["gold-tier", "cross-domain", "domain-tagging", "unified-view", "calendar-integration"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - Company_Handbook.md
  - Watchers/filesystem_watcher.py
  - Watchers/gmail_watcher.py
  - Scripts/cross_domain.py
  - Scripts/ceo_briefing.py
  - Dashboard.md
  - Skills/cross_domain_integration.md
  - SPEC.md
tests:
  - "python3 Scripts/cross_domain.py --dry-run — prints unified summary"
  - "python3 Scripts/cross_domain.py --backfill --dry-run — shows files to tag"
  - "python3 Scripts/cross_domain.py --domain personal --json — filters personal"
  - "python3 Scripts/ceo_briefing.py --dry-run — includes Calendar Events, Personal Affairs, Business Operations, Cross-Domain Insights sections"
  - "filesystem_watcher.py includes domain: tag in task frontmatter"
  - "gmail_watcher.py includes domain: tag in email task frontmatter"
  - "Dashboard.md has 3 new domain panels"
  - "SPEC.md shows G5 checked, tier_progress 5/7, Gold 5/7, Skills 13"
---

## Prompt

Implement the following plan:

# G5 Cross-Domain Integration — Implementation Plan

[Full plan covering 5 phases: domain tagging in watchers, cross_domain.py module with DomainRouter/UnifiedView/backfill/CLI, CEO briefing enhancement with calendar data and domain-split sections, Dashboard domain panels, and skill documentation + SPEC updates.]

## Response

Implemented G5 Cross-Domain Integration across 8 files in 5 phases:

**Phase 1 — Domain Tagging:**
- Company_Handbook.md: Added `domain: personal|business|cross-domain` to frontmatter schema
- filesystem_watcher.py: Added BUSINESS_FILE_KEYWORDS detection + `domain:` tag in task frontmatter
- gmail_watcher.py: Added BUSINESS_SENDER_KEYWORDS detection + `domain:` tag in email task frontmatter

**Phase 2 — Cross-Domain Module:**
- Created Scripts/cross_domain.py with DomainRouter, UnifiedView, backfill_domains(), detect_cross_domain_insights(), CLI with --dry-run/--domain/--backfill/--json flags, calendar integration via MCP calendar_server

**Phase 3 — CEO Briefing Enhancement:**
- Replaced calendar placeholder with live calendar event data from UnifiedView
- Added Personal Affairs, Business Operations, and Cross-Domain Insights sections
- Graceful fallback when cross_domain module not available

**Phase 4 — Dashboard:**
- Added Cross-Domain Router to System Status table
- Added Personal Domain Status, Business Domain Status, and Cross-Domain Health panels with commands

**Phase 5 — Documentation:**
- Created Skills/cross_domain_integration.md (7-section format)
- Updated SPEC.md: G5 checked, tier_progress 5/7, Gold 5/7, Skills 13, added cross_domain.py to Scripts table
