# Social Media Check

Post to Facebook, Instagram, and Twitter/X — create approval requests, check posting status, and view social media summaries.

## Triggers
- "post to facebook"
- "post to instagram"
- "post to twitter"
- "social media post"
- "social media summary"
- "social check"
- "social media status"

## Instructions

When the user asks about social media posting:

1. **Post to Facebook** - Use the `post_facebook` MCP tool with `dry_run=True` first to preview. Only set `dry_run=False` after user confirmation. Creates an approval request in `Pending_Approval/`.

2. **Post to Instagram** - Use `post_instagram` with `dry_run=True` first. Include `image_path` if available (V1 is text-only, will warn if no image). Only set `dry_run=False` after user confirmation.

3. **Post to Twitter/X** - Use `post_twitter` with `dry_run=True` first. Validates 280-character limit. Only set `dry_run=False` after user confirmation.

4. **Social media summary** - Use `get_social_summary` to view posting history from Done/ grouped by platform.

5. **Check status** - Run `python Scripts/social_poster.py --platform all --dry-run --once` to see pending posts across all platforms.

6. **Generate summary report** - Run `python Scripts/social_poster.py --summary` to create `Logs/social_summary.md`.

## Notes
- MCP tools create approval requests — they do NOT post directly
- Human must move file from `Pending_Approval/` to `Approved/` to trigger posting
- Each platform requires a one-time interactive login: `python Scripts/social_poster.py --platform <name>`
- Sessions stored in `.social_sessions/{platform}/state.json`
- Twitter has a strict 280-character limit
- Instagram V1 is text-only — image upload planned for future
- All operations are audit-logged to `Logs/audit.jsonl`
- See `Skills/social_media_poster.md` for full documentation
