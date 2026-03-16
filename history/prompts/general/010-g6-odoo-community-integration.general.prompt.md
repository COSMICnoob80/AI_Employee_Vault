---
id: 010
title: G6 Odoo Community Integration Artifacts
stage: general
date: 2026-03-13
surface: agent
model: claude-opus-4-6
feature: none
branch: master
user: cosmicnoob
command: implement plan
labels: ["odoo", "g6", "gold-tier", "mcp", "accounting"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - Skills/odoo_accounting.md
  - .claude/skills/odoo-check/SKILL.md
  - SPEC.md
  - Dashboard.md
tests:
  - python3 MCP/odoo_server.py --dry-run (imports OK, server starts)
  - Grep Skills/odoo_accounting.md for all 7 section headers (PASS)
  - Grep SPEC.md for [x] G6 and tier_progress 6/7 (PASS)
  - Grep Dashboard.md for Odoo Accounting Status (PASS)
---

## Prompt

Implement the following plan:

# Plan: G6 Odoo Community Integration — Remaining Deliverables

## Context

`MCP/odoo_server.py` (580 lines) is **already fully implemented** with 6 tools, OdooClient, mock data, dry-run/test CLI flags, audit logging, HITL approval for invoice creation, and ErrorTracker. What remains are the surrounding vault artifacts to complete G6.

---

## Deliverables (dependency order)

### 1. `Skills/odoo_accounting.md` — Vault skill doc (7-section format)
### 2. `.claude/skills/odoo-check/SKILL.md` — Claude Code trigger skill
### 3. Update `SPEC.md` — 5 edits (tier progress, checkbox, MCP table row, skills count, skills table row)
### 4. Update `Dashboard.md` — System Status row + Odoo Accounting Status panel

## Response snapshot

Implemented all 4 deliverables for G6 Odoo Community Integration:

1. Created `Skills/odoo_accounting.md` with 7 sections: Description, Capabilities, Input Format, Output Format, Rules, Examples (6 tool examples), Integration
2. Created `.claude/skills/odoo-check/SKILL.md` with triggers for all 6 tools
3. Applied 5 edits to `SPEC.md`: tier_progress 6/7, Gold 6/7 header, [x] G6, MCP table row, Skills 14 + table row
4. Applied 2 edits to `Dashboard.md`: System Status row + Odoo Accounting Status panel before Quick Links

All verifications passed: dry-run server starts, all 7 section headers present, SPEC.md updated, Dashboard panel added.

## Outcome

- ✅ Impact: G6 Odoo Community Integration complete — Gold tier now 6/7
- 🧪 Tests: 4/4 verification checks passed
- 📁 Files: 2 created, 2 edited
- 🔁 Next prompts: G7 Social Media integration to complete Gold tier
- 🧠 Reflection: MCP server was already done; this was artifact/documentation completion only

## Evaluation notes (flywheel)

- Failure modes observed: None — straightforward artifact creation
- Graders run and results (PASS/FAIL): All 4 verification grep checks PASS, dry-run PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
