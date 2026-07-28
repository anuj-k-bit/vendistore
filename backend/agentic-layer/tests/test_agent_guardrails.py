import pytest
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base
from app.models import AgentAuditLog
from app.guardrails import validate_price_change, validate_refund_request
from app.tools import set_price, issue_refund, get_inventory

# Setup in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_disallowed_30_percent_price_cut_blocked_and_logged(setup_database):
    """
    PROVES that a 30% price cut (disallowed action) is BLOCKED by guardrails and logged in agent_audit_log.
    """
    db = setup_database
    base_price = 3.50
    cost_floor = 2.00
    proposed_price = 2.45 # 30% discount ($2.45 vs $3.50)

    # Execute tool call
    result = set_price("VM-101", "prod-1", proposed_price, base_price, cost_floor, db)

    # 1. Assert action was BLOCKED
    assert result["success"] is False
    assert result["applied_price"] == base_price
    assert "exceeds maximum allowed guardrail threshold of ±15.0%" in result["error"]

    # 2. Assert record was persisted to append-only agent_audit_log table
    audit_entry = db.query(AgentAuditLog).filter(AgentAuditLog.tool_name == "set_price").first()
    assert audit_entry is not None
    assert audit_entry.status == "REJECTED"
    assert audit_entry.policy_name == "MaxPriceDeltaPolicy"
    assert audit_entry.arguments["new_price"] == 2.45
    assert audit_entry.execution_result["success"] is False

def test_price_below_cost_floor_blocked_and_logged(setup_database):
    """Proves selling below cost floor is BLOCKED and logged."""
    db = setup_database
    base_price = 3.50
    cost_floor = 2.00
    proposed_price = 1.50 # Below cost floor $2.00

    result = set_price("VM-101", "prod-1", proposed_price, base_price, cost_floor, db)

    assert result["success"] is False
    assert "below minimum cost floor limit" in result["error"]

    audit_entry = db.query(AgentAuditLog).filter(AgentAuditLog.policy_name == "CostFloorProtectionPolicy").first()
    assert audit_entry is not None
    assert audit_entry.status == "REJECTED"

def test_allowed_10_percent_price_change_executed_and_logged(setup_database):
    """Proves valid 10% price surge is ALLOWED and logged."""
    db = setup_database
    base_price = 3.50
    cost_floor = 2.00
    proposed_price = 3.85 # 10% surge

    result = set_price("VM-101", "prod-1", proposed_price, base_price, cost_floor, db)

    assert result["success"] is True
    assert result["applied_price"] == 3.85

    audit_entry = db.query(AgentAuditLog).filter(AgentAuditLog.status == "EXECUTED").first()
    assert audit_entry is not None
    assert audit_entry.policy_name == "PriceGuardrailPolicy"

def test_refund_auto_approval_vs_human_escalation(setup_database):
    """Proves $5.00 refund is auto-approved, while $25.00 refund is escalated."""
    db = setup_database

    # $5.00 refund -> Auto-approved
    res_auto = issue_refund("TX-001", "CUST-101", 5.00, "Spilled drink", db)
    assert res_auto["success"] is True

    # $25.00 refund -> Escalated
    res_esc = issue_refund("TX-002", "CUST-102", 25.00, "Vending machine error", db)
    assert res_esc["success"] is False
    assert res_esc["requires_human_approval"] is True

    # Verify audit log
    auto_log = db.query(AgentAuditLog).filter(AgentAuditLog.status == "EXECUTED").first()
    assert auto_log.arguments["amount"] == 5.00

    esc_log = db.query(AgentAuditLog).filter(AgentAuditLog.status == "ESCALATED").first()
    assert esc_log.arguments["amount"] == 25.00
    assert esc_log.policy_name == "HumanEscalationPolicy"
