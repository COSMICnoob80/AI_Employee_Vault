# Inbox Processor Skill

## Description
Monitors the `Inbox/` directory for new files and automatically creates structured task files in `Needs_Action/` with YAML frontmatter metadata. Works via the [[filesystem_watcher.py|Filesystem Watcher]] using the watchdog library for real-time file detection.

## Capabilities
- Detect new files dropped into `Inbox/` in real time
- Generate YAML frontmatter with type, source, timestamp, status, and priority
- Create task files with standardized naming: `YYYYMMDD_HHMMSS_<filename>.md`
- Read text file content and embed it in the task (truncated at 2000 chars)
- Handle binary files gracefully with size-only metadata
- Skip hidden files (dotfiles) automatically
- Track processed files to prevent duplicate task creation
- Log all activity to `Logs/watcher.log`

## Input Format
Any file dropped into the `Inbox/` directory:
```
Inbox/
  └── <filename>.<ext>
```

Supported inputs:
- Text files (`.txt`, `.md`, `.csv`, etc.) — content is read and embedded
- Binary files (images, PDFs, archives) — logged as binary with file size
- Any other file type — best-effort read, fallback to error message

## Output Format
A Markdown task file created in `Needs_Action/` with this structure:
```markdown
---
type: file_drop
source: <original filename>
received: <ISO 8601 timestamp>
status: pending
priority: normal
---

# Task: Process <filename>

## Source File
- **Filename**: <original filename>
- **Received**: <formatted timestamp>
- **Size**: <bytes> bytes

## Original Content
\`\`\`
<file content, truncated at 2000 chars>
\`\`\`

## Actions
- [ ] Review content
- [ ] Categorize appropriately
- [ ] Take required action
- [ ] Move to Done when complete
```

## Rules

### File Handling
1. Only process files, not directories
2. Skip hidden files (names starting with `.`)
3. Wait 0.5s after detection to ensure the file is fully written
4. Read text files as UTF-8; fall back to binary descriptor on decode errors

### Naming Conventions
1. Task filename format: `YYYYMMDD_HHMMSS_<stem>.md` where `<stem>` is the original filename without extension
2. Timestamps use the moment of processing, not file creation time

### Priority Assignment
1. All file drops default to `priority: normal`
2. Priority escalation is handled downstream by [[task_planner]] or [[email_classifier]]

### Duplicate Detection
1. Maintain an in-memory set of processed file paths
2. Skip files that have already been processed in the current session
3. On watcher restart, the processed set resets (files already moved out of Inbox won't re-trigger)

## Examples

### Example 1: Text File Drop
**Input:** `Inbox/meeting_notes.txt` (340 bytes)
```
Meeting with client re: Q2 deliverables.
Action items:
- Send revised proposal by Friday
- Schedule follow-up call next week
```

**Output:** `Needs_Action/20260227_143022_meeting_notes.md`
```yaml
---
type: file_drop
source: meeting_notes.txt
received: 2026-02-27T14:30:22
status: pending
priority: normal
---
```
Content embedded in full under `## Original Content`.

---

### Example 2: Document Drop
**Input:** `Inbox/invoice_feb.pdf` (245,000 bytes, binary)

**Output:** `Needs_Action/20260227_150105_invoice_feb.md`
```yaml
---
type: file_drop
source: invoice_feb.pdf
received: 2026-02-27T15:01:05
status: pending
priority: normal
---
```
Original Content section shows: `[Binary file - 245000 bytes]`

---

### Example 3: Unknown File Type
**Input:** `Inbox/data_export.jsonl` (12,500 bytes, text)

**Output:** `Needs_Action/20260227_160830_data_export.md`
```yaml
---
type: file_drop
source: data_export.jsonl
received: 2026-02-27T16:08:30
status: pending
priority: normal
---
```
Content read as UTF-8 text, truncated at 2000 characters if needed.

---

### Example 4: Duplicate File (Skipped)
**Input:** `Inbox/meeting_notes.txt` dropped again in the same session

**Output:** No new task created. Watcher log shows the file was already processed and skipped.

---

## Integration

- New tasks appear on [[Dashboard]] Active Tasks
- Tasks feed into [[task_planner]] for plan generation
- Email-originated files cross-reference [[email_classifier]] categories
- All actions follow [[Company_Handbook]] guidelines for review and approval thresholds
