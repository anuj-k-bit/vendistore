import os
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from .database import engine, Base, get_audit_db
from .models import AgentAuditLog
from .tools import (
    get_inventory,
    get_forecast,
    set_price,
    issue_refund,
    get_machine_health,
    lookup_transaction
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgenticLayer")

# Create database tables on startup
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initialized Agentic Tool Layer with Guardrails & Audit Logging.")
    yield

app = FastAPI(
    title="IntelliVend Agentic Tool Layer & Guardrails API",
    version="1.0.0",
    description="Tool execution layer for AI agents with deterministic policy guardrails and append-only audit logging",
    lifespan=lifespan
)

from .agents import SupervisorAgent

supervisor_agent = SupervisorAgent()

class AgentRunRequest(BaseModel):
    goal: str = "Inspect health for VM-101 and optimize product pricing within guardrails"

class SupportChatRequest(BaseModel):
    transaction_id: str
    message: str = "My item failed to dispense"

class SetPriceRequest(BaseModel):
    machine_id: str = "VM-101"
    product_id: str = "prod-1"
    new_price: float
    base_price: float = 3.50
    cost_floor: float = 2.00

class RefundRequest(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    reason: str = "Item failed to dispense"

class AuditLogItemResponse(BaseModel):
    id: int
    timestamp: str
    tool_name: str
    target_resource: str
    status: str
    policy_name: Optional[str] = None
    policy_reason: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    execution_result: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

@app.get("/")
def read_root():
    return {
        "service": "IntelliVend Agentic Tool Layer",
        "status": "HEALTHY",
        "guardrail_rules": {
            "max_price_change_percent": 15.0,
            "cost_floor_protection": "Enabled",
            "auto_refund_limit": "$10.00"
        },
        "endpoints": {
            "set_price": "POST /agent/tools/set-price",
            "issue_refund": "POST /agent/tools/issue-refund",
            "get_inventory": "GET /agent/tools/inventory/{machine_id}",
            "get_forecast": "GET /agent/tools/forecast/{machine_id}/{product_id}",
            "get_health": "GET /agent/tools/health/{machine_id}",
            "audit_log": "GET /agent/audit-log"
        }
    }

@app.post("/agent/support-chat")
def api_support_chat(req: SupportChatRequest, db: Session = Depends(get_audit_db)):
    """
    Handles customer support complaints by looking up transaction details and invoking guardrailed issue_refund().
    Returns step-by-step agent reasoning trace and refund/escalation status.
    """
    # 1. Action: lookup_transaction
    tx_info = lookup_transaction(req.transaction_id, db)
    cust_id = tx_info.get("customer_id", "CUST-101")
    amount = float(tx_info.get("amount", 4.50))
    dispense_status = tx_info.get("dispense_status", "FAILED_DISPENSE")
    product_name = tx_info.get("product_name", "Vending Product")

    # 2. Action: issue_refund (subject to guardrails <= $10.00 auto-approved, > $10.00 escalated)
    refund_res = issue_refund(
        transaction_id=req.transaction_id,
        customer_id=cust_id,
        amount=amount,
        reason=f"Customer Complaint ({req.message}): {dispense_status}",
        db=db
    )

    reasoning_steps = [
        f"Step 1 [lookup_transaction]: Found order '{req.transaction_id}' for {product_name} (${amount:.2f}). Dispense Status: {dispense_status}.",
        f"Step 2 [guardrails_check]: Validating refund request of ${amount:.2f} against $10.00 auto-approval threshold.",
        f"Step 3 [issue_refund]: {refund_res.get('message', refund_res.get('error', 'Refund processed.'))}"
    ]

    return {
        "transaction_id": req.transaction_id,
        "customer_id": cust_id,
        "product_name": product_name,
        "amount": amount,
        "dispense_status": dispense_status,
        "status": "APPROVED" if refund_res.get("success") else "ESCALATED",
        "agent_reasoning": reasoning_steps,
        "refund_details": refund_res
    }

@app.post("/agent/run")
def api_run_agent_goal(req: AgentRunRequest, db: Session = Depends(get_audit_db)):
    """
    Accepts a high-level goal, decomposes it via Supervisor Agent, delegates to sub-agents,
    and logs complete reasoning traces to agent_audit_log.
    """
    return supervisor_agent.run_goal(req.goal, db)

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "service": "agentic-tool-layer"}

@app.get("/agent/tools/inventory/{machine_id}")
def api_get_inventory(machine_id: str, db: Session = Depends(get_audit_db)):
    return get_inventory(machine_id, db)

@app.get("/agent/tools/forecast/{machine_id}/{product_id}")
def api_get_forecast(machine_id: str, product_id: str, db: Session = Depends(get_audit_db)):
    return get_forecast(machine_id, product_id, db)

@app.post("/agent/tools/set-price")
def api_set_price(req: SetPriceRequest, db: Session = Depends(get_audit_db)):
    res = set_price(req.machine_id, req.product_id, req.new_price, req.base_price, req.cost_floor, db)
    if not res.get("success", False):
        raise HTTPException(status_code=422, detail=res.get("error", "Price change blocked by guardrails."))
    return res

@app.post("/agent/tools/issue-refund")
def api_issue_refund(req: RefundRequest, db: Session = Depends(get_audit_db)):
    res = issue_refund(req.transaction_id, req.customer_id, req.amount, req.reason, db)
    if res.get("requires_human_approval", False):
        return {"status": "ESCALATED", "result": res}
    if not res.get("success", False):
        raise HTTPException(status_code=422, detail=res.get("error", "Refund request rejected."))
    return res

@app.get("/agent/tools/health/{machine_id}")
def api_get_machine_health(machine_id: str, db: Session = Depends(get_audit_db)):
    return get_machine_health(machine_id, db)

@app.get("/agent/audit-log")
def get_audit_logs(limit: int = 50, db: Session = Depends(get_audit_db)):
    """Returns persistent append-only records from agent_audit_log table."""
    logs = db.query(AgentAuditLog).order_by(AgentAuditLog.id.desc()).limit(limit).all()
    out = []
    for l in logs:
        out.append({
            "id": l.id,
            "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "tool_name": l.tool_name,
            "target_resource": l.target_resource,
            "status": l.status,
            "policy_name": l.policy_name,
            "policy_reason": l.policy_reason,
            "arguments": l.arguments,
            "execution_result": l.execution_result
        })
    return {"total_records": len(out), "audit_logs": out}
