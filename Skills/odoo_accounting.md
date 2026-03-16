# Odoo Accounting Skill

## Description
Odoo Community accounting integration via MCP JSON-RPC. Exposes 6 tools for querying and managing invoices, chart of accounts, journal entries, and financial summaries through the Model Context Protocol. Connects to Odoo Community 19+ using JSON-RPC with authentication caching, retry logic, and circuit breaker error tracking.

## Capabilities
- List customer invoices with optional state filtering and pagination
- Get detailed invoice information including line items
- Create draft invoices with HITL approval workflow and dry-run preview
- List the chart of accounts with code, name, and type
- Query journal entries within a date range
- Generate accounting summaries (receivables, payables, cash position) for CEO Briefing consumption

## Input Format
MCP tool calls with parameters:
```
list_invoices(state: str = "", limit: int = 20)
get_invoice(invoice_id: int)
create_invoice(partner_name: str, lines_json: str, dry_run: bool = True)
list_accounts()
get_journal_entries(date_from: str, date_to: str)
accounting_summary()
```

- `state`: One of `draft`, `posted`, `cancel`, or empty for all
- `lines_json`: JSON array of objects with `product`, `quantity`, `price` keys
- `date_from` / `date_to`: ISO dates in `YYYY-MM-DD` format

## Output Format
All tools return a single string:
- **Success**: Formatted multi-line result with data
- **Dry run**: Prefixed with `[DRY RUN]` or `--- DRY RUN PREVIEW ---`
- **Error**: `Error <action>: <description>`
- **Circuit breaker**: Raises if error threshold exceeded (via `ErrorTracker`)

## Rules
1. `.env.odoo` must exist at vault root with `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD`
2. Always use dry-run first for `create_invoice` — default `dry_run=True`
3. Invoice creation triggers HITL approval: writes approval request to `Pending_Approval/`
4. Circuit breaker via `ErrorTracker` — consecutive errors will block further calls until reset
5. All operations are audit-logged to `Logs/audit.jsonl` via `vault_audit.audit_log()`
6. Retry logic (2 retries) for transient connection errors (`ConnectionError`, `TimeoutError`, `OSError`)
7. Test connectivity before first use: `python MCP/odoo_server.py --test`

## Examples

### Example 1: List Invoices
```
list_invoices(state="posted", limit=10)
-> "Invoices (2 found):
     INV/2026/0001 | Test Customer | 15000.00 | posted | 2026-03-01
     INV/2026/0002 | Sample Corp | 8500.00 | posted | 2026-03-05"
```

### Example 2: Get Invoice Details
```
get_invoice(invoice_id=1)
-> "Invoice: INV/2026/0001
     Partner: Test Customer
     Date: 2026-03-01
     State: posted
     Total: 15000.00
     Lines:
       1. Consulting Service | Qty: 10 | Price: 1500.00 | Subtotal: 15000.00"
```

### Example 3: Create Invoice (Dry Run)
```
create_invoice(partner_name="Test Customer", lines_json='[{"product": "Consulting", "quantity": 5, "price": 2000}]', dry_run=True)
-> "--- DRY RUN PREVIEW ---
   Partner: Test Customer
   Lines:
     1. Consulting | Qty: 5 | Price: 2000.00 | Subtotal: 10000.00
   Total: 10000.00
   --- END PREVIEW (not created) ---"
```

### Example 4: List Chart of Accounts
```
list_accounts()
-> "Chart of Accounts (4 accounts):
     1000 | Cash | asset_cash
     1100 | Accounts Receivable | asset_receivable
     2000 | Accounts Payable | liability_payable
     4000 | Revenue | income"
```

### Example 5: Get Journal Entries
```
get_journal_entries(date_from="2026-03-01", date_to="2026-03-31")
-> "Journal Entries (2 found, 2026-03-01 to 2026-03-31):
     MISC/2026/0001 | 2026-03-01 | Opening Balance | 50000.00 | posted
     MISC/2026/0002 | 2026-03-03 | Office Supplies | 2500.00 | posted"
```

### Example 6: Accounting Summary
```
accounting_summary()
-> "Accounting Summary
   ============================
   Total Receivables:  25,000.00
   Total Payables:     12,500.00
   Cash Position:      50,000.00
   Open Invoices:      3
   Draft Invoices:     1
   ============================
   Generated: 2026-03-13 10:30"
```

## Integration
- MCP Server: `MCP/odoo_server.py` (stdio transport, FastMCP)
- Audit logging: `Watchers/vault_audit.py` (`audit_log`, `safe_write`, `retry`, `ErrorTracker`)
- Approval workflow: [[Company_Handbook]] (invoice creation requires HITL approval)
- CEO Briefing: [[ceo_briefing]] (accounting_summary feeds into weekly reports)
- Cross-domain: [[cross_domain_integration]] (business domain data source)
- System status: [[Dashboard]]
