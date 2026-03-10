#!/usr/bin/env python3
"""
MCP Vault Filesystem Server for AI Employee Vault

Exposes 5 tools for safe vault file operations via the Model Context Protocol.
All paths are validated to stay within VAULT_ROOT. Write operations support
dry-run mode. Integrates with vault_audit for audit logging.

Transport: stdio (standard for Claude Code)

Dependencies:
    pip install mcp
"""

import sys
from pathlib import Path

# Allow importing vault_audit from Watchers/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Watchers"))

from mcp.server.fastmcp import FastMCP
from vault_audit import audit_log, safe_write, ErrorTracker

# Configuration
VAULT_ROOT = Path.home() / "AI_Employee_Vault"
MAX_READ_CHARS = 50_000
MAX_SEARCH_RESULTS = 20

mcp = FastMCP("vault-fs")
error_tracker = ErrorTracker("vault_fs_server")


def _validate_path(path_str: str) -> Path:
    """Resolve and validate that a path stays within the vault.

    Raises ValueError if the resolved path is outside VAULT_ROOT.
    """
    candidate = Path(path_str)
    if not candidate.is_absolute():
        candidate = VAULT_ROOT / candidate
    resolved = candidate.resolve()
    if not str(resolved).startswith(str(VAULT_ROOT.resolve())):
        audit_log(
            "path_violation",
            "vault_fs_server",
            {"requested": path_str, "resolved": str(resolved)},
            status="error",
            error="Path resolves outside vault",
        )
        raise ValueError(f"Path '{path_str}' resolves outside vault. Access denied.")
    return resolved


@mcp.tool()
def read_file(path: str) -> str:
    """Read a file from the vault.

    Args:
        path: File path (absolute or relative to vault root).

    Returns:
        File contents (truncated at 50K chars) or error message.
    """
    try:
        resolved = _validate_path(path)
        if not resolved.is_file():
            return f"Error: '{path}' is not a file or does not exist."
        content = resolved.read_text(encoding="utf-8")
        audit_log("file_read", "vault_fs_server", {"path": str(resolved)})
        if len(content) > MAX_READ_CHARS:
            return content[:MAX_READ_CHARS] + f"\n\n--- TRUNCATED at {MAX_READ_CHARS} chars ---"
        return content
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error reading file: {e}"


@mcp.tool()
def write_file(path: str, content: str, dry_run: bool = False) -> str:
    """Write content to a file in the vault (atomic write).

    Args:
        path: File path (absolute or relative to vault root).
        content: Content to write.
        dry_run: If True, returns a preview without writing.

    Returns:
        Success message, preview, or error description.
    """
    try:
        resolved = _validate_path(path)
    except ValueError as e:
        return f"Error: {e}"

    if dry_run:
        return (
            f"--- DRY RUN PREVIEW ---\n"
            f"Would write to: {resolved}\n"
            f"Content length: {len(content)} chars\n"
            f"First 200 chars:\n{content[:200]}\n"
            f"--- END PREVIEW (not written) ---"
        )

    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        safe_write(resolved, content)
        audit_log("file_write", "vault_fs_server", {
            "path": str(resolved),
            "size": len(content),
        })
        return f"File written successfully: {resolved} ({len(content)} chars)"
    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error writing file: {e}"


@mcp.tool()
def move_file(source: str, destination: str, dry_run: bool = False) -> str:
    """Move a file within the vault.

    Args:
        source: Source file path (absolute or relative to vault root).
        destination: Destination file path (absolute or relative to vault root).
        dry_run: If True, returns a preview without moving.

    Returns:
        Success message, preview, or error description.
    """
    try:
        src = _validate_path(source)
        dst = _validate_path(destination)
    except ValueError as e:
        return f"Error: {e}"

    if not src.is_file():
        return f"Error: Source '{source}' is not a file or does not exist."

    if dry_run:
        return (
            f"--- DRY RUN PREVIEW ---\n"
            f"Would move: {src}\n"
            f"        to: {dst}\n"
            f"--- END PREVIEW (not moved) ---"
        )

    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        audit_log("file_move", "vault_fs_server", {
            "source": str(src),
            "destination": str(dst),
        })
        return f"File moved: {src} -> {dst}"
    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error moving file: {e}"


@mcp.tool()
def list_folder(path: str = "") -> str:
    """List contents of a vault folder.

    Args:
        path: Folder path (absolute or relative to vault root). Defaults to vault root.

    Returns:
        Formatted listing of folder contents or error message.
    """
    try:
        if not path:
            resolved = VAULT_ROOT
        else:
            resolved = _validate_path(path)
        if not resolved.is_dir():
            return f"Error: '{path}' is not a directory or does not exist."
        entries = sorted(resolved.iterdir())
        lines = []
        for entry in entries:
            if entry.name.startswith("."):
                continue
            prefix = "📁 " if entry.is_dir() else "📄 "
            lines.append(f"{prefix}{entry.name}")
        audit_log("folder_list", "vault_fs_server", {
            "path": str(resolved),
            "count": len(lines),
        })
        if not lines:
            return f"Folder is empty: {resolved}"
        return f"Contents of {resolved}:\n" + "\n".join(lines)
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error listing folder: {e}"


@mcp.tool()
def search_vault(query: str, file_pattern: str = "*.md") -> str:
    """Search vault files for a text query (case-insensitive).

    Args:
        query: Text to search for.
        file_pattern: Glob pattern for files to search. Defaults to "*.md".

    Returns:
        Matching files and lines, or error message.
    """
    if not query or not query.strip():
        return "Error: Search query cannot be empty."

    try:
        query_lower = query.lower()
        matches = []
        for filepath in VAULT_ROOT.rglob(file_pattern):
            if not filepath.is_file():
                continue
            # Skip hidden dirs/files
            if any(part.startswith(".") for part in filepath.relative_to(VAULT_ROOT).parts):
                continue
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for i, line in enumerate(content.splitlines(), 1):
                if query_lower in line.lower():
                    rel = filepath.relative_to(VAULT_ROOT)
                    matches.append(f"{rel}:{i}: {line.strip()}")
                    if len(matches) >= MAX_SEARCH_RESULTS:
                        break
            if len(matches) >= MAX_SEARCH_RESULTS:
                break

        audit_log("vault_search", "vault_fs_server", {
            "query": query,
            "pattern": file_pattern,
            "matches": len(matches),
        })

        if not matches:
            return f"No matches found for '{query}' in {file_pattern} files."
        result = f"Search results for '{query}' ({len(matches)} matches):\n"
        result += "\n".join(matches)
        if len(matches) >= MAX_SEARCH_RESULTS:
            result += f"\n\n--- Limited to {MAX_SEARCH_RESULTS} results ---"
        return result
    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error searching vault: {e}"


if __name__ == "__main__":
    mcp.run()
