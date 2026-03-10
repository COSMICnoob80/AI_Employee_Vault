#!/usr/bin/env python3
"""
CEO Briefing Generator for AI Employee Vault

Aggregates vault data into a structured weekly executive status report.
Scans Needs_Action/, Done/, Pending_Approval/, and system PIDs to build
a comprehensive snapshot of AI Employee operations.

Usage:
    python ceo_briefing.py                    # Generate current week briefing
    python ceo_briefing.py --dry-run          # Print to stdout, no file writes
    python ceo_briefing.py --week 2026-W10    # Specific ISO week
    python ceo_briefing.py --output report.md # Custom output path

Dependencies:
    pip install pyyaml  (optional, falls back to regex parsing)
"""

import argparse
import logging
import os
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

# Cross-domain integration (graceful fallback)
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from cross_domain import UnifiedView, detect_cross_domain_insights
    CROSS_DOMAIN_AVAILABLE = True
except ImportError:
    CROSS_DOMAIN_AVAILABLE = False

# Configuration
VAULT_ROOT = Path.home() / "AI_Employee_Vault"
NEEDS_ACTION_DIR = VAULT_ROOT / "Needs_Action"
DONE_DIR = VAULT_ROOT / "Done"
PLANS_DIR = VAULT_ROOT / "Plans"
PENDING_DIR = VAULT_ROOT / "Pending_Approval"
APPROVED_DIR = VAULT_ROOT / "Approved"
REPORTS_DIR = VAULT_ROOT / "Reports"
LOG_DIR = VAULT_ROOT / "Logs"

# Setup logging
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "ceo_briefing.log"),
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


def get_iso_week_range(year: int, week: int) -> tuple:
    """Return (monday, sunday) dates for a given ISO year and week."""
    # Jan 4 is always in ISO week 1
    jan4 = datetime(year, 1, 4)
    start_of_week1 = jan4 - timedelta(days=jan4.isoweekday() - 1)
    monday = start_of_week1 + timedelta(weeks=week - 1)
    sunday = monday + timedelta(days=6)
    return monday, sunday


def parse_week_arg(week_str: str) -> tuple:
    """Parse --week YYYY-WNN argument. Returns (year, week_number)."""
    try:
        parts = week_str.split('-W')
        if len(parts) != 2:
            raise ValueError
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        raise argparse.ArgumentTypeError(
            f"Invalid week format: '{week_str}'. Use YYYY-WNN (e.g. 2026-W10)"
        )


class CEOBriefingGenerator:
    """Generates a weekly CEO briefing report from vault data."""

    def __init__(self, week_start: datetime, week_end: datetime, week_label: str):
        self.week_start = week_start
        self.week_end = week_end
        self.week_label = week_label

    def collect_email_tasks(self) -> dict:
        """Scan Needs_Action/EMAIL_*.md, group by priority."""
        result = {"urgent": [], "high": [], "normal": []}
        if not NEEDS_ACTION_DIR.exists():
            return result

        for filepath in sorted(NEEDS_ACTION_DIR.glob("EMAIL_*.md")):
            fm = parse_frontmatter(filepath)
            sender = fm.get("from", "Unknown")
            subject = fm.get("subject", filepath.stem)
            priority = str(fm.get("priority", "normal")).lower()

            entry = {"file": filepath.name, "from": sender, "subject": subject}

            if priority == "urgent":
                result["urgent"].append(entry)
            elif priority == "high":
                result["high"].append(entry)
            else:
                result["normal"].append(entry)

        return result

    def collect_task_stats(self) -> dict:
        """Count files in key vault directories."""
        def count_md(d: Path) -> int:
            if not d.exists():
                return 0
            return len(list(d.glob("*.md")))

        return {
            "needs_action": count_md(NEEDS_ACTION_DIR),
            "done": count_md(DONE_DIR),
            "plans": count_md(PLANS_DIR),
            "pending_approval": count_md(PENDING_DIR),
            "approved": count_md(APPROVED_DIR),
        }

    def collect_completed_this_week(self) -> list:
        """Filter Done/ by timestamp fields within the week range."""
        completed = []
        if not DONE_DIR.exists():
            return completed

        for filepath in sorted(DONE_DIR.glob("*.md")):
            fm = parse_frontmatter(filepath)
            # Check multiple timestamp fields
            for ts_field in ["completed", "posted", "requested", "created"]:
                ts_val = fm.get(ts_field)
                if ts_val:
                    try:
                        ts_str = str(ts_val).replace("T", " ")[:19]
                        ts = datetime.fromisoformat(ts_str)
                        if self.week_start <= ts <= self.week_end + timedelta(days=1):
                            completed.append({
                                "file": filepath.name,
                                "type": fm.get("type", "unknown"),
                                "action_type": fm.get("action_type", ""),
                                "date": ts.strftime("%Y-%m-%d"),
                            })
                            break
                    except (ValueError, TypeError):
                        continue

        return completed

    def collect_linkedin_activity(self) -> dict:
        """Filter Done/ for action_type: linkedin_post."""
        all_posts = []
        this_week = []
        if not DONE_DIR.exists():
            return {"all_posts": all_posts, "this_week": this_week}

        for filepath in sorted(DONE_DIR.glob("*.md")):
            fm = parse_frontmatter(filepath)
            if fm.get("action_type") == "linkedin_post":
                post_info = {
                    "file": filepath.name,
                    "posted": str(fm.get("posted", fm.get("created", "unknown"))),
                }
                all_posts.append(post_info)

                # Check if this week
                for ts_field in ["posted", "created"]:
                    ts_val = fm.get(ts_field)
                    if ts_val:
                        try:
                            ts_str = str(ts_val).replace("T", " ")[:19]
                            ts = datetime.fromisoformat(ts_str)
                            if self.week_start <= ts <= self.week_end + timedelta(days=1):
                                this_week.append(post_info)
                                break
                        except (ValueError, TypeError):
                            continue

        return {"all_posts": all_posts, "this_week": this_week}

    def collect_system_health(self) -> list:
        """Check *.pid files for watcher liveness."""
        watchers = []
        pid_files = list(VAULT_ROOT.glob("*.pid"))

        if not pid_files:
            # Check common watcher names even without PID files
            known_watchers = [
                ("filesystem_watcher", "Watchers/filesystem_watcher.py"),
                ("gmail_watcher", "Watchers/gmail_watcher.py"),
                ("approval_watcher", "Watchers/approval_watcher.py"),
            ]
            for name, script in known_watchers:
                watchers.append({
                    "name": name,
                    "script": script,
                    "status": "no PID file",
                    "pid": None,
                })
            return watchers

        for pid_file in sorted(pid_files):
            name = pid_file.stem
            try:
                pid = int(pid_file.read_text().strip())
                # Check if process is alive
                os.kill(pid, 0)
                status = "running"
            except (ValueError, ProcessLookupError, PermissionError):
                pid = None
                status = "stopped"
            except Exception:
                pid = None
                status = "unknown"

            watchers.append({
                "name": name,
                "script": f"Watchers/{name}.py",
                "status": status,
                "pid": pid,
            })

        return watchers

    def collect_pending_approvals(self) -> list:
        """Scan Pending_Approval/ frontmatter."""
        approvals = []
        if not PENDING_DIR.exists():
            return approvals

        for filepath in sorted(PENDING_DIR.glob("*.md")):
            fm = parse_frontmatter(filepath)
            approvals.append({
                "file": filepath.name,
                "type": fm.get("action_type", fm.get("type", "unknown")),
                "priority": fm.get("priority", "normal"),
                "requested": str(fm.get("requested", fm.get("created", "unknown"))),
                "status": fm.get("status", "pending"),
            })

        return approvals

    def build_action_items(self, emails: dict, approvals: list, health: list) -> list:
        """Derive actionable items from urgent emails, pending approvals, stopped watchers."""
        items = []

        # Urgent/high emails needing attention
        for email in emails.get("urgent", []):
            items.append(f"Review urgent email from {email['from']}: {email['subject']}")
        for email in emails.get("high", [])[:3]:
            items.append(f"Review high-priority email from {email['from']}: {email['subject']}")

        # Pending approvals
        for approval in approvals:
            items.append(
                f"Approve/reject: {approval['file']} ({approval['type']}, "
                f"priority: {approval['priority']})"
            )

        # Stopped watchers
        for watcher in health:
            if watcher["status"] in ("stopped", "no PID file"):
                items.append(f"Restart watcher: {watcher['name']} ({watcher['status']})")

        return items

    def generate_report(self) -> str:
        """Build the full CEO briefing markdown."""
        logger.info("Collecting vault data...")

        emails = self.collect_email_tasks()
        stats = self.collect_task_stats()
        completed = self.collect_completed_this_week()
        linkedin = self.collect_linkedin_activity()
        health = self.collect_system_health()
        approvals = self.collect_pending_approvals()
        action_items = self.build_action_items(emails, approvals, health)

        now = datetime.now()
        total_emails = sum(len(v) for v in emails.values())
        urgent_count = len(emails["urgent"])
        high_count = len(emails["high"])

        # Build attention callout
        attention_parts = []
        if urgent_count > 0:
            attention_parts.append(f"{urgent_count} urgent email(s)")
        if len(approvals) > 0:
            attention_parts.append(f"{len(approvals)} pending approval(s)")
        stopped_watchers = [w for w in health if w["status"] in ("stopped", "no PID file")]
        if stopped_watchers:
            attention_parts.append(f"{len(stopped_watchers)} watcher(s) not running")

        attention_line = ""
        if attention_parts:
            attention_line = f"\n> **Attention Required:** {', '.join(attention_parts)}\n"

        # --- Build report ---
        lines = []

        # YAML frontmatter
        lines.append("---")
        lines.append("type: ceo_briefing")
        lines.append(f"week: \"{self.week_label}\"")
        lines.append(f"generated: {now.isoformat()}")
        lines.append(f"period_start: {self.week_start.strftime('%Y-%m-%d')}")
        lines.append(f"period_end: {self.week_end.strftime('%Y-%m-%d')}")
        lines.append("---")
        lines.append("")

        # Title
        lines.append(f"# CEO Briefing — {self.week_label}")
        lines.append(f"_Generated: {now.strftime('%Y-%m-%d %H:%M')}_")
        lines.append("")

        # 1. Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(
            f"This week the AI Employee processed **{total_emails} email(s)** "
            f"in the queue ({urgent_count} urgent, {high_count} high priority), "
            f"completed **{len(completed)} task(s)**, and has "
            f"**{stats['pending_approval']} item(s)** awaiting approval. "
            f"Currently **{stats['needs_action']} task(s)** need action and "
            f"**{stats['done']} total** are in the Done archive."
        )
        if attention_line:
            lines.append(attention_line)
        lines.append("")

        # 2. Email Digest
        lines.append("## Email Digest")
        lines.append("")
        lines.append("| Priority | Count |")
        lines.append("|----------|-------|")
        lines.append(f"| Urgent | {urgent_count} |")
        lines.append(f"| High | {high_count} |")
        lines.append(f"| Normal | {len(emails['normal'])} |")
        lines.append(f"| **Total** | **{total_emails}** |")
        lines.append("")

        if urgent_count > 0 or high_count > 0:
            lines.append("### Top Priority Emails")
            lines.append("")
            for email in (emails["urgent"] + emails["high"])[:5]:
                lines.append(f"- **{email['from']}**: {email['subject']}")
            lines.append("")

        # 3. Calendar Events (live data or fallback)
        lines.append("## Calendar Events")
        lines.append("")
        if CROSS_DOMAIN_AVAILABLE:
            try:
                cal_data = UnifiedView()._collect_calendar_data()
                if cal_data.get("available") and cal_data.get("events"):
                    lines.append("| Date/Time | Event |")
                    lines.append("|-----------|-------|")
                    for event in cal_data["events"]:
                        lines.append(f"| {event['start']} | {event['summary']} |")
                elif cal_data.get("available"):
                    lines.append("_No upcoming events in the next 7 days._")
                else:
                    lines.append("_Calendar token unavailable — run calendar_server.py to authenticate._")
            except Exception as e:
                lines.append(f"_Calendar data error: {e}_")
        else:
            lines.append("_Calendar integration unavailable — install cross_domain module._")
        lines.append("")

        # 4. Task Status
        lines.append("## Task Status")
        lines.append("")
        lines.append("| Directory | Count |")
        lines.append("|-----------|-------|")
        lines.append(f"| Needs_Action | {stats['needs_action']} |")
        lines.append(f"| Plans | {stats['plans']} |")
        lines.append(f"| Pending_Approval | {stats['pending_approval']} |")
        lines.append(f"| Approved | {stats['approved']} |")
        lines.append(f"| Done | {stats['done']} |")
        lines.append("")

        if completed:
            lines.append("### Completed This Week")
            lines.append("")
            for item in completed:
                action = f" ({item['action_type']})" if item['action_type'] else ""
                lines.append(f"- {item['file']} — {item['type']}{action} ({item['date']})")
            lines.append("")

        # 5. LinkedIn Activity
        lines.append("## LinkedIn Activity")
        lines.append("")
        lines.append(f"- **Posts this week:** {len(linkedin['this_week'])}")
        lines.append(f"- **All-time posts:** {len(linkedin['all_posts'])}")
        if linkedin["this_week"]:
            lines.append("")
            for post in linkedin["this_week"]:
                lines.append(f"  - {post['file']} (posted: {post['posted']})")
        lines.append("")

        # 6. System Health
        lines.append("## System Health")
        lines.append("")
        lines.append("| Watcher | Status | PID |")
        lines.append("|---------|--------|-----|")
        for w in health:
            indicator = "running" if w["status"] == "running" else w["status"]
            pid_str = str(w["pid"]) if w["pid"] else "—"
            lines.append(f"| {w['name']} | {indicator} | {pid_str} |")
        lines.append("")

        # 7. Pending Approvals
        lines.append("## Pending Approvals")
        lines.append("")
        if approvals:
            lines.append("| File | Type | Priority | Requested |")
            lines.append("|------|------|----------|-----------|")
            for a in approvals:
                lines.append(f"| {a['file']} | {a['type']} | {a['priority']} | {a['requested']} |")
        else:
            lines.append("_No pending approvals._")
        lines.append("")

        # 8. Action Items
        lines.append("## Action Items")
        lines.append("")
        if action_items:
            for item in action_items:
                lines.append(f"- [ ] {item}")
        else:
            lines.append("_No action items this week._")
        lines.append("")

        # 9. Metrics Summary
        lines.append("## Metrics Summary")
        lines.append("")
        lines.append("| KPI | Value |")
        lines.append("|-----|-------|")
        lines.append(f"| Emails in queue | {total_emails} |")
        lines.append(f"| Tasks completed this week | {len(completed)} |")
        lines.append(f"| Pending approvals | {len(approvals)} |")
        lines.append(f"| LinkedIn posts this week | {len(linkedin['this_week'])} |")
        lines.append(f"| LinkedIn posts all-time | {len(linkedin['all_posts'])} |")
        running_count = len([w for w in health if w["status"] == "running"])
        lines.append(f"| Watchers running | {running_count}/{len(health)} |")
        lines.append(f"| Total done (all time) | {stats['done']} |")
        lines.append("")

        # 10. Cross-Domain Sections (when available)
        if CROSS_DOMAIN_AVAILABLE:
            try:
                unified = UnifiedView().build()
                email_data = unified.get("email", {})
                task_data = unified.get("tasks", {})
                cal_data = unified.get("calendar", {})
                li_data = unified.get("linkedin", {})

                # Personal Affairs
                lines.append("## Personal Affairs")
                lines.append("")
                lines.append(f"- **Personal emails in queue:** {email_data.get('personal', 0)}")
                if cal_data.get("available"):
                    lines.append(f"- **Calendar events (7d):** {cal_data.get('count', 0)}")
                na_personal = task_data.get("needs_action", {}).get("personal", 0)
                lines.append(f"- **Personal tasks pending:** {na_personal}")
                lines.append("")

                # Business Operations
                lines.append("## Business Operations")
                lines.append("")
                lines.append(f"- **Business emails in queue:** {email_data.get('business', 0)}")
                lines.append(f"- **LinkedIn posts this week:** {li_data.get('this_week', 0)}")
                na_business = task_data.get("needs_action", {}).get("business", 0)
                lines.append(f"- **Business tasks pending:** {na_business}")
                lines.append("")

                # Cross-Domain Insights
                insights = detect_cross_domain_insights(unified)
                lines.append("## Cross-Domain Insights")
                lines.append("")
                if insights:
                    for insight in insights:
                        lines.append(f"- {insight}")
                else:
                    lines.append("_No cross-domain patterns detected._")
                lines.append("")
            except Exception as e:
                logger.warning(f"Cross-domain sections unavailable: {e}")

        return "\n".join(lines)

    def run(self, dry_run: bool = False, output_path: Path = None) -> Path:
        """Generate and optionally write the briefing report."""
        REPORTS_DIR.mkdir(exist_ok=True)

        report = self.generate_report()

        if dry_run:
            print(report)
            logger.info("Dry run complete — no file written")
            return None

        if output_path is None:
            date_str = self.week_start.strftime("%Y-%m-%d")
            output_path = REPORTS_DIR / f"CEO_Briefing_{date_str}.md"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding='utf-8')
        logger.info(f"CEO Briefing written to: {output_path}")
        return output_path


def get_mock_data_report() -> str:
    """Generate a briefing with hardcoded mock data for --dry-run without vault."""
    now = datetime.now()
    iso = now.isocalendar()
    week_label = f"{iso[0]}-W{iso[1]:02d}"

    return f"""---
type: ceo_briefing
week: "{week_label}"
generated: {now.isoformat()}
period_start: 2026-03-02
period_end: 2026-03-08
---

# CEO Briefing — {week_label}
_Generated: {now.strftime('%Y-%m-%d %H:%M')} (DRY RUN — mock data)_

## Executive Summary

This week the AI Employee processed **5 email(s)** in the queue (1 urgent, 2 high priority), completed **3 task(s)**, and has **2 item(s)** awaiting approval. Currently **5 task(s)** need action and **10 total** are in the Done archive.

> **Attention Required:** 1 urgent email(s), 2 pending approval(s), 1 watcher(s) not running

## Email Digest

| Priority | Count |
|----------|-------|
| Urgent | 1 |
| High | 2 |
| Normal | 2 |
| **Total** | **5** |

### Top Priority Emails

- **CEO <ceo@example.com>**: Q1 Revenue Review — Action Required
- **Finqalab <support@finqalab.com>**: Payment Processing Update
- **HR <hr@example.com>**: Quarterly Compliance Deadline

## Calendar Events

_No calendar integration yet — coming in G4 (Additional MCP Servers)._

## Task Status

| Directory | Count |
|-----------|-------|
| Needs_Action | 5 |
| Plans | 3 |
| Pending_Approval | 2 |
| Approved | 1 |
| Done | 10 |

### Completed This Week

- invoice_processing.md — task (2026-03-03)
- email_response_draft.md — approval_request (2026-03-04)
- linkedin_post_q1.md — approval_request (linkedin_post) (2026-03-05)

## LinkedIn Activity

- **Posts this week:** 1
- **All-time posts:** 4

  - linkedin_post_q1.md (posted: 2026-03-05T14:30:00)

## System Health

| Watcher | Status | PID |
|---------|--------|-----|
| filesystem_watcher | running | 12345 |
| gmail_watcher | running | 12346 |
| approval_watcher | stopped | — |

## Pending Approvals

| File | Type | Priority | Requested |
|------|------|----------|-----------|
| send_client_email.md | email | high | 2026-03-04 |
| software_purchase.md | financial | normal | 2026-03-03 |

## Action Items

- [ ] Review urgent email from CEO <ceo@example.com>: Q1 Revenue Review — Action Required
- [ ] Approve/reject: send_client_email.md (email, priority: high)
- [ ] Approve/reject: software_purchase.md (financial, priority: normal)
- [ ] Restart watcher: approval_watcher (stopped)

## Metrics Summary

| KPI | Value |
|-----|-------|
| Emails in queue | 5 |
| Tasks completed this week | 3 |
| Pending approvals | 2 |
| LinkedIn posts this week | 1 |
| LinkedIn posts all-time | 4 |
| Watchers running | 2/3 |
| Total done (all time) | 10 |
"""


def main():
    """Main entry point for the CEO Briefing Generator."""
    parser = argparse.ArgumentParser(
        description="CEO Briefing Generator for AI Employee Vault"
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Print report to stdout with no file writes'
    )
    parser.add_argument(
        '--week', type=str, default=None,
        help='Target ISO week (YYYY-WNN, e.g. 2026-W10). Default: current week'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Custom output path (default: Reports/CEO_Briefing_YYYY-MM-DD.md)'
    )
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("CEO Briefing Generator Starting")
    if args.dry_run:
        logger.info("Mode: DRY RUN")
    if args.week:
        logger.info(f"Target week: {args.week}")
    logger.info("=" * 50)

    # Determine week range
    if args.week:
        year, week_num = parse_week_arg(args.week)
        week_label = f"{year}-W{week_num:02d}"
    else:
        now = datetime.now()
        iso = now.isocalendar()
        year, week_num = iso[0], iso[1]
        week_label = f"{year}-W{week_num:02d}"

    week_start, week_end = get_iso_week_range(year, week_num)

    logger.info(f"Week: {week_label} ({week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')})")

    output_path = Path(args.output) if args.output else None

    generator = CEOBriefingGenerator(week_start, week_end, week_label)
    result = generator.run(dry_run=args.dry_run, output_path=output_path)

    if result:
        logger.info(f"Report saved: {result}")
    logger.info("CEO Briefing Generator finished")


if __name__ == "__main__":
    main()
