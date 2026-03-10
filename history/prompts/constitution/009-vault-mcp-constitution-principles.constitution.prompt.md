---
id: 009
title: Vault MCP Constitution Principles
stage: constitution
date: 2026-03-08
surface: agent
model: claude-opus-4-6
feature: none
branch: master
user: cosmicnoob
command: /sp.constitution
labels: ["constitution", "mcp", "vault-principles", "gold-tier"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
  - .claude/skills/gold-check/SKILL.md
  - .claude/skills/cross-domain-audit/SKILL.md
tests:
  - none
---

## Prompt

Create principles for vault MCP integration: all MCP servers must use FastMCP framework, include --dry-run, integrate vault_audit.py, follow 7-section skill documentation, respect vault boundary security constraints.

## Response snapshot

Created AI Employee Vault Constitution v1.0.0 with 6 core principles:
1. FastMCP Framework Mandate - all MCP servers use FastMCP with stdio transport
2. Dry-Run by Default - every server/script supports --dry-run preview
3. Vault Audit Integration - vault_audit.py for logging, safe_write, retry, circuit-breaker
4. 7-Section Skill Documentation - standardized skill format with 4+ examples
5. Vault Boundary Security - path validation, credential isolation, approval gates
6. Pipeline-First Architecture - all data flows through Inbox->Needs_Action->Done pipeline

Plus Security & Boundary Constraints section, Development Workflow section, and Governance with semantic versioning.

## Outcome

- ✅ Impact: Establishes foundational governance for all future vault MCP integrations (G4-G7)
- 🧪 Tests: N/A (governance document)
- 📁 Files: .specify/memory/constitution.md (new), 2 operational skills created
- 🔁 Next prompts: /sp.specify for G6 Odoo, /sp.specify for G7 Social Media
- 🧠 Reflection: Constitution codifies patterns already proven in G1-G4 implementations

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Run /sp.specify for Odoo to validate constitution gates work in planning
