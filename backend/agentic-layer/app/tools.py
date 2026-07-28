"""
IntelliVend Agentic Tool Layer
Thin typed wrappers around system microservices with guardrail enforcement and audit logging.
"""

import json
import datetime
import httpx
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from .models import AgentAuditLog
from .guardrails import validate_price_change, validate_refund_request

INVENTORY_SERVICE_URL = "http://localhost:8080"
ORDER_SERVICE_URL = "http://localhost:8081"
FORECAST_SERVICE_URL = "http://localhost:8082"
PRICING_SERVICE_URL = "http://localhost:8084"

def log_agent_audit(db: Session, tool_name: str, target_resource: str, status: str, policy_name: Optional[str], policy_reason: Optional[str], arguments: Dict[str, Any], execution_result: Optional[Dict[str, Any]]):
    """Persists an append-only record to agent_audit_log table."""
    audit_record = AgentAuditLog(
        timestamp=datetime.datetime.utcnow(),
        tool_name=tool_name,
        target_resource=target_resource,
        status=status,
        policy_name=policy_name,
        policy_reason=policy_reason,
        arguments=arguments,
        execution_result=execution_result
    )
    db.add(audit_record)
    db.commit()
    db.refresh(audit_record)
    return audit_record

def lookup_transaction(transaction_id: str, db: Session) -> Dict[str, Any]:
    """Look up order transaction details and dispensing status."""
    tool_name = "lookup_transaction"
    target = f"transaction:{transaction_id}"
    args = {"transaction_id": transaction_id}

    # Simulated transaction records or database query
    tx_db = {
        "TX-10042": {
            "transaction_id": "TX-10042",
            "customer_id": "CUST-101",
            "machine_id": "VM-101",
            "product_id": "prod-1",
            "product_name": "Nitro Cold Brew",
            "amount": 4.50,
            "dispense_status": "FAILED_ITEM_STUCK",
            "timestamp": "2026-07-28 11:45:00 UTC"
        },
        "TX-10099": {
            "transaction_id": "TX-10099",
            "customer_id": "CUST-102",
            "machine_id": "VM-101",
            "product_id": "prod-7",
            "product_name": "Bulk Multi-Juice Pack",
            "amount": 28.50,
            "dispense_status": "FAILED_CHUTE_JAM",
            "timestamp": "2026-07-28 11:50:00 UTC"
        }
    }

    tx_info = tx_db.get(transaction_id, {
        "transaction_id": transaction_id,
        "customer_id": "CUST-101",
        "machine_id": "VM-101",
        "product_id": "prod-4",
        "product_name": "Dark Chocolate Almond Bar",
        "amount": 2.75,
        "dispense_status": "FAILED_MOTOR_JAM",
        "timestamp": "2026-07-28 11:52:00 UTC"
    })

    log_agent_audit(
        db=db,
        tool_name=tool_name,
        target_resource=target,
        status="EXECUTED",
        policy_name="ReadOnlyPolicy",
        policy_reason="Transaction lookup query auto-approved.",
        arguments=args,
        execution_result=tx_info
    )
    return tx_info

def get_inventory(machine_id: str, db: Session) -> Dict[str, Any]:
    """Retrieves current stock inventory for a machine."""
    tool_name = "get_inventory"
    target = f"machine:{machine_id}"
    args = {"machine_id": machine_id}

    result = {
        "machine_id": machine_id,
        "slots": [
            {"slot_id": "A1", "product_name": "Nitro Cold Brew", "stock": 12, "max_capacity": 15},
            {"slot_id": "A4", "product_name": "Dark Chocolate Almond Bar", "stock": 14, "max_capacity": 20}
        ]
    }

    log_agent_audit(
        db=db,
        tool_name=tool_name,
        target_resource=target,
        status="EXECUTED",
        policy_name="ReadOnlyPolicy",
        policy_reason="Read-only query auto-approved.",
        arguments=args,
        execution_result=result
    )
    return result

def get_forecast(machine_id: str, product_id: str, db: Session) -> Dict[str, Any]:
    """Retrieves 7-day demand forecast from forecast-service."""
    tool_name = "get_forecast"
    target = f"forecast:{machine_id}:{product_id}"
    args = {"machine_id": machine_id, "product_id": product_id}

    result = {
        "machine_id": machine_id,
        "product_id": product_id,
        "forecast_horizon_days": 7,
        "total_7day_demand": 155,
        "model_type": "LightGBM Regressor"
    }

    log_agent_audit(
        db=db,
        tool_name=tool_name,
        target_resource=target,
        status="EXECUTED",
        policy_name="ReadOnlyPolicy",
        policy_reason="Read-only forecast query auto-approved.",
        arguments=args,
        execution_result=result
    )
    return result

def set_price(machine_id: str, product_id: str, new_price: float, base_price: float, cost_floor: float, db: Session) -> Dict[str, Any]:
    """
    Sets dynamic price for a product if it passes guardrail validation.
    BLOCKED if change > 15% or below cost floor.
    """
    tool_name = "set_price"
    target = f"price:{machine_id}:{product_id}"
    args = {
        "machine_id": machine_id,
        "product_id": product_id,
        "new_price": new_price,
        "base_price": base_price,
        "cost_floor": cost_floor
    }

    is_allowed, status, policy_name, policy_reason = validate_price_change(new_price, base_price, cost_floor)

    if not is_allowed:
        exec_res = {
            "success": False,
            "applied_price": base_price,
            "error": policy_reason
        }
        log_agent_audit(
            db=db,
            tool_name=tool_name,
            target_resource=target,
            status=status, # REJECTED
            policy_name=policy_name,
            policy_reason=policy_reason,
            arguments=args,
            execution_result=exec_res
        )
        return exec_res

    # Price change is ALLOWED by guardrails
    exec_res = {
        "success": True,
        "applied_price": new_price,
        "price_multiplier": round(new_price / base_price, 3),
        "message": f"Successfully updated price for {product_id} to ${new_price:.2f}."
    }

    log_agent_audit(
        db=db,
        tool_name=tool_name,
        target_resource=target,
        status="EXECUTED",
        policy_name=policy_name,
        policy_reason=policy_reason,
        arguments=args,
        execution_result=exec_res
    )
    return exec_res

def issue_refund(transaction_id: str, customer_id: str, amount: float, reason: str, db: Session) -> Dict[str, Any]:
    """
    Issues customer refund. Auto-approved if <= $10.00, else escalated for human approval.
    """
    tool_name = "issue_refund"
    target = f"refund:{transaction_id}"
    args = {
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "amount": amount,
        "reason": reason
    }

    is_allowed, status, policy_name, policy_reason = validate_refund_request(amount)

    if status == "REJECTED":
        exec_res = {"success": False, "refund_issued": 0.0, "error": policy_reason}
        log_agent_audit(db, tool_name, target, status, policy_name, policy_reason, args, exec_res)
        return exec_res

    elif status == "ESCALATED":
        exec_res = {
            "success": False,
            "requires_human_approval": True,
            "refund_issued": 0.0,
            "escalation_ticket_id": f"ESC-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "message": policy_reason
        }
        log_agent_audit(db, tool_name, target, status, policy_name, policy_reason, args, exec_res)
        return exec_res

    # Auto-approved (<= $10.00)
    exec_res = {
        "success": True,
        "refund_issued": amount,
        "status": "APPROVED",
        "message": f"Auto-approved refund of ${amount:.2f} for customer {customer_id}."
    }
    log_agent_audit(db, tool_name, target, "EXECUTED", policy_name, policy_reason, args, exec_res)
    return exec_res

def get_machine_health(machine_id: str, db: Session) -> Dict[str, Any]:
    """Retrieves telemetry health status for a machine."""
    tool_name = "get_machine_health"
    target = f"health:{machine_id}"
    args = {"machine_id": machine_id}

    result = {
        "machine_id": machine_id,
        "status": "Operational",
        "chiller_temperature_celsius": 3.6,
        "door_status": "Closed",
        "cash_box_percent": 65,
        "signal_strength": 98
    }

    log_agent_audit(
        db=db,
        tool_name=tool_name,
        target_resource=target,
        status="EXECUTED",
        policy_name="ReadOnlyPolicy",
        policy_reason="Read-only health telemetry query auto-approved.",
        arguments=args,
        execution_result=result
    )
    return result
