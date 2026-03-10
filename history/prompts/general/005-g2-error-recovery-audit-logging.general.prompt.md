---
id: 5
title: "G2 Error Recovery + Audit Logging"
stage: general
date: 2026-03-06
surface: agent
model: claude-opus-4-6
feature: none
branch: master
user: cosmicnoob
command: "implement G2 error recovery + audit logging"
labels: ["gold-tier", "error-recovery", "audit", "watchers", "reliability"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - Watchers/vault_audit.py
  - Watchers/gmail_watcher.py
  - Watchers/filesystem_watcher.py
  - Watchers/approval_watcher.py
  - .claude/skills/audit-check/SKILL.md
  - .gitignore
  - SPEC.md
tests:
  - "python3 -c 'from vault_audit import audit_log, safe_write, ErrorTracker' — pass"
  - "audit_log writes valid JSON to Logs/audit.jsonl with fcntl locking — pass"
  - "safe_write atomic tmp+replace pattern — pass"
  - "ErrorTracker trips after threshold errors in window — pass"
  - "ast.parse on all 3 modified watchers — pass (syntax OK)"
---

## Prompt

Read SPEC.md Gold requirements for error recovery. Implement try/except wrappers on all watchers, JSON audit log at Logs/audit.jsonl, and recovery procedures. Create .claude/skills/audit-check/SKILL.md for verification.

## Response snapshot

Implemented G2 in full. Created Watchers/vault_audit.py — shared stdlib-only module with 4 components: (1) audit_log() appends JSON Lines to Logs/audit.jsonl with fcntl file locking for concurrent watcher safety, (2) safe_write() atomic file writes via tmp+os.replace, (3) @retry decorator with exponential backoff+jitter and audit logging, (4) ErrorTracker circuit breaker that pauses processing after threshold errors in a time window. Modified all 3 watchers (gmail_watcher.py, filesystem_watcher.py, approval_watcher.py) to: import vault_audit, use ErrorTracker, audit log start/stop/error/task_created events, use safe_write for all file creation. Created .claude/skills/audit-check/SKILL.md verification skill. SPEC.md updated to tier_progress: 2/7, G2 marked complete.
