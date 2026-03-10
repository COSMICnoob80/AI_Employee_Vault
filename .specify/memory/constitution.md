<!--
Sync Impact Report
- Version change: 0.0.0 → 1.0.0
- Modified principles: N/A (initial creation)
- Added sections: 6 Core Principles, Security & Boundary Constraints, Development Workflow, Governance
- Removed sections: None
- Templates requiring updates:
  - .specify/templates/plan-template.md ✅ compatible (Constitution Check section exists)
  - .specify/templates/spec-template.md ✅ compatible (requirements map to principles)
  - .specify/templates/tasks-template.md ✅ compatible (phase structure aligns)
- Follow-up TODOs: None
-->

# AI Employee Vault Constitution

## Core Principles

### I. FastMCP Framework Mandate

All MCP servers in the vault MUST use the FastMCP Python framework
(`from mcp.server.fastmcp import FastMCP`). This ensures a uniform
tool registration API, consistent stdio transport, and predictable
server lifecycle across all integrations.

- Every server MUST declare a named instance: `mcp = FastMCP("<name>")`
- Every server MUST expose at least one `@mcp.tool()` function
- Every server MUST terminate with `mcp.run()` for stdio transport
- Registration in `.claude/mcp.json` MUST use `command: python3` with
  absolute path to the server script

### II. Dry-Run by Default

Every MCP server and automation script MUST support a `--dry-run` mode
(or `dry_run` parameter for MCP tools) that previews behavior without
side effects. This is non-negotiable for safe iteration and testing.

- MCP tools: accept `dry_run: bool = False` parameter; return preview
  string when True
- CLI scripts: accept `--dry-run` flag; print output to stdout without
  writing files, sending messages, or calling external APIs
- Dry-run output MUST be realistic enough to verify correctness

### III. Vault Audit Integration

All watchers, MCP servers, and automation scripts MUST integrate with
`Watchers/vault_audit.py` for structured audit logging, atomic file
writes, retry resilience, and circuit-breaker protection.

- Import and use `audit_log()` for all significant events
- Import and use `safe_write()` for all file creation/modification
- Import and use `@retry` decorator on external API calls
- Instantiate `ErrorTracker` per component boundary for circuit breaking
- Audit log format: JSON Lines in `Logs/audit.jsonl` with `fcntl` locking

### IV. 7-Section Skill Documentation

Every capability (skill) added to the vault MUST have a corresponding
markdown file in `Skills/` following the standard 7-section format.
This ensures discoverability, testability, and consistent onboarding.

Required sections (in order):
1. Description
2. Capabilities
3. Input Format
4. Output Format
5. Rules
6. Examples (minimum 4 I/O pairs)
7. Integration (wikilinks to related vault files)

- Skill MUST be indexed in `Skills/README.md`
- Dashboard.md MUST reflect skill count and component status
- SPEC.md MUST list the skill in the Skills table

### V. Vault Boundary Security

All automation MUST respect the vault boundary defined by
`VAULT_ROOT = Path.home() / "AI_Employee_Vault"`. No script or MCP
server may read, write, or reference files outside this boundary
without explicit human approval.

- MCP filesystem operations MUST validate resolved paths stay within
  `VAULT_ROOT` (path traversal protection via `_validate_path()`)
- Credentials (`.gmail_token*.json`, `credentials.json`, `.env`,
  `.linkedin_session/`) MUST be in `.gitignore` and never committed
- OAuth tokens MUST use separate files per scope (read vs send vs
  calendar) to enforce least-privilege
- All external actions (email send, social post, financial operations)
  MUST pass through the human-in-the-loop approval gate per
  Company_Handbook thresholds

### VI. Pipeline-First Architecture

All vault operations MUST follow the established pipeline:
`Inbox -> Needs_Action -> Plans -> Approved -> Done` with
`Pending_Approval` as the human-in-the-loop gate. New integrations
MUST feed into this pipeline rather than creating parallel workflows.

- New data sources (Odoo, social media APIs) MUST create task files
  in `Needs_Action/` with YAML frontmatter
- Task files MUST include `type`, `created`, `status` fields minimum
- Cross-domain data MUST flow through the CEO Briefing aggregation
  system for unified reporting
- Wikilinks (`[[target]]`) MUST be used for cross-referencing

## Security & Boundary Constraints

- **Credential isolation**: Each external service MUST use a dedicated
  token file (e.g., `.gmail_token.json`, `.gmail_token_send.json`,
  `.calendar_token.json`) to prevent scope creep
- **Approval thresholds**: Financial operations >500 PKR, all external
  communications, all public postings, and all data modifications
  require human approval per Company_Handbook
- **No hardcoded secrets**: All secrets MUST use `.env` files or
  separate credential files excluded from version control
- **Read-only by default**: New API integrations MUST start with
  read-only scopes; write scopes require explicit justification
- **Atomic writes**: All file mutations MUST use `safe_write()` from
  `vault_audit.py` to prevent corruption from concurrent access

## Development Workflow

- **Smallest viable diff**: Changes MUST be minimal and focused on the
  current task; no unrelated refactoring
- **Watcher pattern**: Long-running monitors use the watcher pattern
  with PID files, graceful SIGTERM shutdown, and integration with
  `Scripts/schedule_watchers.sh`
- **Script discovery**: Scripts in `Watchers/` are auto-discovered;
  scripts in `Scripts/` require explicit registration in the WATCHERS
  array
- **Verification-driven**: Every new component MUST be independently
  verifiable via syntax check (`ast.parse`), dry-run test, and live
  E2E test documented in `VERIFICATION_REPORT.md`
- **Dashboard currency**: `Dashboard.md` MUST be updated with every
  new component (System Status row, metrics, command reference)
- **SPEC tracking**: `SPEC.md` MUST be updated with tier progress,
  component tables, and checklist items for every milestone

## Governance

- This constitution supersedes ad-hoc decisions; all new components
  MUST comply before merging
- Amendments require: (1) documented rationale, (2) impact assessment
  on existing components, (3) update to this file with version bump
- Version follows semantic versioning: MAJOR for principle
  removal/redefinition, MINOR for new principles, PATCH for
  clarifications
- Compliance review: every verification report MUST check constitution
  adherence as part of the validation checklist
- Use `CLAUDE.md` for runtime development guidance that supplements
  but does not override these principles

**Version**: 1.0.0 | **Ratified**: 2026-03-08 | **Last Amended**: 2026-03-08
