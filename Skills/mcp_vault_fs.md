# MCP Vault Filesystem Skill

## Description
MCP server exposing 5 tools for safe vault file operations via the Model Context Protocol. All paths are validated to stay within the vault root directory. Write and move operations support dry-run preview mode. Uses atomic writes and audit logging for all operations.

## Capabilities
- Read files from the vault (truncated at 50K chars)
- Write files atomically via `safe_write()` with dry-run support
- Move files between vault folders with dry-run support
- List folder contents (excludes hidden files)
- Search vault files by text query (case-insensitive, up to 20 matches)
- Path traversal prevention — all paths validated to stay within vault
- Full audit logging of every operation to `Logs/audit.jsonl`

## Input Format
MCP tool calls with parameters:
```
read_file(path: str)
write_file(path: str, content: str, dry_run: bool = False)
move_file(source: str, destination: str, dry_run: bool = False)
list_folder(path: str = "")
search_vault(query: str, file_pattern: str = "*.md")
```

Paths can be absolute or relative to vault root.

## Output Format
All tools return a single string:
- **Success**: Operation result with details
- **Dry run**: Formatted preview block
- **Validation error**: `Error: <description>`
- **Path violation**: `Error: Path '...' resolves outside vault. Access denied.`

## Rules
1. All paths must resolve within `~/AI_Employee_Vault/` — traversal attempts are blocked and logged
2. Write operations should follow [[Company_Handbook]] thresholds — use dry-run first for sensitive files
3. `write_file` uses atomic writes (tmp + replace) to prevent partial writes
4. `read_file` truncates at 50,000 characters to prevent memory issues
5. `search_vault` returns at most 20 matches, case-insensitive
6. Hidden files/folders (starting with `.`) are excluded from `list_folder` and `search_vault`
7. Path validation follows symlinks via `.resolve()` before checking boundaries

## Examples

### Example 1: Read a File
```
read_file(path="Dashboard.md")
-> "---\ntype: dashboard\ncreated: 2026-02-02\n..."
```

### Example 2: Write with Dry Run
```
write_file(path="Inbox/new_task.md", content="---\ntype: task\n---\n# New Task", dry_run=True)
-> "--- DRY RUN PREVIEW ---\nWould write to: /home/.../Inbox/new_task.md\nContent length: 35 chars\n..."
```

### Example 3: Move a File
```
move_file(source="Needs_Action/task.md", destination="Done/task.md")
-> "File moved: /home/.../Needs_Action/task.md -> /home/.../Done/task.md"
```

### Example 4: List Folder
```
list_folder(path="Skills")
-> "Contents of /home/.../Skills:\n📄 email_classifier.md\n📄 gmail_processor.md\n..."
```

### Example 5: Path Traversal Rejection
```
read_file(path="../../etc/passwd")
-> "Error: Path '../../etc/passwd' resolves outside vault. Access denied."
```

## Integration
- Audit logging: `Watchers/vault_audit.py` (`audit_log`, `safe_write`, `ErrorTracker`)
- Approval workflow: [[Company_Handbook]] (write operations may need approval)
- System status: [[Dashboard]]
- Related watcher: `Watchers/filesystem_watcher.py` (monitors Inbox/)
