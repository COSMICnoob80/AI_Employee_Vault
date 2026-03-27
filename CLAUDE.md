# Claude Code Rules

**Last Updated:** 2026-03-19 12:47
**Project:** AI Employee Vault

> For universal project context (architecture, MCP servers, scripts, HITL rules, folder structure), see [`AGENTS.md`](AGENTS.md).
> This file covers **Claude Code-specific** features and workflows only.

---

## Core Guarantees

- Record every user input in a Prompt History Record (PHR) after every user message. Do not truncate.
- PHR routing (all under `history/prompts/`):
  - Constitution → `history/prompts/constitution/`
  - Feature-specific → `history/prompts/<feature-name>/`
  - General → `history/prompts/general/`
- ADR suggestions: when an architecturally significant decision is detected, suggest documenting. Never auto-create ADRs; require user consent.

## PHR Creation

After completing requests, create a PHR:
1. Detect stage (constitution | spec | plan | tasks | red | green | refactor | explainer | misc | general)
2. Generate title (3–7 words slug)
3. Route to appropriate `history/prompts/` subdirectory
4. Read template from `.specify/templates/phr-template.prompt.md`
5. Fill ALL placeholders (ID, TITLE, STAGE, DATE_ISO, MODEL, FILES_YAML, PROMPT_TEXT, RESPONSE_TEXT)
6. Write file, confirm path
7. Validate: no unresolved placeholders, title/stage/dates match, PROMPT_TEXT complete

## ADR Suggestions

When architecturally significant decisions are made, run three-part test (Impact + Alternatives + Scope all true), then suggest documenting.

## Human as Tool Strategy

Invoke the user when:
1. **Ambiguous Requirements** — Ask 2-3 clarifying questions
2. **Unforeseen Dependencies** — Surface and ask for prioritization
3. **Architectural Uncertainty** — Present options, get preference
4. **Completion Checkpoint** — Summarize and confirm next steps

## Execution Contract

1. Confirm surface and success criteria.
2. List constraints, invariants, non-goals.
3. Produce artifact with acceptance checks.
4. Add follow-ups and risks (max 3 bullets).
5. Create PHR in appropriate subdirectory.
6. Surface ADR suggestion if applicable.

## Claude-Specific Project Structure

- `.specify/memory/constitution.md` — Project principles
- `specs/<feature>/spec.md` — Feature requirements
- `specs/<feature>/plan.md` — Architecture decisions
- `specs/<feature>/tasks.md` — Testable tasks
- `history/prompts/` — Prompt History Records
- `history/adr/` — Architecture Decision Records

## Code Standards

See `.specify/memory/constitution.md` for code quality, testing, performance, security, and architecture principles.
