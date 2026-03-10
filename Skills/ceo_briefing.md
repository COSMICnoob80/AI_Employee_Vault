# CEO Briefing Skill

## Description
Aggregates all vault data into a structured weekly executive status report. Scans email tasks, completed items, LinkedIn activity, system health, and pending approvals to produce a single-file CEO briefing with actionable insights and KPI metrics.

## Capabilities
- Scan Needs_Action/ for email tasks grouped by priority (urgent/high/normal)
- Count files across all pipeline directories (Needs_Action, Done, Plans, Pending_Approval, Approved)
- Filter Done/ items by timestamp to identify completions within the target week
- Track LinkedIn posting activity (this week and all-time)
- Check watcher PID files for system liveness (running/stopped)
- Derive action items from urgent emails, pending approvals, and stopped watchers
- Generate YAML-frontmattered markdown reports with 9 structured sections
- Support dry-run mode, custom week targeting, and custom output paths

## Input Format
CLI invocation with optional flags:
```bash
# Current week (default)
python Scripts/ceo_briefing.py

# Dry run — print to stdout, no files created
python Scripts/ceo_briefing.py --dry-run

# Specific ISO week
python Scripts/ceo_briefing.py --week 2026-W10

# Custom output path
python Scripts/ceo_briefing.py --output Reports/custom_report.md
```

No input files required — the script reads vault directories directly.

## Output Format
Markdown file in `Reports/` with YAML frontmatter:
```yaml
---
type: ceo_briefing
week: "2026-W10"
generated: 2026-03-05T14:30:00.000000
period_start: 2026-03-02
period_end: 2026-03-08
---
```

Report sections:
1. **Executive Summary** — one-paragraph overview with attention callout
2. **Email Digest** — priority breakdown table and top items
3. **Calendar Events** — placeholder for future G4 integration
4. **Task Status** — directory counts and completed-this-week list
5. **LinkedIn Activity** — weekly and all-time post counts
6. **System Health** — watcher status table (running/stopped)
7. **Pending Approvals** — table of items awaiting human review
8. **Action Items** — derived checkbox list
9. **Metrics Summary** — KPI table

Log entries in `Logs/ceo_briefing.log`.

## Rules

### Autonomy
1. Report generation is an autonomous action per [[Company_Handbook]] — no approval gate needed
2. All vault reads are read-only; no files are modified except the output report
3. Reports directory is gitignored (generated output)

### Data Collection
1. Email tasks are identified by `EMAIL_*.md` filename pattern in Needs_Action/
2. Priority is read from YAML frontmatter `priority` field
3. Completed items are filtered by timestamp fields: `completed`, `posted`, `requested`, `created`
4. LinkedIn posts are identified by `action_type: linkedin_post` in Done/ frontmatter
5. System health checks use `os.kill(pid, 0)` on PID files — signal 0 tests liveness without affecting the process

### Week Targeting
1. Default: current ISO week (Monday–Sunday)
2. `--week YYYY-WNN` targets a specific week for historical reports
3. Week boundaries are inclusive (Monday 00:00 to Sunday 23:59)

### Output
1. Default path: `Reports/CEO_Briefing_YYYY-MM-DD.md` (using week's Monday date)
2. `--output` overrides the default path
3. `--dry-run` prints to stdout and writes no files

## Examples

### Example 1: Standard Weekly Run
```bash
python Scripts/ceo_briefing.py
```
```
2026-03-05 14:30:00 [INFO] CEO Briefing Generator Starting
2026-03-05 14:30:00 [INFO] Week: 2026-W10 (2026-03-02 to 2026-03-08)
2026-03-05 14:30:00 [INFO] Collecting vault data...
2026-03-05 14:30:00 [INFO] CEO Briefing written to: Reports/CEO_Briefing_2026-03-02.md
2026-03-05 14:30:00 [INFO] CEO Briefing Generator finished
```

### Example 2: Dry Run
```bash
python Scripts/ceo_briefing.py --dry-run
```
Prints full report to stdout. No files created. Log shows "Dry run complete — no file written".

### Example 3: Specific Week
```bash
python Scripts/ceo_briefing.py --week 2026-W09
```
Generates report for week 9 (Feb 23 – Mar 1), saved as `Reports/CEO_Briefing_2026-02-23.md`.

### Example 4: Custom Output Path
```bash
python Scripts/ceo_briefing.py --output ~/Desktop/weekly_report.md
```
Writes report to the specified path instead of `Reports/`.

## Integration

- Reads from [[email_classifier]] output files (EMAIL_*.md in Needs_Action/)
- Reads from [[approval_requester]] output files (Pending_Approval/*.md)
- Tracks [[linkedin_poster]] results (Done/ files with action_type: linkedin_post)
- Checks watcher health for [[scheduler]] managed processes
- Updates [[Dashboard]] CEO Briefing status section
- Logs to `Logs/ceo_briefing.log` in standard vault format
- Can be scheduled via [[scheduler]] cron for automated weekly runs
