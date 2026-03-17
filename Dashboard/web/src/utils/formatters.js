export function formatCurrency(value, currency = "PKR") {
  if (value == null) return "—";
  return `${currency} ${Number(value).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

export function formatRelativeTime(isoString) {
  if (!isoString) return "—";
  const date = new Date(isoString);
  if (isNaN(date)) return isoString;
  const diff = Date.now() - date.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function statusColor(status) {
  const map = {
    active: "var(--success)",
    ok: "var(--success)",
    ready: "var(--warning)",
    idle: "var(--accent)",
    error: "var(--alert)",
    retry: "var(--warning)",
    pending: "var(--warning)",
    unknown: "var(--text-dim)",
  };
  return map[status] || "var(--text-dim)";
}

export function priorityClass(priority) {
  const map = { urgent: "priority-urgent", high: "priority-high", normal: "priority-normal", low: "priority-low" };
  return map[priority] || "priority-normal";
}
