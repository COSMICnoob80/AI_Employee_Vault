---
id: 8
title: "G5-G7 Project Sub-Agents"
stage: general
date: 2026-03-08
surface: agent
model: claude-opus-4-6
feature: none
branch: master
user: cosmicnoob
command: "create project-level sub-agents for G5-G7"
labels: ["gold-tier", "subagents", "cross-domain", "verification", "mcp-testing"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/agents/verifier.md
  - .claude/agents/cross-domain.md
  - .claude/agents/mcp-tester.md
tests:
  - "file existence check — all 3 agents created in .claude/agents/"
  - "sync check — models, tools, and permissions match user sequence spec"
---

## Prompt

Create project-level sub-agents for G5-G7. Follow the provided sequence exactly:
1. Verifier Sub-Agent (Haiku, read-only, plan mode) — verification specialist checking against SPEC.md with ast.parse, 7-section format checks, pass/fail matrix
2. Cross-Domain Integrator Sub-Agent (Sonnet, all tools) — bridges Personal and Business domains for G5 cross-domain integration
3. MCP Tester Sub-Agent (Haiku, Bash+Read) — runs --dry-run on all MCP servers, validates schemas, checks audit integration, tests error recovery

Ensure no conflicts between agents and full sync with the provided sequence.

## Response

Created 3 project-level sub-agents in `.claude/agents/`:

**verifier.md** — Haiku model, Read/Grep/Glob/Bash tools, plan permissionMode (read-only enforced). 7-step verification protocol: SPEC.md line item check, ast.parse Python validation, 7-section skill format check, cross-reference check, pass/fail matrix output. Never modifies production files.

**cross-domain.md** — Sonnet model, all tools, default permissionMode. Covers Personal domain (Gmail, Calendar, tasks) and Business domain (LinkedIn, CEO Briefings, Business Goals, audit trail). 4-phase integration protocol: data discovery, pattern detection, unified view generation, integration point validation.

**mcp-tester.md** — Haiku model, Bash/Read tools only. Tests all 3 MCP servers (Gmail Send, Filesystem, Calendar) with 6-step protocol: syntax validation, dry-run execution, tool schema validation, audit log integration, error recovery paths, MCP config validation. Always uses --dry-run, never sends real data.

All agents are in sync with the user's sequence — no conflicts in scope, tools, or permissions.
