#!/usr/bin/env python3
"""
Social Media Auto-Poster for AI Employee Vault

Watches Approved/ for files with action_type: facebook_post | instagram_post | twitter_post,
posts content via Playwright, and archives to Done/.

Extends the linkedin_poster.py pattern with a PlatformAdapter abstraction
for Facebook, Instagram, and Twitter/X.

First run per platform requires headed browser for manual login.
Subsequent runs reuse saved session in headless mode.

Usage:
    python social_poster.py --platform facebook --once
    python social_poster.py --platform all --dry-run --once
    python social_poster.py --platform twitter --once
    python social_poster.py --summary

Dependencies:
    pip install playwright
    python -m playwright install chromium
"""

import abc
import argparse
import json
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

# Allow importing vault_audit from Watchers/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Watchers"))

from vault_audit import audit_log, retry, ErrorTracker, safe_write

# Configuration
VAULT_ROOT = Path.home() / "AI_Employee_Vault"
APPROVED_DIR = VAULT_ROOT / "Approved"
DONE_DIR = VAULT_ROOT / "Done"
LOG_DIR = VAULT_ROOT / "Logs"
SESSION_BASE = VAULT_ROOT / ".social_sessions"
SCREENSHOT_DIR = LOG_DIR / "screenshots" / "social"
CHECK_INTERVAL = 60  # seconds

# Setup logging
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "social_poster.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Platform-specific error trackers
_error_trackers = {}


def get_error_tracker(platform: str) -> ErrorTracker:
    if platform not in _error_trackers:
        _error_trackers[platform] = ErrorTracker(f"social_{platform}")
    return _error_trackers[platform]


# ---------------------------------------------------------------------------
# Shared Utilities (reused from linkedin_poster pattern)
# ---------------------------------------------------------------------------

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
    """Extract the post body text from a markdown file."""
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"Could not read {filepath.name}: {e}")
        return ""

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            body = parts[2]
        else:
            body = content
    else:
        body = content

    lines = body.strip().splitlines()
    in_section = False
    post_lines = []
    for line in lines:
        if line.strip().lower().startswith('## post content'):
            in_section = True
            continue
        if in_section:
            if line.strip().startswith('## '):
                break
            post_lines.append(line)

    if post_lines:
        return '\n'.join(post_lines).strip()

    fallback_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('- ['):
            continue
        if stripped:
            fallback_lines.append(line)
    return '\n'.join(fallback_lines).strip()


def archive_to_done(filepath: Path) -> bool:
    """Move a processed file to Done/ with updated status and timestamp."""
    DONE_DIR.mkdir(exist_ok=True)
    done_path = DONE_DIR / filepath.name

    try:
        content = filepath.read_text(encoding='utf-8')
        content = content.replace(
            'status: pending_approval', 'status: done'
        ).replace(
            'status: approved', 'status: done'
        )
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


# ---------------------------------------------------------------------------
# Platform Adapter (Abstract Base)
# ---------------------------------------------------------------------------

class PlatformAdapter(abc.ABC):
    """Abstract base class for social media platform adapters."""

    name: str = ""
    login_url: str = ""
    max_length: int = 0

    @property
    def session_dir(self) -> Path:
        return SESSION_BASE / self.name

    @property
    def session_file(self) -> Path:
        return self.session_dir / "state.json"

    @property
    def action_type(self) -> str:
        return f"{self.name}_post"

    def validate_content(self, text: str) -> tuple:
        """Validate content against platform constraints. Returns (ok, reason)."""
        if not text:
            return False, "Empty post content"
        if self.max_length > 0 and len(text) > self.max_length:
            return False, f"Exceeds {self.max_length} chars ({len(text)} chars)"
        return True, ""

    def interactive_login(self, playwright):
        """Launch headed browser for manual login and save session."""
        self.session_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Launching headed browser for {self.name} login...")

        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(self.login_url, wait_until="domcontentloaded")

        print(f"\n{'=' * 50}")
        print(f"{self.name.title()} Login Required")
        print("=" * 50)
        print(f"1. Log in to {self.name.title()} in the browser window")
        print("2. Complete any 2FA if prompted")
        print("3. Wait until you see your feed/home")
        print("4. Press Enter here when done")
        print("=" * 50)
        input("\nPress Enter after logging in... ")

        context.storage_state(path=str(self.session_file))
        logger.info(f"{self.name.title()} session saved to {self.session_file}")

        page.close()
        context.close()
        browser.close()

    @abc.abstractmethod
    def ensure_login(self, context) -> bool:
        """Check if session is valid. Returns True if logged in."""

    @abc.abstractmethod
    def compose_and_post(self, page, content: str, dry_run: bool = False) -> bool:
        """Navigate, compose, and post content. Returns True on success."""

    def take_screenshot(self, page, suffix: str = ""):
        """Save a screenshot for debugging."""
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.name}_{ts}{('_' + suffix) if suffix else ''}.png"
        path = SCREENSHOT_DIR / filename
        try:
            page.screenshot(path=str(path))
            logger.info(f"Screenshot saved: {path}")
        except Exception as e:
            logger.warning(f"Screenshot failed: {e}")


# ---------------------------------------------------------------------------
# Facebook Adapter
# ---------------------------------------------------------------------------

class FacebookAdapter(PlatformAdapter):
    name = "facebook"
    login_url = "https://www.facebook.com/login"
    max_length = 63206

    # Selectors (class constants for easy maintenance)
    FEED_URL = "https://www.facebook.com/"
    POST_BOX_SELECTOR = (
        'div[role="button"]:has-text("What\'s on your mind"), '
        'div[data-pagelet="FeedComposer"] div[role="button"]'
    )
    EDITOR_SELECTOR = (
        'div[role="textbox"][contenteditable="true"]'
    )
    POST_BTN_SELECTOR = (
        'div[aria-label="Post"][role="button"], '
        'div[role="button"]:has-text("Post"):not(:has-text("Repost"))'
    )

    def ensure_login(self, context) -> bool:
        page = context.new_page()
        try:
            page.goto(self.FEED_URL, wait_until="domcontentloaded", timeout=30000)
            try:
                page.wait_for_selector(
                    'div[role="navigation"], div[aria-label="Facebook"]',
                    timeout=10000
                )
                logger.info("Facebook session valid — logged in")
                return True
            except Exception:
                logger.warning("Facebook session expired or invalid")
                return False
        except Exception as e:
            logger.error(f"Failed to check Facebook login: {e}")
            return False
        finally:
            page.close()

    def compose_and_post(self, page, content: str, dry_run: bool = False) -> bool:
        try:
            page.goto(self.FEED_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(random.uniform(2, 4))

            if dry_run:
                logger.info(f"[DRY RUN] Would post to Facebook: {content[:100]}...")
                return True

            post_box = page.locator(self.POST_BOX_SELECTOR)
            post_box.first.click()
            time.sleep(random.uniform(1, 2))

            editor = page.locator(self.EDITOR_SELECTOR)
            editor.first.wait_for(state="visible", timeout=10000)
            time.sleep(random.uniform(0.5, 1))

            editor.first.click()
            editor.first.fill(content)
            time.sleep(random.uniform(1, 2))

            self.take_screenshot(page, "pre_post")

            post_btn = page.locator(self.POST_BTN_SELECTOR)
            post_btn.first.click()
            time.sleep(random.uniform(3, 5))

            logger.info("Facebook post submitted successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to post to Facebook: {e}")
            self.take_screenshot(page, "error")
            return False


# ---------------------------------------------------------------------------
# Instagram Adapter
# ---------------------------------------------------------------------------

class InstagramAdapter(PlatformAdapter):
    name = "instagram"
    login_url = "https://www.instagram.com/accounts/login/"
    max_length = 2200  # caption limit

    FEED_URL = "https://www.instagram.com/"
    # Instagram text-only: V1 warns that images are preferred
    NEW_POST_SELECTOR = 'svg[aria-label="New post"], a[href="/create/select/"]'

    def ensure_login(self, context) -> bool:
        page = context.new_page()
        try:
            page.goto(self.FEED_URL, wait_until="domcontentloaded", timeout=30000)
            try:
                page.wait_for_selector(
                    'svg[aria-label="Home"], a[href="/direct/inbox/"]',
                    timeout=10000
                )
                logger.info("Instagram session valid — logged in")
                return True
            except Exception:
                logger.warning("Instagram session expired or invalid")
                return False
        except Exception as e:
            logger.error(f"Failed to check Instagram login: {e}")
            return False
        finally:
            page.close()

    def validate_content(self, text: str) -> tuple:
        ok, reason = super().validate_content(text)
        if ok:
            logger.warning(
                "Instagram V1: Text-only posting. Feed posts typically require images. "
                "This will attempt a text post but may fail without an image."
            )
        return ok, reason

    def compose_and_post(self, page, content: str, dry_run: bool = False) -> bool:
        try:
            page.goto(self.FEED_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(random.uniform(2, 4))

            if dry_run:
                logger.info(f"[DRY RUN] Would post to Instagram: {content[:100]}...")
                logger.warning("[DRY RUN] Instagram V1 is text-only — image upload not supported yet")
                return True

            # Instagram requires image for feed posts — V1 text attempt
            logger.warning(
                "Instagram text-only post attempted. This may not work as "
                "Instagram requires an image for feed posts. Image support "
                "is planned for a future version."
            )

            new_post = page.locator(self.NEW_POST_SELECTOR)
            new_post.first.click()
            time.sleep(random.uniform(1, 2))

            self.take_screenshot(page, "compose")
            logger.info("Instagram compose dialog opened — text-only V1 limited")
            return False  # V1: text-only not reliably supported

        except Exception as e:
            logger.error(f"Failed to post to Instagram: {e}")
            self.take_screenshot(page, "error")
            return False


# ---------------------------------------------------------------------------
# Twitter/X Adapter
# ---------------------------------------------------------------------------

class TwitterAdapter(PlatformAdapter):
    name = "twitter"
    login_url = "https://x.com/i/flow/login"
    max_length = 280

    FEED_URL = "https://x.com/home"
    COMPOSE_SELECTOR = (
        'div[data-testid="tweetTextarea_0"][role="textbox"], '
        'div[role="textbox"][data-testid="tweetTextarea_0"]'
    )
    POST_BTN_SELECTOR = (
        'button[data-testid="tweetButtonInline"], '
        'button[data-testid="tweetButton"]'
    )

    def ensure_login(self, context) -> bool:
        page = context.new_page()
        try:
            page.goto(self.FEED_URL, wait_until="domcontentloaded", timeout=30000)
            try:
                page.wait_for_selector(
                    'a[data-testid="AppTabBar_Home_Link"], '
                    'div[data-testid="primaryColumn"]',
                    timeout=10000
                )
                logger.info("Twitter/X session valid — logged in")
                return True
            except Exception:
                logger.warning("Twitter/X session expired or invalid")
                return False
        except Exception as e:
            logger.error(f"Failed to check Twitter/X login: {e}")
            return False
        finally:
            page.close()

    def compose_and_post(self, page, content: str, dry_run: bool = False) -> bool:
        try:
            page.goto(self.FEED_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(random.uniform(2, 4))

            if dry_run:
                logger.info(f"[DRY RUN] Would post to Twitter/X: {content[:100]}...")
                return True

            editor = page.locator(self.COMPOSE_SELECTOR)
            editor.first.wait_for(state="visible", timeout=10000)
            time.sleep(random.uniform(0.5, 1))

            editor.first.click()
            editor.first.fill(content)
            time.sleep(random.uniform(1, 2))

            self.take_screenshot(page, "pre_post")

            post_btn = page.locator(self.POST_BTN_SELECTOR)
            post_btn.first.click()
            time.sleep(random.uniform(3, 5))

            logger.info("Twitter/X post submitted successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to post to Twitter/X: {e}")
            self.take_screenshot(page, "error")
            return False


# ---------------------------------------------------------------------------
# Adapter Registry
# ---------------------------------------------------------------------------

ADAPTERS = {
    "facebook": FacebookAdapter,
    "instagram": InstagramAdapter,
    "twitter": TwitterAdapter,
}


def get_adapter(platform: str) -> PlatformAdapter:
    cls = ADAPTERS.get(platform)
    if not cls:
        raise ValueError(f"Unknown platform: {platform}. Choose from: {list(ADAPTERS.keys())}")
    return cls()


# ---------------------------------------------------------------------------
# Post Processing
# ---------------------------------------------------------------------------

def get_social_posts(platform: str = None) -> list:
    """Scan Approved/ for social media post files."""
    APPROVED_DIR.mkdir(exist_ok=True)
    action_types = []
    if platform:
        action_types = [f"{platform}_post"]
    else:
        action_types = [f"{p}_post" for p in ADAPTERS]

    posts = []
    for filepath in sorted(APPROVED_DIR.glob("*.md")):
        if filepath.name.startswith('.'):
            continue
        fm = parse_frontmatter(filepath)
        if fm.get("action_type") in action_types:
            posts.append(filepath)
    return posts


def process_posts_for_platform(adapter: PlatformAdapter, dry_run: bool = False) -> int:
    """Process all pending posts for a single platform."""
    tracker = get_error_tracker(adapter.name)
    tracker.check()

    posts = get_social_posts(adapter.name)
    if not posts:
        logger.debug(f"No {adapter.name} posts found in Approved/")
        return 0

    logger.info(f"Found {len(posts)} {adapter.name} post(s) to process")

    audit_log("social_post_started", "social_poster", {
        "platform": adapter.name,
        "count": len(posts),
        "dry_run": dry_run,
    })

    if dry_run:
        for filepath in posts:
            text = extract_post_content(filepath)
            ok, reason = adapter.validate_content(text)
            if not ok:
                logger.warning(
                    f"[DRY RUN] {adapter.name} post {filepath.name}: validation failed — {reason}"
                )
            else:
                logger.info(
                    f"[DRY RUN] Would post to {adapter.name} from {filepath.name}: "
                    f"{text[:100]}{'...' if len(text) > 100 else ''}"
                )
        return len(posts)

    # Import playwright only when needed
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error(
            "Playwright not installed. Run: "
            "pip install playwright && python -m playwright install chromium"
        )
        return 0

    if not adapter.session_file.exists():
        logger.error(
            f"No {adapter.name} session found at {adapter.session_file}. "
            "Run script without --once for interactive login."
        )
        audit_log("social_session_expired", "social_poster", {
            "platform": adapter.name,
            "reason": "no session file",
        }, status="error")
        return 0

    processed = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(adapter.session_file))

        if not adapter.ensure_login(context):
            logger.error(
                f"{adapter.name.title()} session expired. "
                "Run script interactively to re-login."
            )
            audit_log("social_session_expired", "social_poster", {
                "platform": adapter.name,
                "reason": "session validation failed",
            }, status="error")
            context.close()
            browser.close()
            return 0

        page = context.new_page()

        for filepath in posts:
            text = extract_post_content(filepath)

            ok, reason = adapter.validate_content(text)
            if not ok:
                logger.warning(f"{adapter.name} post {filepath.name}: {reason} — skipping")
                continue

            logger.info(f"Posting to {adapter.name} from {filepath.name}...")
            if adapter.compose_and_post(page, text, dry_run=False):
                archive_to_done(filepath)
                processed += 1
                audit_log("social_post_success", "social_poster", {
                    "platform": adapter.name,
                    "file": filepath.name,
                    "length": len(text),
                })
                # Delay between posts
                if filepath != posts[-1]:
                    delay = random.uniform(30, 60)
                    logger.info(f"Waiting {delay:.0f}s before next post...")
                    time.sleep(delay)
            else:
                logger.error(f"Failed to post {filepath.name} to {adapter.name} — leaving in Approved/")
                tracker.record_error(f"post_failed:{filepath.name}")
                audit_log("social_post_failed", "social_poster", {
                    "platform": adapter.name,
                    "file": filepath.name,
                }, status="error")

        page.close()
        context.close()
        browser.close()

    return processed


def generate_summary() -> str:
    """Generate a summary of social media posting activity from Done/."""
    DONE_DIR.mkdir(exist_ok=True)
    summary = {"facebook": [], "instagram": [], "twitter": []}

    for filepath in sorted(DONE_DIR.glob("*.md")):
        fm = parse_frontmatter(filepath)
        action = fm.get("action_type", "")
        for platform in summary:
            if action == f"{platform}_post":
                summary[platform].append({
                    "file": filepath.name,
                    "posted": str(fm.get("posted", fm.get("created", "unknown"))),
                })

    lines = ["# Social Media Summary", ""]
    lines.append(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_")
    lines.append("")

    total = sum(len(v) for v in summary.values())
    lines.append(f"**Total Posts:** {total}")
    lines.append("")

    lines.append("| Platform | Posts |")
    lines.append("|----------|-------|")
    for platform, posts in summary.items():
        lines.append(f"| {platform.title()} | {len(posts)} |")
    lines.append("")

    for platform, posts in summary.items():
        if posts:
            lines.append(f"## {platform.title()} Posts")
            lines.append("")
            for post in posts:
                lines.append(f"- {post['file']} (posted: {post['posted']})")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Main entry point for the Social Media Poster."""
    parser = argparse.ArgumentParser(
        description="Social Media Auto-Poster for AI Employee Vault"
    )
    parser.add_argument(
        '--platform', type=str, default='all',
        choices=['facebook', 'instagram', 'twitter', 'all'],
        help='Platform to post to (default: all)'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Log what would be posted without using browser'
    )
    parser.add_argument(
        '--once', action='store_true',
        help='Single check and exit (for cron)'
    )
    parser.add_argument(
        '--summary', action='store_true',
        help='Generate social media summary report'
    )
    args = parser.parse_args()

    if args.summary:
        report = generate_summary()
        summary_path = LOG_DIR / "social_summary.md"
        safe_write(summary_path, report)
        print(report)
        logger.info(f"Summary written to {summary_path}")
        return

    platforms = list(ADAPTERS.keys()) if args.platform == 'all' else [args.platform]

    logger.info("=" * 50)
    logger.info("Social Media Poster Starting")
    logger.info(f"Platforms: {', '.join(platforms)}")
    logger.info(f"Watching: {APPROVED_DIR}")
    logger.info(f"Archive to: {DONE_DIR}")
    if args.dry_run:
        logger.info("Mode: DRY RUN (no browser)")
    if args.once:
        logger.info("Mode: Single check")
    logger.info("=" * 50)

    # Ensure directories exist
    APPROVED_DIR.mkdir(exist_ok=True)
    DONE_DIR.mkdir(exist_ok=True)

    if args.dry_run or args.once:
        total = 0
        for platform_name in platforms:
            adapter = get_adapter(platform_name)
            count = process_posts_for_platform(adapter, dry_run=args.dry_run)
            total += count
        logger.info(f"Processed {total} post(s). Exiting.")
        return

    # Check for sessions — interactive login if missing
    for platform_name in platforms:
        adapter = get_adapter(platform_name)
        if not adapter.session_file.exists():
            try:
                from playwright.sync_api import sync_playwright
            except ImportError:
                logger.error(
                    "Playwright not installed. Run: "
                    "pip install playwright && python -m playwright install chromium"
                )
                sys.exit(1)

            with sync_playwright() as p:
                adapter.interactive_login(p)
            logger.info(f"{adapter.name.title()} session saved. Continuing...")

    # Polling loop
    logger.info(f"Polling every {CHECK_INTERVAL}s. Press Ctrl+C to stop.")
    try:
        while True:
            for platform_name in platforms:
                adapter = get_adapter(platform_name)
                process_posts_for_platform(adapter, dry_run=False)
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Stopping social media poster...")
    logger.info("Social media poster stopped.")


if __name__ == "__main__":
    main()
