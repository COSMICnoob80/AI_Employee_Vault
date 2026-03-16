# Odoo Accounting Check

Query Odoo accounting data — invoices, accounts, journal entries, and summaries.

## Triggers
- "list invoices"
- "get invoice"
- "create invoice"
- "chart of accounts"
- "journal entries"
- "accounting summary"
- "odoo check"
- "odoo status"

## Instructions

When the user asks about Odoo accounting data:

1. **List invoices** - Use the `list_invoices` MCP tool to list customer invoices. Optionally filter by `state` (draft, posted, cancel) and set a `limit`.

2. **Get invoice details** - Use `get_invoice` with the Odoo invoice ID to retrieve full details including line items.

3. **Create invoice** - Use `create_invoice` with `dry_run=True` first to preview. Only set `dry_run=False` after user confirmation. Invoice creation writes an approval request to `Pending_Approval/`.

4. **List accounts** - Use `list_accounts` to retrieve the chart of accounts with code, name, and type.

5. **Journal entries** - Use `get_journal_entries` with `date_from` and `date_to` (YYYY-MM-DD) to query entries in a date range.

6. **Accounting summary** - Use `accounting_summary` to generate a financial overview (receivables, payables, cash position, invoice counts). This feeds into the CEO Briefing.

## Notes
- Requires `.env.odoo` at vault root with Odoo credentials
- Test connection first: `python MCP/odoo_server.py --test`
- Dry-run mode (mock data): `python MCP/odoo_server.py --dry-run`
- All operations are audit-logged to `Logs/audit.jsonl`
- Circuit breaker activates after consecutive errors
- See `Skills/odoo_accounting.md` for full documentation
