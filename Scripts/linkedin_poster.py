#!/usr/bin/env python3
"""
LinkedIn Auto-Poster for AI Employee Vault

Watches Approved/ for files with action_type: linkedin_post,
posts text content to LinkedIn via Playwright, and archives to Done/.

First run requires headed browser for manual LinkedIn login.
Subsequent runs reuse saved session in headless mode.

Usage:
    python linkedin_poster.py              # Normal polling mode
    python linkedin_poster.py --once       # Single check and exit
    python linkedin_poster.py --dry-run    # Log what would be posted
    python linkedin_poster.py --dry-run --once  # Preview without browser

Dependencies:
    pip install playwright
    python -m playwright install chromium
"""

import argparse
import logging
import random
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

# Configuration
VAULT_ROOT = Path.home() / "AI_Employee_Vault"
APPROVED_DIR = VAULT_ROOT / "Approved"
DONE_DIR = VAULT_ROOT / "Done"
LOG_DIR = VAULT_ROOT / "Logs"
SESSION_DIR = VAULT_ROOT / ".linkedin_session"
SESSION_FILE = SESSION_DIR / "state.json"
CHECK_INTERVAL = 60  # seconds
MAX_POST_LENGTH = 3000

# Setup logging
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "linkedin.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def parse_frontmatter(filepath: Path) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    try:
        content = filepath.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        logger.warning(f"Could not decode {filepath.name} as UTF-8")
        return {}
    except Exception as e:
        logger.warning(f"Could not read {filepath.name}: {e}")
        return {}

    if not content.startswith('---'):
        return {}

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}

    raw_frontmatter = parts[1]

    if yaml is not None:
        try:
            data = yaml.safe_load(raw_frontmatter)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning(f"YAML parse error in {filepath.name}: {e}")
            return {}
    else:
        result = {}
        for line in raw_frontmatter.strip().splitlines():
            if ':' in line:
                key, _, value = line.partition(':')
                result[key.strip()] = value.strip()
        return result


def extract_post_content(filepath: Path) -> str:
    """Extract the post body text from a markdown file.

    Looks for a '## Post Content' section and returns its text,
    or falls back to all body text after frontmatter.
    """
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"Could not read {filepath.name}: {e}")
        return ""

    # Strip frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            body = parts[2]
        else:
            body = content
    else:
        body = content

    # Try to find ## Post Content section
    lines = body.strip().splitlines()
    in_section = False
    post_lines = []
    for line in lines:
        if line.strip().lower().startswith('## post content'):
            in_section = True
            continue
        if in_section:
            # Stop at next heading or approval section
            if line.strip().startswith('## '):
                break
            post_lines.append(line)

    if post_lines:
        return '\n'.join(post_lines).strip()

    # Fallback: return all body text (excluding headings and checkboxes)
    fallback_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('- ['):
            continue
        if stripped:
            fallback_lines.append(line)
    return '\n'.join(fallback_lines).strip()


def get_linkedin_posts() -> list[Path]:
    """Scan Approved/ for files with action_type: linkedin_post."""
    APPROVED_DIR.mkdir(exist_ok=True)
    posts = []
    for filepath in sorted(APPROVED_DIR.glob("*.md")):
        if filepath.name.startswith('.'):
            continue
        fm = parse_frontmatter(filepath)
        if fm.get("action_type") == "linkedin_post":
            posts.append(filepath)
    return posts


def archive_to_done(filepath: Path) -> bool:
    """Move a processed file to Done/ with updated status and timestamp."""
    DONE_DIR.mkdir(exist_ok=True)
    done_path = DONE_DIR / filepath.name

    try:
        content = filepath.read_text(encoding='utf-8')
        # Update status
        content = content.replace(
            'status: pending_approval', 'status: done'
        ).replace(
            'status: approved', 'status: done'
        )
        # Add posted timestamp after status line
        posted_ts = datetime.now().isoformat()
        content = content.replace(
            'status: done',
            f'status: done\nposted: {posted_ts}'
        )
        done_path.write_text(content, encoding='utf-8')
        filepath.unlink()
        logger.info(f"Archived to Done: {filepath.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to archive {filepath.name}: {e}")
        return False


def ensure_login(context):
    """Check if LinkedIn session is valid. Returns True if logged in."""
    page = context.new_page()
    try:
        page.goto("https://www.linkedin.com/feed", wait_until="domcontentloaded",
                   timeout=30000)
        # Check for profile menu (indicates logged-in state)
        try:
            page.wait_for_selector(
                'img.global-nav__me-photo, .feed-identity-module',
                timeout=10000
            )
            logger.info("LinkedIn session valid — logged in")
            return True
        except Exception:
            logger.warning("LinkedIn session expired or invalid")
            return False
    except Exception as e:
        logger.error(f"Failed to check LinkedIn login: {e}")
        return False
    finally:
        page.close()


def interactive_login(playwright):
    """Launch headed browser for manual LinkedIn login and save session."""
    SESSION_DIR.mkdir(exist_ok=True)
    logger.info("Launching headed browser for LinkedIn login...")
    logger.info("Please log in to LinkedIn manually. The session will be saved.")

    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")

    print("\n" + "=" * 50)
    print("LinkedIn Login Required")
    print("=" * 50)
    print("1. Log in to LinkedIn in the browser window")
    print("2. Complete any 2FA if prompted")
    print("3. Wait until you see your feed")
    print("4. Press Enter here when done")
    print("=" * 50)
    input("\nPress Enter after logging in... ")

    # Save session state
    context.storage_state(path=str(SESSION_FILE))
    logger.info(f"Session saved to {SESSION_FILE}")

    page.close()
    context.close()
    browser.close()


def post_to_linkedin(page, text: str) -> bool:
    """Post text content to LinkedIn feed.

    Navigates to feed, opens compose dialog, enters text, and clicks Post.
    Includes human-like delays to reduce automation detection.
    """
    try:
        # Navigate to feed
        page.goto("https://www.linkedin.com/feed", wait_until="domcontentloaded",
                   timeout=30000)
        time.sleep(random.uniform(2, 4))

        # Click "Start a post" button
        start_post_btn = page.locator(
            'button:has-text("Start a post"), '
            '.share-box-feed-entry__trigger'
        )
        start_post_btn.first.click()
        time.sleep(random.uniform(1, 2))

        # Wait for the post editor to appear
        editor = page.locator(
            '.ql-editor[data-placeholder], '
            'div[role="textbox"][contenteditable="true"]'
        )
        editor.first.wait_for(state="visible", timeout=10000)
        time.sleep(random.uniform(0.5, 1))

        # Type the post content with human-like delays
        editor.first.click()
        editor.first.fill(text)
        time.sleep(random.uniform(1, 2))

        # Click Post button
        post_btn = page.locator(
            'button:has-text("Post"):not(:has-text("Repost")), '
            'button.share-actions__primary-action'
        )
        post_btn.first.click()
        time.sleep(random.uniform(3, 5))

        logger.info("Post submitted successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to post to LinkedIn: {e}")
        return False


def process_posts(dry_run: bool = False) -> int:
    """Process all pending LinkedIn posts. Returns count of posts processed."""
    posts = get_linkedin_posts()
    if not posts:
        logger.debug("No LinkedIn posts found in Approved/")
        return 0

    logger.info(f"Found {len(posts)} LinkedIn post(s) to process")

    if dry_run:
        for filepath in posts:
            text = extract_post_content(filepath)
            logger.info(
                f"[DRY RUN] Would post from {filepath.name}: "
                f"{text[:100]}{'...' if len(text) > 100 else ''}"
            )
            if len(text) > MAX_POST_LENGTH:
                logger.warning(
                    f"[DRY RUN] Post exceeds {MAX_POST_LENGTH} chars "
                    f"({len(text)} chars) — would be skipped"
                )
        return len(posts)

    # Import playwright only when needed (not for dry-run)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error(
            "Playwright not installed. Run: "
            "pip install playwright && python -m playwright install chromium"
        )
        return 0

    if not SESSION_FILE.exists():
        logger.error(
            f"No LinkedIn session found at {SESSION_FILE}. "
            "Run script without --once for interactive login."
        )
        return 0

    processed = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(SESSION_FILE))

        if not ensure_login(context):
            logger.error(
                "LinkedIn session expired. "
                "Run script interactively to re-login."
            )
            context.close()
            browser.close()
            return 0

        page = context.new_page()

        for filepath in posts:
            text = extract_post_content(filepath)

            if not text:
                logger.warning(f"Empty post content in {filepath.name} — skipping")
                continue

            if len(text) > MAX_POST_LENGTH:
                logger.warning(
                    f"Post {filepath.name} exceeds {MAX_POST_LENGTH} chars "
                    f"({len(text)} chars) — skipping"
                )
                continue

            logger.info(f"Posting from {filepath.name}...")
            if post_to_linkedin(page, text):
                archive_to_done(filepath)
                processed += 1
                # Delay between posts
                if filepath != posts[-1]:
                    delay = random.uniform(30, 60)
                    logger.info(f"Waiting {delay:.0f}s before next post...")
                    time.sleep(delay)
            else:
                logger.error(f"Failed to post {filepath.name} — leaving in Approved/")

        page.close()
        context.close()
        browser.close()

    return processed


def main():
    """Main entry point for the LinkedIn poster."""
    parser = argparse.ArgumentParser(
        description="LinkedIn Auto-Poster for AI Employee Vault"
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Log what would be posted without using browser'
    )
    parser.add_argument(
        '--once', action='store_true',
        help='Single check and exit (for cron)'
    )
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("LinkedIn Poster Starting")
    logger.info(f"Watching: {APPROVED_DIR}")
    logger.info(f"Archive to: {DONE_DIR}")
    logger.info(f"Session dir: {SESSION_DIR}")
    if args.dry_run:
        logger.info("Mode: DRY RUN (no browser)")
    if args.once:
        logger.info("Mode: Single check")
    logger.info("=" * 50)

    # Ensure directories exist
    APPROVED_DIR.mkdir(exist_ok=True)
    DONE_DIR.mkdir(exist_ok=True)

    if args.dry_run:
        process_posts(dry_run=True)
        return

    # Check for session — if missing, run interactive login
    if not SESSION_FILE.exists() and not args.once:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error(
                "Playwright not installed. Run: "
                "pip install playwright && python -m playwright install chromium"
            )
            sys.exit(1)

        with sync_playwright() as p:
            interactive_login(p)
        logger.info("Session saved. Starting polling loop...")

    if args.once:
        count = process_posts(dry_run=False)
        logger.info(f"Processed {count} post(s). Exiting.")
        return

    # Polling loop
    logger.info(f"Polling every {CHECK_INTERVAL}s. Press Ctrl+C to stop.")
    try:
        while True:
            process_posts(dry_run=False)
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Stopping LinkedIn poster...")
    logger.info("LinkedIn poster stopped.")


if __name__ == "__main__":
    main()
