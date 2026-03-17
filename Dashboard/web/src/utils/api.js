const BASE = "/api";

async function get(path) {
  try {
    const res = await fetch(`${BASE}${path}`);
    if (!res.ok) throw new Error(res.statusText);
    return await res.json();
  } catch {
    return null;
  }
}

export const fetchStatus = () => get("/status");
export const fetchTasks = () => get("/tasks");
export const fetchApprovals = () => get("/approvals");
export const fetchBriefing = () => get("/briefing");
export const fetchOdooInvoices = () => get("/odoo/invoices");
export const fetchOdooSummary = () => get("/odoo/summary");
export const fetchAudit = (n = 10) => get(`/audit?n=${n}`);
export const fetchMcp = () => get("/mcp");
