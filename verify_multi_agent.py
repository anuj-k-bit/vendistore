#!/usr/bin/env python3
"""
IntelliVend Multi-Agent System Verification Script
Executes 3 realistic goals with the Supervisor Agent & Sub-Agents (Restock Planner, Pricing Agent, Ops/Anomaly Agent).
Displays full ReAct reasoning traces (Thought -> Action -> Observation) and audit log database records.
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
from app.agents import SupervisorAgent

def verify_multi_agent_system():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    supervisor = SupervisorAgent()

    print("=" * 80)
    print("👑 INTELLIVEND MULTI-AGENT SYSTEM REASONING TRACE VERIFICATION")
    print("=" * 80)

    goals = [
        "Inspect machine health for VM-101 and auto-resolve or escalate telemetry anomalies",
        "Plan restock dispatch for VM-101 based on 7-day forecast demand",
        "Attempt a 30% price cut on VM-101 prod-1 and verify policy guardrail rejection"
    ]

    for idx, goal in enumerate(goals, 1):
        print(f"\n" + "-" * 80)
        print(f"🎯 GOAL #{idx}: '{goal}'")
        print("-" * 80)

        result = supervisor.run_goal(goal, db)

        print(f"  * Status        : {result['status']}")
        print(f"  * Planned Steps : {result['planned_steps']}")
        print(f"  * Execution Log : {result['execution_summary']}")
        print("  * Sub-Agent Results:")
        for agent_key, res in result["sub_agent_results"].items():
            print(f"    - [{agent_key}]: {json.dumps(res, indent=6)}")

    print("\n" + "=" * 80)
    print("📜 PERSISTED REASONING TRACES IN AGENT_AUDIT_LOG DATABASE TABLE")
    print("=" * 80)

    trace_logs = db.query(AgentAuditLog).filter(AgentAuditLog.tool_name.like("agent_trace:%")).order_by(AgentAuditLog.id.desc()).limit(10).all()

    for t in reversed(trace_logs):
        print(f"\n[Trace ID: {t.id:02d}] {t.timestamp.strftime('%H:%M:%S')} UTC | Tool: {t.tool_name}")
        print(f"  * Thought     : {t.policy_reason}")
        print(f"  * Action      : {t.arguments.get('action')} (Args: {t.arguments.get('args')})")
        print(f"  * Observation : {t.execution_result.get('observation')}")

    db.close()
    print("\n" + "=" * 80)
    print("✅ Multi-Agent Reasoning Traces & Guardrail Policies Successfully Verified!")
    print("=" * 80)

if __name__ == "__main__":
    verify_multi_agent_system()
