---
id: 6
title: "G3 Ralph Wiggum Task Loop"
stage: general
date: 2026-03-06
surface: agent
model: claude-opus-4-6
feature: none
branch: master
user: cosmicnoob
command: "implement G3 Ralph Wiggum task loop"
labels: ["gold-tier", "task-loop", "automation", "queue", "approval-routing"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - Scripts/ralph_loop.py
  - Scripts/ralph_hooks.sh
  - .claude/hooks.json
  - .claude/skills/ralph-loop/SKILL.md
  - Skills/ralph_wiggum.md
  - Scripts/schedule_watchers.sh
  - Dashboard.md
  - SPEC.md
  - Skills/README.md
  - VERIFICATION_REPORT.md
tests:
  - "python3 Scripts/ralph_loop.py --scan-only — pass (27 tasks scanned, manifest written)"
  - "python3 Scripts/ralph_loop.py --dry-run --once — pass (27 tasks classified, no files moved)"
  - "touch .ralph_stop && python3 Scripts/ralph_loop.py --once — pass (stop sentinel detected, graceful exit)"
  - "bash Scripts/schedule_watchers.sh status — pass (ralph_loop shown in watcher list)"
---

## Prompt

Implement the following plan: Ralph Wiggum Task Loop (G3) - Implementation Plan. Build a persistent task completion loop that scans the vault's task queue, prioritizes work, executes autonomous tasks, routes approval-required items to human review, verifies completion, and reports. Uses Claude Code PostToolUse hooks for automatic audit logging.

## Response snapshot

Implemented G3 in full. Created 5 new files: (1) Scripts/ralph_loop.py — core Python runner with TaskQueue (scan/prioritize/manifest), ActionClassifier (autonomous vs needs_approval), TaskExecutor (execute/route/verify), RalphLoop (main loop with 30s interval, stop sentinel, signal handling, circuit breaker). Priority scoring: urgent=3, high=2, normal=1, low=0 with tiebreakers for plan availability, age, and type. (2) Scripts/ralph_hooks.sh — PostToolUse hook logging every tool action to Logs/audit.jsonl with flock concurrency. (3) .claude/hooks.json — PostToolUse hook config. (4) .claude/skills/ralph-loop/SKILL.md — Claude Code skill with triggers and instructions. (5) Skills/ralph_wiggum.md — 7-section vault skill doc. Modified 4 files: schedule_watchers.sh (added ralph_loop to WATCHERS), Dashboard.md (added Ralph Wiggum status section), SPEC.md (G3 checked, tier_progress 3/7, scripts/skills tables updated), VERIFICATION_REPORT.md (37-check G3 section). All 4 verification tests pass.
