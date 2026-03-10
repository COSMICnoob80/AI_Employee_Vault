#!/usr/bin/env python3
"""
Cross-Domain Integration Module for AI Employee Vault

Bridges personal and business vault domains with:
- Domain tagging and routing (DomainRouter)
- Unified view aggregation (UnifiedView)
- Backfill utility for existing files
- Cross-domain insight detection

Usage:
    python cross_domain.py --dry-run              # Print unified summary
    python cross_domain.py --domain personal      # Filter personal only
    python cross_domain.py --backfill --dry-run   # Preview backfill
    python cross_domain.py --json                 # Output as JSON

Dependencies:
    pip install pyyaml  (optional, falls back to regex parsing)
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

# Allow importing vault_audit from Watchers/
VAULT_ROOT = Path.home() / "AI_Employee_Vault"
sys.path.insert(0, str(VAULT_ROOT / "Watchers"))
sys.path.insert(0, str(VAULT_ROOT / "MCP"))

from vault_audit import audit_log, safe_write, ErrorTracker, retry

# Calendar integration (graceful fallback)
try:
    from calendar_server import get_calendar_service, _list_events_api
    CALENDAR_AVAILABLE = True
except Exception:
    CALENDAR_AVAILABLE = False

# Configuration
NEEDS_ACTION_DIR = VAULT_ROOT / "Needs_Action"
DONE_DIR = VAULT_ROOT / "Done"
PENDING_DIR = VAULT_ROOT / "Pending_Approval"
APPROVED_DIR = VAULT_ROOT / "Approved"
LOG_DIR = VAULT_ROOT / "Logs"

# Setup logging
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "cross_domain.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Business keyword sets
BUSINESS_FILE_KEYWORDS = {
    "invoice", "contract", "client", "project", "meeting-notes",
    "quarterly", "budget", "proposal"
}
BUSINESS_SENDER_KEYWORDS = {
    "invoice", "payment", "contract", "finqalab", "client", "project",
    "quarterly", "compliance", "hr@", "finance@", "billing"
}


def parse_frontmatter(filepath: Path) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    try:
        content = filepath.read_text(encoding='utf-8')
    except (UnicodeDecodeError, Exception):
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
        except Exception:
            return {}
    else:
        result = {}
        for line in raw_frontmatter.strip().splitlines():
            if ':' in line:
                key, _, value = line.partition(':')
                result[key.strip()] = value.strip()
        return result


class DomainRouter:
    """Routes and filters vault files by domain tag."""

    def __init__(self, domain_filter: str = "all"):
        self.domain_filter = domain_filter

    def scan_directory(self, dir_path: Path) -> list:
        """Parse frontmatter from all .md files in a directory."""
        results = []
        if not dir_path.exists():
            return results

        for filepath in sorted(dir_path.glob("*.md")):
            fm = parse_frontmatter(filepath)
            fm["_filepath"] = str(filepath)
            fm["_filename"] = filepath.name
            results.append(fm)

        return results

    def filter_by_domain(self, files: list, domain: str) -> list:
        """Filter file metadata list by domain tag."""
        if domain == "all":
            return files
        return [f for f in files if f.get("domain", "unknown") == domain]

    def get_tasks(self, domain: str = "all") -> dict:
        """Scan task directories and return domain-filtered results."""
        all_tasks = {
            "needs_action": self.scan_directory(NEEDS_ACTION_DIR),
            "done": self.scan_directory(DONE_DIR),
            "pending_approval": self.scan_directory(PENDING_DIR),
        }

        if domain != "all":
            for key in all_tasks:
                all_tasks[key] = self.filter_by_domain(all_tasks[key], domain)

        return all_tasks


class UnifiedView:
    """Aggregates data across all vault domains into a unified structure."""

    def __init__(self):
        self.router = DomainRouter()

    def _collect_email_data(self) -> dict:
        """Count personal vs business email tasks."""
        emails = self.router.scan_directory(NEEDS_ACTION_DIR)
        email_tasks = [e for e in emails if e.get("type") == "email"]

        personal = [e for e in email_tasks if e.get("domain") != "business"]
        business = [e for e in email_tasks if e.get("domain") == "business"]

        return {
            "total": len(email_tasks),
            "personal": len(personal),
            "business": len(business),
        }

    def _collect_calendar_data(self) -> dict:
        """Fetch calendar events via calendar_server integration."""
        if not CALENDAR_AVAILABLE:
            return {"available": False, "events": [], "count": 0}

        try:
            from datetime import timezone
            service = get_calendar_service()
            now = datetime.now(timezone.utc)
            time_min = now.isoformat()
            time_max = (now + timedelta(days=7)).isoformat()
            result = _list_events_api(service, time_min, time_max, 20)
            events = result.get("items", [])

            formatted = []
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                summary = event.get("summary", "(No title)")
                # Calculate duration
                end = event["end"].get("dateTime", event["end"].get("date"))
                formatted.append({
                    "start": start,
                    "end": end,
                    "summary": summary,
                })

            return {"available": True, "events": formatted, "count": len(formatted)}
        except Exception as e:
            logger.warning(f"Calendar data unavailable: {e}")
            return {"available": False, "events": [], "count": 0, "error": str(e)}

    def _collect_task_data(self) -> dict:
        """Count tasks by domain across directories."""
        tasks = self.router.get_tasks()
        result = {}

        for directory, items in tasks.items():
            personal = [i for i in items if i.get("domain") != "business"]
            business = [i for i in items if i.get("domain") == "business"]
            result[directory] = {
                "total": len(items),
                "personal": len(personal),
                "business": len(business),
            }

        return result

    def _collect_linkedin_data(self) -> dict:
        """Collect LinkedIn post data from Done/ (always business domain)."""
        done_files = self.router.scan_directory(DONE_DIR)
        posts = [f for f in done_files if f.get("action_type") == "linkedin_post"]

        now = datetime.now()
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        this_week = []
        for post in posts:
            for ts_field in ["posted", "created"]:
                ts_val = post.get(ts_field)
                if ts_val:
                    try:
                        ts_str = str(ts_val).replace("T", " ")[:19]
                        ts = datetime.fromisoformat(ts_str)
                        if ts >= week_start:
                            this_week.append(post.get("_filename", ""))
                            break
                    except (ValueError, TypeError):
                        continue

        return {
            "total_posts": len(posts),
            "this_week": len(this_week),
            "domain": "business",
        }

    def _collect_system_health(self) -> list:
        """Check watcher PID files for liveness."""
        watchers = []
        pid_files = list(VAULT_ROOT.glob("*.pid"))

        if not pid_files:
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

    def build(self) -> dict:
        """Build the full unified data structure."""
        data = {
            "generated": datetime.now().isoformat(),
            "email": self._collect_email_data(),
            "calendar": self._collect_calendar_data(),
            "tasks": self._collect_task_data(),
            "linkedin": self._collect_linkedin_data(),
            "system_health": self._collect_system_health(),
        }

        audit_log("unified_view_built", "cross_domain", {
            "email_total": data["email"]["total"],
            "calendar_available": data["calendar"]["available"],
            "calendar_events": data["calendar"]["count"],
        })

        return data


def get_personal_summary() -> dict:
    """Get summary of personal domain data."""
    router = DomainRouter(domain_filter="personal")
    tasks = router.get_tasks(domain="personal")
    view = UnifiedView()
    email = view._collect_email_data()
    calendar = view._collect_calendar_data()

    return {
        "domain": "personal",
        "email_count": email["personal"],
        "calendar": calendar,
        "tasks": {k: len(v) for k, v in tasks.items()},
    }


def get_business_summary() -> dict:
    """Get summary of business domain data."""
    router = DomainRouter(domain_filter="business")
    tasks = router.get_tasks(domain="business")
    view = UnifiedView()
    email = view._collect_email_data()
    linkedin = view._collect_linkedin_data()

    return {
        "domain": "business",
        "email_count": email["business"],
        "linkedin": linkedin,
        "tasks": {k: len(v) for k, v in tasks.items()},
    }


def get_unified_summary() -> dict:
    """Get full unified summary across all domains."""
    view = UnifiedView()
    return view.build()


def backfill_domains(dry_run: bool = False) -> dict:
    """Backfill domain tags on existing files missing the domain field."""
    stats = {"scanned": 0, "updated": 0, "skipped": 0, "errors": 0}
    dirs_to_scan = [NEEDS_ACTION_DIR, DONE_DIR, PENDING_DIR]

    for scan_dir in dirs_to_scan:
        if not scan_dir.exists():
            continue

        for filepath in sorted(scan_dir.glob("*.md")):
            stats["scanned"] += 1

            try:
                content = filepath.read_text(encoding='utf-8')
            except Exception:
                stats["errors"] += 1
                continue

            if not content.startswith('---'):
                stats["skipped"] += 1
                continue

            parts = content.split('---', 2)
            if len(parts) < 3:
                stats["skipped"] += 1
                continue

            fm_text = parts[1]

            # Skip if domain already exists
            if re.search(r'^domain:', fm_text, re.MULTILINE):
                stats["skipped"] += 1
                continue

            # Determine domain heuristically
            fm = parse_frontmatter(filepath)
            file_type = fm.get("type", "")
            domain = "personal"  # default

            if file_type == "email":
                sender = str(fm.get("from", "")).lower()
                subject = str(fm.get("subject", "")).lower()
                if any(kw in sender or kw in subject for kw in BUSINESS_SENDER_KEYWORDS):
                    domain = "business"
            elif file_type == "file_drop":
                source = str(fm.get("source", "")).lower()
                if any(kw in source for kw in BUSINESS_FILE_KEYWORDS):
                    domain = "business"
            elif fm.get("action_type") == "linkedin_post":
                domain = "business"

            # Insert domain line after priority: or status: in frontmatter
            new_fm = fm_text
            inserted = False
            for anchor in ["priority:", "status:"]:
                if anchor in new_fm:
                    lines = new_fm.splitlines()
                    new_lines = []
                    for line in lines:
                        new_lines.append(line)
                        if line.strip().startswith(anchor):
                            new_lines.append(f"domain: {domain}")
                            inserted = True
                            break
                    if inserted:
                        # Add remaining lines
                        idx = lines.index(next(l for l in lines if l.strip().startswith(anchor)))
                        new_lines.extend(lines[idx + 1:])
                        new_fm = "\n".join(new_lines)
                        break

            if not inserted:
                # Append before end of frontmatter
                new_fm = fm_text.rstrip() + f"\ndomain: {domain}\n"

            new_content = f"---{new_fm}---{parts[2]}"

            if dry_run:
                logger.info(f"[DRY-RUN] Would tag {filepath.name} as domain: {domain}")
            else:
                safe_write(filepath, new_content)
                logger.info(f"Tagged {filepath.name} as domain: {domain}")
                audit_log("domain_backfill", "cross_domain", {
                    "file": filepath.name,
                    "domain": domain,
                })

            stats["updated"] += 1

    return stats


def detect_cross_domain_insights(unified: dict) -> list:
    """Detect cross-domain patterns and generate insight strings."""
    insights = []

    email = unified.get("email", {})
    calendar = unified.get("calendar", {})
    tasks = unified.get("tasks", {})

    # Business emails but no calendar meetings
    if email.get("business", 0) > 0 and calendar.get("available") and calendar.get("count", 0) == 0:
        insights.append(
            f"{email['business']} business email(s) but no calendar meetings this week"
        )

    # Personal tasks backlog
    na_tasks = tasks.get("needs_action", {})
    personal_pending = na_tasks.get("personal", 0)
    if personal_pending > 3:
        insights.append(
            f"Personal tasks backlog: {personal_pending} tasks pending"
        )

    # Approval queue age check
    pending_files = list(PENDING_DIR.glob("*.md")) if PENDING_DIR.exists() else []
    old_approvals = 0
    for fp in pending_files:
        fm = parse_frontmatter(fp)
        for ts_field in ["requested", "created"]:
            ts_val = fm.get(ts_field)
            if ts_val:
                try:
                    ts_str = str(ts_val).replace("T", " ")[:19]
                    ts = datetime.fromisoformat(ts_str)
                    if (datetime.now() - ts).days > 3:
                        old_approvals += 1
                    break
                except (ValueError, TypeError):
                    continue
    if old_approvals > 0:
        insights.append(
            f"Approval queue has {old_approvals} item(s) older than 3 days"
        )

    # Email volume comparison
    personal_emails = email.get("personal", 0)
    business_emails = email.get("business", 0)
    if personal_emails > 0 and business_emails > 0:
        ratio = max(personal_emails, business_emails) / max(min(personal_emails, business_emails), 1)
        if ratio > 3:
            dominant = "personal" if personal_emails > business_emails else "business"
            insights.append(
                f"Email volume skew: {dominant} emails outnumber the other domain {ratio:.0f}:1"
            )

    # Calendar load
    if calendar.get("available") and calendar.get("count", 0) > 5:
        insights.append(
            f"Heavy calendar week: {calendar['count']} events in the next 7 days"
        )

    return insights


def format_markdown(unified: dict, domain_filter: str = "all") -> str:
    """Format unified data as readable markdown."""
    lines = []
    now = datetime.now()
    lines.append(f"# Cross-Domain Summary — {now.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"_Domain filter: {domain_filter}_")
    lines.append("")

    # Email summary
    email = unified["email"]
    lines.append("## Email Tasks")
    lines.append("")
    lines.append("| Domain | Count |")
    lines.append("|--------|-------|")
    lines.append(f"| Personal | {email['personal']} |")
    lines.append(f"| Business | {email['business']} |")
    lines.append(f"| **Total** | **{email['total']}** |")
    lines.append("")

    # Calendar
    cal = unified["calendar"]
    lines.append("## Calendar Events (Next 7 Days)")
    lines.append("")
    if cal["available"] and cal["events"]:
        lines.append("| Date/Time | Event |")
        lines.append("|-----------|-------|")
        for event in cal["events"]:
            lines.append(f"| {event['start']} | {event['summary']} |")
    elif cal["available"]:
        lines.append("_No upcoming events._")
    else:
        lines.append("_Calendar integration unavailable._")
    lines.append("")

    # Tasks by domain
    tasks = unified["tasks"]
    lines.append("## Tasks by Domain")
    lines.append("")
    lines.append("| Directory | Personal | Business | Total |")
    lines.append("|-----------|----------|----------|-------|")
    for directory, counts in tasks.items():
        lines.append(
            f"| {directory} | {counts['personal']} | {counts['business']} | {counts['total']} |"
        )
    lines.append("")

    # LinkedIn
    li = unified["linkedin"]
    lines.append("## LinkedIn Activity (Business)")
    lines.append("")
    lines.append(f"- Posts this week: {li['this_week']}")
    lines.append(f"- All-time posts: {li['total_posts']}")
    lines.append("")

    # System health
    lines.append("## System Health")
    lines.append("")
    lines.append("| Watcher | Status | PID |")
    lines.append("|---------|--------|-----|")
    for w in unified["system_health"]:
        pid_str = str(w["pid"]) if w["pid"] else "—"
        lines.append(f"| {w['name']} | {w['status']} | {pid_str} |")
    lines.append("")

    # Cross-domain insights
    insights = detect_cross_domain_insights(unified)
    lines.append("## Cross-Domain Insights")
    lines.append("")
    if insights:
        for insight in insights:
            lines.append(f"- {insight}")
    else:
        lines.append("_No cross-domain patterns detected._")
    lines.append("")

    return "\n".join(lines)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Cross-Domain Integration for AI Employee Vault"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Print output, no file writes")
    parser.add_argument("--domain", choices=["personal", "business", "all"],
                        default="all", help="Domain filter (default: all)")
    parser.add_argument("--backfill", action="store_true",
                        help="One-shot domain tag backfill for existing files")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON instead of markdown")
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("Cross-Domain Integration")
    logger.info(f"Domain: {args.domain}")
    if args.dry_run:
        logger.info("Mode: DRY RUN")
    logger.info("=" * 50)

    if args.backfill:
        stats = backfill_domains(dry_run=args.dry_run)
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print(f"\nBackfill Results:")
            print(f"  Scanned: {stats['scanned']}")
            print(f"  Updated: {stats['updated']}")
            print(f"  Skipped: {stats['skipped']}")
            print(f"  Errors:  {stats['errors']}")
        return

    unified = get_unified_summary()

    if args.domain != "all":
        # Re-collect with domain filter for summary functions
        if args.domain == "personal":
            summary = get_personal_summary()
        else:
            summary = get_business_summary()

        if args.json:
            print(json.dumps(summary, indent=2, default=str))
        else:
            print(json.dumps(summary, indent=2, default=str))
        return

    if args.json:
        print(json.dumps(unified, indent=2, default=str))
    else:
        print(format_markdown(unified, args.domain))

    audit_log("cross_domain_run", "cross_domain", {
        "domain": args.domain,
        "dry_run": args.dry_run,
    })


if __name__ == "__main__":
    main()
