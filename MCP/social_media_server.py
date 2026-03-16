#!/usr/bin/env python3
"""
MCP Social Media Server for AI Employee Vault

Exposes social media posting tools via the Model Context Protocol.
Tools create approval requests in Pending_Approval/ — actual posting
happens when social_poster.py finds approved files. This maintains HITL.

Transport: stdio (standard for Claude Code)

Dependencies:
    pip install mcp
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Allow importing vault_audit from Watchers/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Watchers"))

from mcp.server.fastmcp import FastMCP
from vault_audit import audit_log, safe_write, ErrorTracker

# Configuration
VAULT_ROOT = Path.home() / "AI_Employee_Vault"
PENDING_DIR = VAULT_ROOT / "Pending_Approval"
DONE_DIR = VAULT_ROOT / "Done"

DRY_RUN_MODE = False

mcp = FastMCP("social-media")
error_tracker = ErrorTracker("social_media_server")

# Platform constraints
PLATFORM_CONFIG = {
    "facebook": {"max_length": 63206, "action_type": "facebook_post"},
    "instagram": {"max_length": 2200, "action_type": "instagram_post"},
    "twitter": {"max_length": 280, "action_type": "twitter_post"},
}


def _create_approval_request(platform: str, content: str, extra_fields: str = "") -> str:
    """Create an approval request file in Pending_Approval/."""
    now = datetime.now()
    config = PLATFORM_CONFIG[platform]
    slug = platform[:10]
    filename = f"{now.strftime('%Y%m%d_%H%M%S')}_social_{slug}_post.md"
    filepath = PENDING_DIR / filename

    approval_content = f"""---
type: approval_request
action_type: {config['action_type']}
platform: {platform}
requested: {now.isoformat(timespec='seconds')}
status: pending_approval
priority: normal
domain: business
requester: AI_Employee
---

# Social Media Post — {platform.title()}

## Post Content

{content}

## Details
- **Platform**: {platform.title()}
- **Character Count**: {len(content)}/{config['max_length']}
{extra_fields}
## Risk Assessment
- **Impact**: Low (social media post)
- **Reversibility**: Medium (can delete post after publishing)

## Approval Actions
- [ ] **Approve**: Move this file to `/Approved/` folder
- [ ] **Reject**: Delete this file or add rejection reason below
- [ ] **Defer**: Add comment and leave in `/Pending_Approval/`

## Rejection Reason (if applicable)
_None_
"""
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    safe_write(filepath, approval_content)
    return str(filepath)


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def post_facebook(content: str, dry_run: bool = True) -> str:
    """Create a Facebook post approval request.

    The post will not be published immediately — it creates an approval request
    in Pending_Approval/. Move to Approved/ to trigger posting.

    Args:
        content: The text content to post to Facebook (max 63,206 chars).
        dry_run: If True (default), returns a preview without creating the request.

    Returns:
        Preview or confirmation of approval request creation.
    """
    error_tracker.check()
    try:
        audit_log("social_post_facebook", "social_media_server", {
            "length": len(content),
            "dry_run": dry_run,
        })

        config = PLATFORM_CONFIG["facebook"]
        if len(content) > config["max_length"]:
            return f"Error: Content exceeds Facebook's {config['max_length']} char limit ({len(content)} chars)."

        if dry_run or DRY_RUN_MODE:
            return (
                f"--- DRY RUN PREVIEW ---\n"
                f"Platform: Facebook\n"
                f"Content ({len(content)} chars):\n{content[:500]}{'...' if len(content) > 500 else ''}\n"
                f"--- END PREVIEW (not created) ---"
            )

        filepath = _create_approval_request("facebook", content)
        return f"Facebook post approval request created at: {filepath}\nMove to Approved/ to trigger posting."

    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error creating Facebook post request: {e}"


@mcp.tool()
def post_instagram(content: str, image_path: str = "", dry_run: bool = True) -> str:
    """Create an Instagram post approval request.

    V1 is text-only. Image upload is a future enhancement.
    Instagram feed posts typically require images — this will warn accordingly.

    Args:
        content: The caption/text content (max 2,200 chars).
        image_path: Optional path to image file (not yet supported in V1).
        dry_run: If True (default), returns a preview without creating the request.

    Returns:
        Preview or confirmation of approval request creation.
    """
    error_tracker.check()
    try:
        audit_log("social_post_instagram", "social_media_server", {
            "length": len(content),
            "has_image": bool(image_path),
            "dry_run": dry_run,
        })

        config = PLATFORM_CONFIG["instagram"]
        if len(content) > config["max_length"]:
            return f"Error: Content exceeds Instagram's {config['max_length']} char limit ({len(content)} chars)."

        warning = ""
        if not image_path:
            warning = "- **Warning**: No image provided. Instagram feed posts require images. V1 is text-only.\n"

        if dry_run or DRY_RUN_MODE:
            return (
                f"--- DRY RUN PREVIEW ---\n"
                f"Platform: Instagram\n"
                f"Content ({len(content)} chars):\n{content[:500]}{'...' if len(content) > 500 else ''}\n"
                f"{'WARNING: No image — Instagram feed posts typically require images.\n' if not image_path else ''}"
                f"--- END PREVIEW (not created) ---"
            )

        extra = warning
        if image_path:
            extra += f"- **Image**: {image_path}\n"

        filepath = _create_approval_request("instagram", content, extra)
        result = f"Instagram post approval request created at: {filepath}\nMove to Approved/ to trigger posting."
        if not image_path:
            result += "\nNote: No image provided. Instagram V1 is text-only; image support planned."
        return result

    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error creating Instagram post request: {e}"


@mcp.tool()
def post_twitter(content: str, dry_run: bool = True) -> str:
    """Create a Twitter/X post (tweet) approval request.

    Args:
        content: The tweet text (max 280 chars).
        dry_run: If True (default), returns a preview without creating the request.

    Returns:
        Preview or confirmation of approval request creation.
    """
    error_tracker.check()
    try:
        audit_log("social_post_twitter", "social_media_server", {
            "length": len(content),
            "dry_run": dry_run,
        })

        config = PLATFORM_CONFIG["twitter"]
        if len(content) > config["max_length"]:
            return (
                f"Error: Content exceeds Twitter's {config['max_length']} char limit "
                f"({len(content)} chars). Please shorten your tweet."
            )

        if dry_run or DRY_RUN_MODE:
            return (
                f"--- DRY RUN PREVIEW ---\n"
                f"Platform: Twitter/X\n"
                f"Content ({len(content)}/280 chars):\n{content}\n"
                f"--- END PREVIEW (not created) ---"
            )

        filepath = _create_approval_request("twitter", content)
        return f"Twitter post approval request created at: {filepath}\nMove to Approved/ to trigger posting."

    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error creating Twitter post request: {e}"


@mcp.tool()
def get_social_summary() -> str:
    """Get a summary of social media posting history from Done/.

    Returns:
        JSON summary of all social media posts grouped by platform.
    """
    error_tracker.check()
    try:
        audit_log("social_summary", "social_media_server", {})

        if DRY_RUN_MODE:
            return json.dumps({
                "facebook": [{"file": "fb_post_demo.md", "posted": "2026-03-14T10:00:00"}],
                "instagram": [],
                "twitter": [{"file": "tweet_demo.md", "posted": "2026-03-14T11:00:00"}],
                "total": 2,
            }, indent=2)

        DONE_DIR.mkdir(exist_ok=True)
        summary = {"facebook": [], "instagram": [], "twitter": []}

        try:
            import yaml as _yaml
        except ImportError:
            _yaml = None

        for filepath in sorted(DONE_DIR.glob("*.md")):
            try:
                content = filepath.read_text(encoding='utf-8')
            except Exception:
                continue

            if not content.startswith('---'):
                continue

            parts = content.split('---', 2)
            if len(parts) < 3:
                continue

            # Parse frontmatter
            fm = {}
            if _yaml:
                try:
                    fm = _yaml.safe_load(parts[1]) or {}
                except Exception:
                    pass
            else:
                for line in parts[1].strip().splitlines():
                    if ':' in line:
                        k, _, v = line.partition(':')
                        fm[k.strip()] = v.strip()

            action = fm.get("action_type", "")
            for platform in summary:
                if action == f"{platform}_post":
                    summary[platform].append({
                        "file": filepath.name,
                        "posted": str(fm.get("posted", fm.get("created", "unknown"))),
                    })

        summary["total"] = sum(len(v) for v in summary.values())
        return json.dumps(summary, indent=2)

    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error generating social summary: {e}"


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Social Media MCP Server")
    parser.add_argument("--dry-run", action="store_true", help="Return mock data")
    args = parser.parse_args()

    if args.dry_run:
        DRY_RUN_MODE = True
        print("Starting in DRY-RUN mode (mock data)", file=sys.stderr)

    mcp.run()
