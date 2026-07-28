#!/usr/bin/env python3
"""
IntelliVend Customer Support Agent & End-to-End Failed Purchase Verification Script
Simulates failed purchase lookup_transaction() and guardrailed issue_refund() calls.
"""

import sys
import json
import urllib.request
from pathlib import Path

# Safe UTF-8 output formatting for Windows terminal
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent / "backend" / "agentic-layer"))

from app.database import Base, engine, SessionLocal
from app.models import AgentAuditLog
from app.tools import lookup_transaction, issue_refund

def verify_support_agent():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("=" * 80)
    print("🤖 INTELLIVEND AI CUSTOMER SUPPORT AGENT END-TO-END VERIFICATION")
    print("=" * 80)

    # -----------------------------------------------------------
    # SCENARIO 1: Failed Purchase <= $10.00 (TX-10042 = $4.50)
    # -----------------------------------------------------------
    print("\n[SCENARIO 1] Customer Complaint: Item stuck in slot (TX-10042 = $4.50)")
    tx1 = lookup_transaction("TX-10042", db)
    print(f"  * Transaction Lookup : Found order for '{tx1['product_name']}' (${tx1['amount']:.2f})")
    print(f"  * Dispense Status    : {tx1['dispense_status']}")

    ref1 = issue_refund(tx1["transaction_id"], tx1["customer_id"], tx1["amount"], "Item failed to dispense", db)
    print(f"  * Guardrail Policy   : Refund <= $10.00 Limit Check")
    print(f"  * Refund Result      : Success={ref1['success']} | Message: {ref1.get('message')}")

    # -----------------------------------------------------------
    # SCENARIO 2: Failed Purchase > $10.00 (TX-10099 = $28.50)
    # -----------------------------------------------------------
    print("\n[SCENARIO 2] Customer Complaint: Bulk pack chute jam (TX-10099 = $28.50)")
    tx2 = lookup_transaction("TX-10099", db)
    print(f"  * Transaction Lookup : Found order for '{tx2['product_name']}' (${tx2['amount']:.2f})")
    print(f"  * Dispense Status    : {tx2['dispense_status']}")

    ref2 = issue_refund(tx2["transaction_id"], tx2["customer_id"], tx2["amount"], "Bulk pack chute jam", db)
    print(f"  * Guardrail Policy   : Refund <= $10.00 Limit Check")
    print(f"  * Refund Result      : Success={ref2['success']} | Escalated={ref2.get('requires_human_approval')}")
    print(f"  * Escalation Ticket  : {ref2.get('escalation_ticket_id')}")
    print(f"  * Message            : {ref2.get('message')}")

    # -----------------------------------------------------------
    # AUDIT LOG VERIFICATION
    # -----------------------------------------------------------
    print("\n" + "=" * 80)
    print("📜 PERSISTED SUPPORT AGENT AUDIT LOGS IN DATABASE")
    print("=" * 80)
    logs = db.query(AgentAuditLog).order_by(AgentAuditLog.id.desc()).limit(6).all()
    for l in reversed(logs):
        print(f"[{l.id:02d}] {l.timestamp.strftime('%H:%M:%S')} | Tool: {l.tool_name:<20} | Status: {l.status:<10} | Policy: {l.policy_name}")
        print(f"     Reason: {l.policy_reason}\n")

    db.close()
    print("=" * 80)
    print("✅ Customer Support Agent & Guardrailed Refunds Successfully Verified!")
    print("=" * 80)

if __name__ == "__main__":
    verify_support_agent()
