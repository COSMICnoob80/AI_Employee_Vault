import { formatCurrency } from "../utils/formatters";

export default function OdooPanel({ summary }) {
  if (!summary) return null;

  return (
    <div className="hud-card">
      <h2 className="card-title">
        ODOO FINANCIALS
        {summary.dry_run && <span className="badge badge-warning">DRY RUN</span>}
      </h2>
      <div className="odoo-grid">
        <div className="odoo-stat">
          <span className="odoo-label">Receivables</span>
          <span className="odoo-value">{formatCurrency(summary.receivables)}</span>
        </div>
        <div className="odoo-stat">
          <span className="odoo-label">Payables</span>
          <span className="odoo-value">{formatCurrency(summary.payables)}</span>
        </div>
        <div className="odoo-stat">
          <span className="odoo-label">Cash Position</span>
          <span className="odoo-value odoo-highlight">{formatCurrency(summary.cash_position)}</span>
        </div>
        <div className="odoo-stat">
          <span className="odoo-label">Open Invoices</span>
          <span className="odoo-value">{summary.open_invoices}</span>
        </div>
      </div>
    </div>
  );
}
