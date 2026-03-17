"""AEWACS Command Center — Flask API server."""

import json
import os
import re
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

from parsers import parse_frontmatter, read_jsonl_tail, list_md_files
import odoo_proxy

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

VAULT = Path(__file__).resolve().parent.parent.parent


# ── /api/status ──────────────────────────────────────────────

@app.route("/api/status")
def api_status():
    meta, body = parse_frontmatter(VAULT / "Dashboard.md")

    # Parse component table from body
    components = []
    for line in body.splitlines():
        # Match table rows like: | Component Name | Status emoji | Activity |
        m = re.match(
            r"\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", line
        )
        if not m:
            continue
        name, raw_status, activity = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        if name.startswith("--") or name.lower() == "component":
            continue

        # Normalise emoji status
        if "\U0001f7e2" in raw_status or "Active" in raw_status:
            status = "active"
        elif "\U0001f7e1" in raw_status or "Ready" in raw_status:
            status = "ready"
        elif "\U0001f534" in raw_status or "Error" in raw_status:
            status = "error"
        elif "\U0001f535" in raw_status or "Idle" in raw_status or "Pending" in raw_status:
            status = "idle"
        else:
            status = "unknown"

        components.append({
            "name": name,
            "status": status,
            "last_activity": activity,
        })

    return jsonify({
        "status": str(meta.get("status", "unknown")),
        "pending_tasks": meta.get("pending_tasks", 0),
        "last_updated": str(meta.get("last_updated", "")),
        "components": components,
    })


# ── /api/tasks ───────────────────────────────────────────────

@app.route("/api/tasks")
def api_tasks():
    items = list_md_files(VAULT / "Needs_Action")
    tasks = []
    for meta, _body, path in items:
        tasks.append({
            "filename": path.name,
            "type": meta.get("type", "unknown"),
            "source": meta.get("from", meta.get("source", "")),
            "priority": meta.get("priority", "normal"),
            "domain": meta.get("domain", ""),
            "status": meta.get("status", "pending"),
        })
    return jsonify({"tasks": tasks, "count": len(tasks)})


# ── /api/approvals ───────────────────────────────────────────

@app.route("/api/approvals")
def api_approvals():
    items = list_md_files(VAULT / "Pending_Approval")
    approvals = []
    for meta, _body, path in items:
        approvals.append({
            "filename": path.name,
            "action_type": meta.get("action_type", "unknown"),
            "priority": meta.get("priority", "normal"),
            "requested": str(meta.get("requested", "")),
            "domain": meta.get("domain", ""),
        })
    return jsonify({"approvals": approvals, "count": len(approvals)})


# ── /api/briefing ────────────────────────────────────────────

@app.route("/api/briefing")
def api_briefing():
    reports_dir = VAULT / "Reports"
    if not reports_dir.is_dir():
        return jsonify({"week": "", "generated": "", "executive_summary": "", "full_body": ""})

    briefings = sorted(reports_dir.glob("CEO_Briefing_*.md"), reverse=True)
    if not briefings:
        return jsonify({"week": "", "generated": "", "executive_summary": "", "full_body": ""})

    meta, body = parse_frontmatter(briefings[0])

    # Extract executive summary section
    exec_summary = ""
    in_summary = False
    for line in body.splitlines():
        if "executive summary" in line.lower():
            in_summary = True
            continue
        if in_summary and line.startswith("## "):
            break
        if in_summary:
            exec_summary += line + "\n"

    return jsonify({
        "week": meta.get("week", ""),
        "generated": str(meta.get("generated", "")),
        "executive_summary": exec_summary.strip(),
        "full_body": body,
    })


# ── /api/odoo/invoices ───────────────────────────────────────

@app.route("/api/odoo/invoices")
def api_odoo_invoices():
    state = request.args.get("state")
    limit = request.args.get("limit", 20, type=int)
    return jsonify(odoo_proxy.get_invoices(state=state, limit=limit))


# ── /api/odoo/summary ────────────────────────────────────────

@app.route("/api/odoo/summary")
def api_odoo_summary():
    return jsonify(odoo_proxy.get_summary())


# ── /api/audit ───────────────────────────────────────────────

@app.route("/api/audit")
def api_audit():
    n = request.args.get("n", 10, type=int)
    entries = read_jsonl_tail(VAULT / "Logs" / "audit.jsonl", n)
    return jsonify({"entries": entries, "count": len(entries)})


# ── /api/mcp ─────────────────────────────────────────────────

@app.route("/api/mcp")
def api_mcp():
    mcp_path = VAULT / ".claude" / "mcp.json"
    try:
        mcp_data = json.loads(mcp_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return jsonify({"servers": [], "count": 0})

    servers_cfg = mcp_data.get("mcpServers", {})
    servers = []
    for name, cfg in servers_cfg.items():
        script = cfg.get("args", [""])[-1] if cfg.get("args") else ""
        tool_count = _count_tools(script)
        servers.append({
            "name": name,
            "script": script,
            "tool_count": tool_count,
        })

    return jsonify({"servers": servers, "count": len(servers)})


def _count_tools(script_path):
    """Count @mcp.tool() decorators in a server file."""
    try:
        text = Path(script_path).read_text(encoding="utf-8")
        return len(re.findall(r"@mcp\.tool\(\)", text))
    except (OSError, UnicodeDecodeError):
        return 0


# ── Main ─────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("DASHBOARD_API_PORT", 5001))
    app.run(host="127.0.0.1", port=port, debug=False)
