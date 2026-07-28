"""
IntelliVend Guardrails Policy Layer
Enforces deterministic safety rules on state-changing agent actions.
"""

from typing import Tuple

MAX_PRICE_CHANGE_PCT = 0.15 # Max 15% change allowed
AUTO_REFUND_THRESHOLD = 10.00 # Refunds <= $10.00 auto-approved

def validate_price_change(new_price: float, base_price: float, cost_floor: float) -> Tuple[bool, str, str, str]:
    """
    Validates set_price proposals against cost floor and max 15% price delta rules.
    Returns: (is_allowed: bool, status: str, policy_name: str, policy_reason: str)
    """
    if base_price <= 0:
        return False, "REJECTED", "InvalidBasePricePolicy", "Base price must be greater than $0.00."

    if new_price < cost_floor:
        return (
            False,
            "REJECTED",
            "CostFloorProtectionPolicy",
            f"Proposed price ${new_price:.2f} is below minimum cost floor limit of ${cost_floor:.2f}."
        )

    price_delta_pct = abs(new_price - base_price) / base_price
    if price_delta_pct > MAX_PRICE_CHANGE_PCT:
        pct_display = round(price_delta_pct * 100.0, 1)
        return (
            False,
            "REJECTED",
            "MaxPriceDeltaPolicy",
            f"Proposed price change ({pct_display}%) exceeds maximum allowed guardrail threshold of ±15.0%."
        )

    return True, "ALLOWED", "PriceGuardrailPolicy", f"Price change of {round(price_delta_pct*100, 1)}% passed guardrail validation."

def validate_refund_request(amount: float) -> Tuple[bool, str, str, str]:
    """
    Validates issue_refund proposals against $10.00 auto-approval limits.
    Returns: (is_allowed: bool, status: str, policy_name: str, policy_reason: str)
    """
    if amount <= 0.0:
        return False, "REJECTED", "InvalidAmountPolicy", "Refund amount must be greater than $0.00."

    if amount <= AUTO_REFUND_THRESHOLD:
        return (
            True,
            "ALLOWED",
            "AutoRefundApprovalPolicy",
            f"Refund amount ${amount:.2f} is <= ${AUTO_REFUND_THRESHOLD:.2f} and auto-approved."
        )

    return (
        False,
        "ESCALATED",
        "HumanEscalationPolicy",
        f"Refund amount ${amount:.2f} exceeds auto-approval threshold of ${AUTO_REFUND_THRESHOLD:.2f}; escalated to human manager."
    )
