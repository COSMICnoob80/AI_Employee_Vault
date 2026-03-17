"""Odoo JSON-RPC proxy with graceful dry-run fallback."""

import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load Odoo credentials
_env_path = Path(__file__).resolve().parent.parent.parent / ".env.odoo"
load_dotenv(_env_path)

ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "")
ODOO_USER = os.getenv("ODOO_USER", "")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")

# ---------- Mock data (from MCP/odoo_server.py) ----------

_MOCK_INVOICES = [
    {"id": 1, "name": "INV/2026/0001", "partner_id": [1, "Test Customer"],
     "amount_total": 15000.0, "state": "posted", "invoice_date": "2026-03-01"},
    {"id": 2, "name": "INV/2026/0002", "partner_id": [2, "Sample Corp"],
     "amount_total": 8500.0, "state": "draft", "invoice_date": "2026-03-05"},
]

_MOCK_SUMMARY = {
    "receivables": 15000.0,
    "payables": 2500.0,
    "cash_position": 50000.0,
    "open_invoices": 2,
}


# ---------- Odoo client ----------

class OdooClient:
    """Lightweight Odoo JSON-RPC client."""

    def __init__(self):
        self.url = ODOO_URL
        self.db = ODOO_DB
        self.user = ODOO_USER
        self.password = ODOO_PASSWORD
        self.uid = None
        self._request_id = 0

    def _jsonrpc(self, service, method, args):
        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": "call",
            "params": {"service": service, "method": method, "args": args},
        }
        resp = requests.post(
            f"{self.url}/jsonrpc",
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("error"):
            raise RuntimeError(result["error"].get("message", "Odoo RPC error"))
        return result.get("result")

    def authenticate(self):
        if self.uid:
            return self.uid
        self.uid = self._jsonrpc("common", "login", [self.db, self.user, self.password])
        return self.uid

    def execute_kw(self, model, method, args, kwargs=None):
        self.authenticate()
        return self._jsonrpc(
            "object", "execute_kw",
            [self.db, self.uid, self.password, model, method, args, kwargs or {}],
        )


# ---------- Public helpers ----------

def get_invoices(state=None, limit=20):
    """Fetch invoices from Odoo. Falls back to mock data on failure."""
    try:
        client = OdooClient()
        domain = []
        if state:
            domain.append(["state", "=", state])
        invoices = client.execute_kw(
            "account.move", "search_read",
            [domain],
            {"fields": ["name", "partner_id", "amount_total", "state", "invoice_date"],
             "limit": limit},
        )
        return {"invoices": invoices, "dry_run": False}
    except Exception:
        return {"invoices": _MOCK_INVOICES, "dry_run": True}


def get_summary():
    """Fetch financial summary from Odoo. Falls back to mock data on failure."""
    try:
        client = OdooClient()
        # Attempt a simple read to verify connectivity
        client.authenticate()
        invoices = client.execute_kw(
            "account.move", "search_read",
            [[["move_type", "=", "out_invoice"], ["state", "=", "posted"]]],
            {"fields": ["amount_total", "amount_residual"], "limit": 100},
        )
        receivables = sum(inv.get("amount_residual", 0) for inv in invoices)
        total = sum(inv.get("amount_total", 0) for inv in invoices)
        return {
            "receivables": receivables,
            "payables": 0,
            "cash_position": total - receivables,
            "open_invoices": len(invoices),
            "dry_run": False,
        }
    except Exception:
        return {**_MOCK_SUMMARY, "dry_run": True}
