#!/usr/bin/env python3
"""
MCP Odoo Community Server for AI Employee Vault

Exposes 6 accounting tools via the Model Context Protocol using Odoo's
JSON-RPC API. Supports Odoo Community 19+.

Transport: stdio (standard for Claude Code)

Dependencies:
    pip install mcp requests python-dotenv
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv
import os

# Allow importing vault_audit from Watchers/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Watchers"))

from mcp.server.fastmcp import FastMCP
from vault_audit import audit_log, safe_write, retry, ErrorTracker

# Configuration
VAULT_ROOT = Path.home() / "AI_Employee_Vault"
ENV_FILE = VAULT_ROOT / ".env.odoo"

load_dotenv(ENV_FILE)

ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "")
ODOO_USER = os.getenv("ODOO_USER", "")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")

DRY_RUN_MODE = False

mcp = FastMCP("odoo-accounting")
error_tracker = ErrorTracker("odoo_server")


# ---------------------------------------------------------------------------
# Odoo JSON-RPC Client
# ---------------------------------------------------------------------------

class OdooClient:
    """Odoo JSON-RPC client with authentication caching."""

    def __init__(self):
        self.url = ODOO_URL
        self.db = ODOO_DB
        self.user = ODOO_USER
        self.password = ODOO_PASSWORD
        self.uid = None
        self._request_id = 0

    @retry(max_retries=2, retryable=(ConnectionError, TimeoutError, OSError))
    def _jsonrpc_call(self, service: str, method: str, args: list) -> dict:
        """Make a raw JSON-RPC call to Odoo."""
        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": "call",
            "params": {
                "service": service,
                "method": method,
                "args": args,
            },
        }
        resp = requests.post(
            f"{self.url}/jsonrpc",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("error"):
            error_msg = result["error"].get("data", {}).get("message", str(result["error"]))
            raise RuntimeError(f"Odoo RPC error: {error_msg}")
        return result.get("result")

    def authenticate(self):
        """Authenticate with Odoo and cache the uid."""
        uid = self._jsonrpc_call("common", "login", [self.db, self.user, self.password])
        if not uid:
            raise RuntimeError("Odoo authentication failed. Check credentials in .env.odoo")
        self.uid = uid
        return uid

    def version(self):
        """Get Odoo server version info."""
        return self._jsonrpc_call("common", "version", [])

    def execute_kw(self, model: str, method: str, args: list, kwargs: dict = None):
        """Execute a model method via JSON-RPC."""
        if not self.uid:
            self.authenticate()
        return self._jsonrpc_call(
            "object", "execute_kw",
            [self.db, self.uid, self.password, model, method, args, kwargs or {}],
        )


_client = OdooClient()


# ---------------------------------------------------------------------------
# Mock data for dry-run mode
# ---------------------------------------------------------------------------

_MOCK_INVOICES = [
    {"id": 1, "name": "INV/2026/0001", "partner_id": [1, "Test Customer"], "amount_total": 15000.0, "state": "posted", "invoice_date": "2026-03-01"},
    {"id": 2, "name": "INV/2026/0002", "partner_id": [2, "Sample Corp"], "amount_total": 8500.0, "state": "draft", "invoice_date": "2026-03-05"},
]

_MOCK_ACCOUNTS = [
    {"id": 1, "code": "1000", "name": "Cash", "account_type": "asset_cash"},
    {"id": 2, "code": "1100", "name": "Accounts Receivable", "account_type": "asset_receivable"},
    {"id": 3, "code": "2000", "name": "Accounts Payable", "account_type": "liability_payable"},
    {"id": 4, "code": "4000", "name": "Revenue", "account_type": "income"},
]

_MOCK_JOURNAL_ENTRIES = [
    {"id": 1, "name": "MISC/2026/0001", "date": "2026-03-01", "ref": "Opening Balance", "amount_total": 50000.0, "state": "posted"},
    {"id": 2, "name": "MISC/2026/0002", "date": "2026-03-03", "ref": "Office Supplies", "amount_total": 2500.0, "state": "posted"},
]


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def list_invoices(state: str = "", limit: int = 20) -> str:
    """List customer invoices from Odoo.

    Args:
        state: Filter by invoice state (draft, posted, cancel). Empty for all.
        limit: Maximum number of invoices to return (default 20).

    Returns:
        Formatted list of invoices or error message.
    """
    error_tracker.check()
    try:
        audit_log("odoo_list_invoices", "odoo_server", {"state": state, "limit": limit})

        if DRY_RUN_MODE:
            invoices = _MOCK_INVOICES
            if state:
                invoices = [inv for inv in invoices if inv["state"] == state]
            lines = [f"[DRY RUN] Invoices ({len(invoices)} found):"]
            for inv in invoices:
                partner = inv["partner_id"][1] if isinstance(inv["partner_id"], list) else inv["partner_id"]
                lines.append(f"  {inv['name']} | {partner} | {inv['amount_total']:.2f} | {inv['state']} | {inv['invoice_date']}")
            return "\n".join(lines)

        domain = [("move_type", "=", "out_invoice")]
        if state:
            domain.append(("state", "=", state))

        fields = ["name", "partner_id", "amount_total", "state", "invoice_date"]
        invoices = _client.execute_kw(
            "account.move", "search_read",
            [domain],
            {"fields": fields, "limit": limit, "order": "invoice_date desc"},
        )

        if not invoices:
            return "No invoices found."

        lines = [f"Invoices ({len(invoices)} found):"]
        for inv in invoices:
            partner = inv["partner_id"][1] if isinstance(inv["partner_id"], list) else inv["partner_id"]
            lines.append(f"  {inv['name']} | {partner} | {inv['amount_total']:.2f} | {inv['state']} | {inv.get('invoice_date', 'N/A')}")
        return "\n".join(lines)

    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error listing invoices: {e}"


@mcp.tool()
def get_invoice(invoice_id: int) -> str:
    """Get detailed information about a specific invoice.

    Args:
        invoice_id: The Odoo ID of the invoice.

    Returns:
        Invoice details with line items or error message.
    """
    error_tracker.check()
    try:
        audit_log("odoo_get_invoice", "odoo_server", {"invoice_id": invoice_id})

        if DRY_RUN_MODE:
            return (
                "[DRY RUN] Invoice: INV/2026/0001\n"
                "  Partner: Test Customer\n"
                "  Date: 2026-03-01\n"
                "  State: posted\n"
                "  Total: 15000.00\n"
                "  Lines:\n"
                "    1. Consulting Service | Qty: 10 | Price: 1500.00 | Subtotal: 15000.00"
            )

        records = _client.execute_kw(
            "account.move", "read",
            [[invoice_id]],
            {"fields": ["name", "partner_id", "amount_total", "state", "invoice_date", "invoice_line_ids", "narration"]},
        )
        if not records:
            return f"Error: Invoice ID {invoice_id} not found."

        inv = records[0]
        partner = inv["partner_id"][1] if isinstance(inv["partner_id"], list) else inv["partner_id"]

        lines_text = ""
        if inv.get("invoice_line_ids"):
            line_records = _client.execute_kw(
                "account.move.line", "read",
                [inv["invoice_line_ids"]],
                {"fields": ["name", "quantity", "price_unit", "price_subtotal"]},
            )
            for i, line in enumerate(line_records, 1):
                lines_text += f"\n    {i}. {line.get('name', 'N/A')} | Qty: {line.get('quantity', 0)} | Price: {line.get('price_unit', 0):.2f} | Subtotal: {line.get('price_subtotal', 0):.2f}"

        return (
            f"Invoice: {inv['name']}\n"
            f"  Partner: {partner}\n"
            f"  Date: {inv.get('invoice_date', 'N/A')}\n"
            f"  State: {inv['state']}\n"
            f"  Total: {inv['amount_total']:.2f}\n"
            f"  Lines:{lines_text or ' (none)'}"
        )

    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error getting invoice: {e}"


@mcp.tool()
def create_invoice(partner_name: str, lines_json: str, dry_run: bool = True) -> str:
    """Create a draft invoice in Odoo. Requires HITL approval by default.

    Args:
        partner_name: Customer/partner name.
        lines_json: JSON array of line items, each with "product", "quantity", "price".
        dry_run: If True (default), returns a preview without creating. Set False to create + trigger approval.

    Returns:
        Preview, success message, or error description.
    """
    error_tracker.check()
    try:
        lines = json.loads(lines_json)
    except json.JSONDecodeError as e:
        return f"Error: Invalid lines_json — {e}"

    total = sum(line.get("price", 0) * line.get("quantity", 0) for line in lines)

    audit_log("odoo_create_invoice", "odoo_server", {
        "partner": partner_name,
        "lines_count": len(lines),
        "total": total,
        "dry_run": dry_run,
    })

    if dry_run or DRY_RUN_MODE:
        preview_lines = [f"--- DRY RUN PREVIEW ---", f"Partner: {partner_name}", f"Lines:"]
        for i, line in enumerate(lines, 1):
            qty = line.get("quantity", 0)
            price = line.get("price", 0)
            preview_lines.append(f"  {i}. {line.get('product', 'N/A')} | Qty: {qty} | Price: {price:.2f} | Subtotal: {qty * price:.2f}")
        preview_lines.append(f"Total: {total:.2f}")
        preview_lines.append(f"--- END PREVIEW (not created) ---")
        return "\n".join(preview_lines)

    try:
        # Find or note partner
        partners = _client.execute_kw(
            "res.partner", "search_read",
            [[("name", "ilike", partner_name)]],
            {"fields": ["id", "name"], "limit": 1},
        )
        if not partners:
            return f"Error: Partner '{partner_name}' not found in Odoo. Create the partner first."
        partner_id = partners[0]["id"]

        # Build invoice lines
        invoice_lines = []
        for line in lines:
            invoice_lines.append((0, 0, {
                "name": line.get("product", "Service"),
                "quantity": line.get("quantity", 1),
                "price_unit": line.get("price", 0),
            }))

        # Create draft invoice
        invoice_id = _client.execute_kw(
            "account.move", "create",
            [{
                "move_type": "out_invoice",
                "partner_id": partner_id,
                "invoice_line_ids": invoice_lines,
            }],
        )

        # Write HITL approval request
        now = datetime.now()
        slug = partner_name.lower().replace(" ", "_")[:30]
        approval_filename = f"{now.strftime('%Y%m%d')}_odoo_invoice_{slug}.md"
        approval_path = VAULT_ROOT / "Pending_Approval" / approval_filename

        lines_detail = ""
        for i, line in enumerate(lines, 1):
            qty = line.get("quantity", 0)
            price = line.get("price", 0)
            lines_detail += f"| {i} | {line.get('product', 'N/A')} | {qty} | {price:.2f} | {qty * price:.2f} |\n"

        approval_content = f"""---
type: approval_request
action_type: financial
requested: {now.isoformat(timespec='seconds')}
status: pending_approval
priority: normal
domain: business
threshold_exceeded: financial_creation
requester: AI_Employee
---

# Approval Request: Odoo Invoice for {partner_name}

## Action Summary
Draft invoice created in Odoo for {partner_name}.

## Details
- **Partner**: {partner_name}
- **Odoo Invoice ID**: {invoice_id}
- **Total Amount**: {total:.2f}
- **Status**: Draft (awaiting approval to confirm)

## Line Items
| # | Product | Qty | Unit Price | Subtotal |
|---|---------|-----|------------|----------|
{lines_detail}
## Risk Assessment
- **Impact**: Medium (financial commitment)
- **Reversibility**: High (draft can be cancelled in Odoo)
- **Total**: {total:.2f}

## Approval Actions
- [ ] **Approve**: Move this file to `/Approved/` folder
- [ ] **Reject**: Delete this file or add rejection reason below
- [ ] **Defer**: Add comment and leave in `/Pending_Approval/`

## Rejection Reason (if applicable)
_None_
"""
        approval_path.parent.mkdir(parents=True, exist_ok=True)
        safe_write(approval_path, approval_content)

        audit_log("odoo_invoice_approval_created", "odoo_server", {
            "invoice_id": invoice_id,
            "approval_file": str(approval_path),
            "total": total,
        })

        return (
            f"Draft invoice created in Odoo (ID: {invoice_id}).\n"
            f"Approval request written to: {approval_path}\n"
            f"Total: {total:.2f}"
        )

    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error creating invoice: {e}"


@mcp.tool()
def list_accounts() -> str:
    """List the chart of accounts from Odoo.

    Returns:
        Formatted list of accounts with code, name, and type.
    """
    error_tracker.check()
    try:
        audit_log("odoo_list_accounts", "odoo_server", {})

        if DRY_RUN_MODE:
            lines = ["[DRY RUN] Chart of Accounts:"]
            for acc in _MOCK_ACCOUNTS:
                lines.append(f"  {acc['code']} | {acc['name']} | {acc['account_type']}")
            return "\n".join(lines)

        accounts = _client.execute_kw(
            "account.account", "search_read",
            [[]],
            {"fields": ["code", "name", "account_type"], "order": "code"},
        )

        if not accounts:
            return "No accounts found."

        lines = [f"Chart of Accounts ({len(accounts)} accounts):"]
        for acc in accounts:
            lines.append(f"  {acc['code']} | {acc['name']} | {acc.get('account_type', 'N/A')}")
        return "\n".join(lines)

    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error listing accounts: {e}"


@mcp.tool()
def get_journal_entries(date_from: str, date_to: str) -> str:
    """Query journal entries within a date range.

    Args:
        date_from: Start date (YYYY-MM-DD).
        date_to: End date (YYYY-MM-DD).

    Returns:
        Formatted list of journal entries or error message.
    """
    error_tracker.check()
    try:
        audit_log("odoo_get_journal_entries", "odoo_server", {"date_from": date_from, "date_to": date_to})

        if DRY_RUN_MODE:
            lines = [f"[DRY RUN] Journal Entries ({date_from} to {date_to}):"]
            for entry in _MOCK_JOURNAL_ENTRIES:
                lines.append(f"  {entry['name']} | {entry['date']} | {entry['ref']} | {entry['amount_total']:.2f} | {entry['state']}")
            return "\n".join(lines)

        domain = [
            ("date", ">=", date_from),
            ("date", "<=", date_to),
        ]
        fields = ["name", "date", "ref", "amount_total", "state"]
        entries = _client.execute_kw(
            "account.move", "search_read",
            [domain],
            {"fields": fields, "order": "date desc"},
        )

        if not entries:
            return f"No journal entries found between {date_from} and {date_to}."

        lines = [f"Journal Entries ({len(entries)} found, {date_from} to {date_to}):"]
        for entry in entries:
            lines.append(f"  {entry['name']} | {entry['date']} | {entry.get('ref', '')} | {entry['amount_total']:.2f} | {entry['state']}")
        return "\n".join(lines)

    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error getting journal entries: {e}"


@mcp.tool()
def accounting_summary() -> str:
    """Generate an accounting summary with receivables, payables, and cash position.

    Returns:
        Formatted accounting summary for CEO Briefing consumption.
    """
    error_tracker.check()
    try:
        audit_log("odoo_accounting_summary", "odoo_server", {})

        if DRY_RUN_MODE:
            return (
                "[DRY RUN] Accounting Summary\n"
                "============================\n"
                "Total Receivables:  25,000.00\n"
                "Total Payables:     12,500.00\n"
                "Cash Position:      50,000.00\n"
                "Open Invoices:      3\n"
                "Draft Invoices:     1\n"
                "============================\n"
                "Generated: [DRY RUN MODE]"
            )

        # Total receivables (open customer invoices)
        receivable_invoices = _client.execute_kw(
            "account.move", "search_read",
            [[("move_type", "=", "out_invoice"), ("state", "=", "posted"), ("payment_state", "!=", "paid")]],
            {"fields": ["amount_residual"]},
        )
        total_receivable = sum(inv.get("amount_residual", 0) for inv in receivable_invoices)

        # Total payables (open vendor bills)
        payable_bills = _client.execute_kw(
            "account.move", "search_read",
            [[("move_type", "=", "in_invoice"), ("state", "=", "posted"), ("payment_state", "!=", "paid")]],
            {"fields": ["amount_residual"]},
        )
        total_payable = sum(bill.get("amount_residual", 0) for bill in payable_bills)

        # Cash position (bank/cash journal balances)
        cash_accounts = _client.execute_kw(
            "account.account", "search_read",
            [[("account_type", "in", ["asset_cash"])]],
            {"fields": ["id"]},
        )
        cash_position = 0.0
        if cash_accounts:
            cash_ids = [a["id"] for a in cash_accounts]
            cash_lines = _client.execute_kw(
                "account.move.line", "search_read",
                [[("account_id", "in", cash_ids), ("parent_state", "=", "posted")]],
                {"fields": ["balance"]},
            )
            cash_position = sum(line.get("balance", 0) for line in cash_lines)

        # Counts
        open_count = len(receivable_invoices)
        draft_invoices = _client.execute_kw(
            "account.move", "search_read",
            [[("move_type", "=", "out_invoice"), ("state", "=", "draft")]],
            {"fields": ["id"]},
        )
        draft_count = len(draft_invoices)

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        return (
            f"Accounting Summary\n"
            f"============================\n"
            f"Total Receivables:  {total_receivable:,.2f}\n"
            f"Total Payables:     {total_payable:,.2f}\n"
            f"Cash Position:      {cash_position:,.2f}\n"
            f"Open Invoices:      {open_count}\n"
            f"Draft Invoices:     {draft_count}\n"
            f"============================\n"
            f"Generated: {now}"
        )

    except Exception as e:
        error_tracker.record_error(str(e))
        return f"Error generating accounting summary: {e}"


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Odoo MCP Accounting Server")
    parser.add_argument("--dry-run", action="store_true", help="Return mock data without Odoo calls")
    parser.add_argument("--test", action="store_true", help="Test Odoo connectivity and exit")
    args = parser.parse_args()

    if args.test:
        print(f"Testing connection to {ODOO_URL} (db: {ODOO_DB})...")
        try:
            version_info = _client.version()
            print(f"Odoo version: {version_info}")
            uid = _client.authenticate()
            print(f"Authenticated as uid={uid}")
            print("Connection test: PASSED")
        except Exception as e:
            print(f"Connection test: FAILED — {e}")
            sys.exit(1)
        sys.exit(0)

    if args.dry_run:
        DRY_RUN_MODE = True
        print("Starting in DRY-RUN mode (mock data, no Odoo calls)", file=sys.stderr)

    mcp.run()
