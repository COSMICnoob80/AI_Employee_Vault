# MCP Vault Filesystem

Safe file operations within the AI Employee Vault via MCP tools.

## Triggers
- "read vault file"
- "write to vault"
- "move file"
- "list vault folder"
- "search vault"
- "vault filesystem"

## Instructions

When the user asks to interact with vault files:

1. **Read files** - Use the `read_file` MCP tool to read any file within the vault. Paths can be relative (e.g. "Dashboard.md") or absolute.

2. **Write files** - Use `write_file` with `dry_run=True` first to preview, then with `dry_run=False` to write. Follow [[Company_Handbook]] thresholds for sensitive files.

3. **Move files** - Use `move_file` to move files between vault folders (e.g. Needs_Action to Done). Use dry-run first for important moves.

4. **List folders** - Use `list_folder` to see folder contents. Call with no path for vault root.

5. **Search** - Use `search_vault` to find text across vault files. Supports glob patterns for file filtering (default: `*.md`).

## Notes
- All paths are validated to stay within the vault — path traversal is blocked
- Write operations use atomic writes to prevent data corruption
- All operations are logged to `Logs/audit.jsonl`
- See `Skills/mcp_vault_fs.md` for full documentation
