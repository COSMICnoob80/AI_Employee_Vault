# Cross-Domain Integration Skill

## Description
Bridges personal and business vault domains into a unified operational view. Provides domain tagging, routing, aggregation, backfill utilities, and cross-domain insight detection for the AI Employee Vault.

## Capabilities
- **Domain tagging**: Automatically tags new tasks with `domain: personal|business` based on sender/subject/filename heuristics
- **Domain routing**: `DomainRouter` class filters vault files by domain across Needs_Action/, Done/, Pending_Approval/
- **Unified views**: `UnifiedView` class aggregates email, calendar, tasks, LinkedIn, and system health into a single data structure
- **Cross-domain insights**: Detects patterns like email volume skew, stale approval queues, calendar load anomalies
- **Backfill**: One-shot utility to add `domain:` tags to all existing files missing the field
- **Calendar integration**: Imports from MCP calendar_server for live event data (graceful fallback if unavailable)
- **Audit logging**: All operations logged via vault_audit

## Input Format
CLI invocation with flags:
```bash
# Print unified summary (no file writes)
python Scripts/cross_domain.py --dry-run

# Filter by domain
python Scripts/cross_domain.py --domain personal
python Scripts/cross_domain.py --domain business

# Backfill existing files with domain tags
python Scripts/cross_domain.py --backfill --dry-run

# JSON output
python Scripts/cross_domain.py --json
```

Flags:
- `--dry-run` — print output, no file writes
- `--domain personal|business|all` — domain filter (default: all)
- `--backfill` — one-shot domain tag backfill for existing files
- `--json` — output as JSON instead of markdown

## Output Format
**Unified summary** (default markdown):
- Cross-Domain Summary heading with timestamp
- Email Tasks table (personal vs business counts)
- Calendar Events table (next 7 days, from MCP calendar)
- Tasks by Domain table (per-directory personal/business split)
- LinkedIn Activity (business domain, this week + all-time)
- System Health table (watcher status)
- Cross-Domain Insights (pattern-detected bullet list)

**JSON mode** (`--json`): Full unified dict with nested email, calendar, tasks, linkedin, system_health objects.

**Backfill mode**: Stats summary showing scanned/updated/skipped/errors counts.

Logs to `Logs/cross_domain.log`.

## Rules

### Domain Detection Heuristics
1. **Email tasks** (`type: email`): Check sender and subject for business keywords (invoice, payment, contract, finqalab, client, project, quarterly, compliance, hr@, finance@, billing). Default: personal.
2. **File drops** (`type: file_drop`): Check source filename for business keywords (invoice, contract, client, project, meeting-notes, quarterly, budget, proposal). Default: personal.
3. **LinkedIn posts** (`action_type: linkedin_post`): Always business.
4. **Other**: Default to personal.

### Graceful Degradation
1. Calendar data requires `MCP/calendar_server.py` token — returns `{"available": false}` when unavailable
2. CEO Briefing falls back to undivided format if cross_domain module is not importable
3. YAML parsing falls back to regex if pyyaml not installed
4. All errors logged but never crash the caller

### Audit Logging
1. Every `backfill_domains()` write logged as `domain_backfill` event
2. Every `UnifiedView.build()` logged as `unified_view_built` event
3. Every CLI run logged as `cross_domain_run` event

## Examples

### Example 1: Unified Summary
```bash
python Scripts/cross_domain.py --dry-run
```
```
Cross-Domain Summary — 2026-03-10 14:30
Domain filter: all

Email Tasks:  Personal=3, Business=2, Total=5
Calendar Events (7d): 2026-03-11T09:00 Team Standup
Tasks by Domain: needs_action P=4 B=1, done P=2 B=3
LinkedIn: 1 this week, 4 all-time
Cross-Domain Insights:
  - Personal tasks backlog: 5 tasks pending
```

### Example 2: Backfill Preview
```bash
python Scripts/cross_domain.py --backfill --dry-run
```
```
Backfill Results:
  Scanned: 12
  Updated: 8
  Skipped: 4
  Errors:  0
```

### Example 3: Business Domain JSON
```bash
python Scripts/cross_domain.py --domain business --json
```
```json
{
  "domain": "business",
  "email_count": 2,
  "linkedin": {"total_posts": 4, "this_week": 1, "domain": "business"},
  "tasks": {"needs_action": 1, "done": 3, "pending_approval": 1}
}
```

### Example 4: Personal Domain
```bash
python Scripts/cross_domain.py --domain personal
```
Outputs personal-only summary with email count, calendar events, and task counts.

## Integration
- **CEO Briefing** ([[ceo_briefing]]): Imports `UnifiedView` and `detect_cross_domain_insights` for domain-split report sections and live calendar data
- **Dashboard** ([[Dashboard]]): Three new panels (Personal Domain, Business Domain, Cross-Domain Health) reference cross_domain.py commands
- **Calendar Server** ([[mcp_vault_calendar]]): Imports `get_calendar_service` and `_list_events_api` for live event data
- **Filesystem Server** ([[mcp_vault_fs]]): Domain-tagged files are queryable via vault search
- **Vault Audit** (`vault_audit.py`): Uses `audit_log`, `safe_write`, `ErrorTracker` for all operations
- **Watchers**: `filesystem_watcher.py` and `gmail_watcher.py` both emit `domain:` tags on new tasks
