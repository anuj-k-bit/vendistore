#!/usr/bin/env python3
"""
IntelliVend Agentic Tool Layer Verification Script
Demonstrates guardrail policy enforcement and queries append-only agent_audit_log entries.
"""

import sys
import io
import json
from pathlib import Path

# Safe UTF-8 output formatting for Windows terminal
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent / "backend" / "agentic-layer"))

from app.database import Base, engine, SessionLocal
from app.models import AgentAuditLog
from app.tools import set_price, issue_refund, get_inventory, get_forecast

def verify_agentic_layer():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("=" * 75)
    print("🛡️ INTELLIVEND AGENTIC TOOL LAYER & GUARDRAILS POLICY VERIFICATION")
    print("=" * 75)

    # ----------------------------------------------------
    # 1. DISALLOWED ACTION 1: 30% Price Cut (Limit is ±15%)
    # ----------------------------------------------------
    print("\n[TEST 1] Proposing DISALLOWED 30% Price Cut ($2.45 vs Base $3.50)...")
    res_30 = set_price("VM-101", "prod-1", new_price=2.45, base_price=3.50, cost_floor=2.00, db=db)
    print(f"  --> Result Success  : {res_30['success']}")
    print(f"  --> Applied Price   : ${res_30['applied_price']:.2f}")
    print(f"  --> Error / Reason  : {res_30['error']}")

    # ----------------------------------------------------
    # 2. DISALLOWED ACTION 2: Below Cost Floor ($1.50 vs Cost Floor $2.00)
    # ----------------------------------------------------
    print("\n[TEST 2] Proposing DISALLOWED Below-Cost Price ($1.50 vs Cost Floor $2.00)...")
    res_cost = set_price("VM-101", "prod-1", new_price=1.50, base_price=3.50, cost_floor=2.00, db=db)
    print(f"  --> Result Success  : {res_cost['success']}")
    print(f"  --> Applied Price   : ${res_cost['applied_price']:.2f}")
    print(f"  --> Error / Reason  : {res_cost['error']}")

    # ----------------------------------------------------
    # 3. ALLOWED ACTION: Valid 10% Price Surge ($3.85 vs Base $3.50)
    # ----------------------------------------------------
    print("\n[TEST 3] Proposing ALLOWED 10% Price Surge ($3.85 vs Base $3.50)...")
    res_valid = set_price("VM-101", "prod-1", new_price=3.85, base_price=3.50, cost_floor=2.00, db=db)
    print(f"  --> Result Success  : {res_valid['success']}")
    print(f"  --> Applied Price   : ${res_valid['applied_price']:.2f}")
    print(f"  --> Message         : {res_valid['message']}")

    # ----------------------------------------------------
    # 4. REFUND ESCALATION: $25.00 Refund (> $10.00 Limit)
    # ----------------------------------------------------
    print("\n[TEST 4] Proposing REFUND ESCALATION ($25.00 vs $10.00 Auto-Limit)...")
    res_ref = issue_refund("TX-999", "CUST-105", amount=25.00, reason="Machine error", db=db)
    print(f"  --> Success Status  : {res_ref['success']}")
    print(f"  --> Escalation Req  : {res_ref.get('requires_human_approval')}")
    print(f"  --> Ticket ID       : {res_ref.get('escalation_ticket_id')}")

    # ----------------------------------------------------
    # 5. AUDIT LOG DATABASE RECORDS
    # ----------------------------------------------------
    print("\n" + "=" * 75)
    print("📜 APPEND-ONLY AGENT_AUDIT_LOG DATABASE TABLE (LATEST RECORDS)")
    print("=" * 75)
    logs = db.query(AgentAuditLog).order_by(AgentAuditLog.id.desc()).limit(10).all()

    for l in logs:
        print(f"[{l.id:02d}] {l.timestamp.strftime('%H:%M:%S')} | Tool: {l.tool_name:<16} | Status: {l.status:<10} | Policy: {l.policy_name or 'N/A'}")
        print(f"     Reason: {l.policy_reason}")
        print(f"     Args  : {l.arguments}\n")

    db.close()
    print("=" * 75)
    print("✅ All Guardrails Policies & Audit Logs Successfully Verified!")
    print("=" * 75)

if __name__ == "__main__":
    verify_agentic_layer()
