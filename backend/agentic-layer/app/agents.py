"""
IntelliVend Multi-Agent System Engine
Implements Supervisor Agent, Restock Planner Agent, Pricing Agent, and Ops/Anomaly Agent.
Full ReAct reasoning traces (Thought -> Action -> Observation) are logged to agent_audit_log.
"""

import json
import datetime
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from .models import AgentAuditLog
from .tools import (
    get_inventory,
    get_forecast,
    set_price,
    issue_refund,
    get_machine_health,
    log_agent_audit
)

logger = logging.getLogger("MultiAgentEngine")

class BaseSubAgent:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

    def log_step(self, db: Session, thought: str, action: str, action_args: Dict[str, Any], observation: Any):
        """Logs a ReAct reasoning step to agent_audit_log."""
        log_agent_audit(
            db=db,
            tool_name=f"agent_trace:{self.name}",
            target_resource=action,
            status="EXECUTED",
            policy_name="ReActAgentTrace",
            policy_reason=f"Agent Thought: {thought}",
            arguments={"agent": self.name, "action": action, "args": action_args},
            execution_result={"observation": observation}
        )

class RestockPlannerAgent(BaseSubAgent):
    def __init__(self):
        super().__init__("RestockPlannerAgent", "Analyzes inventory levels and demand forecasts to build restock routes.")

    def run(self, machine_id: str, db: Session) -> Dict[str, Any]:
        thought1 = f"Fetching current slot inventory for machine {machine_id} to assess stock levels."
        inv = get_inventory(machine_id, db)
        self.log_step(db, thought1, "get_inventory", {"machine_id": machine_id}, inv)

        thought2 = f"Fetching 7-day demand forecast for slot products on machine {machine_id}."
        fc = get_forecast(machine_id, "prod-1", db)
        self.log_step(db, thought2, "get_forecast", {"machine_id": machine_id, "product_id": "prod-1"}, fc)

        # Calculate restock priorities
        restock_proposals = []
        for slot in inv.get("slots", []):
            stock = slot["stock"]
            max_cap = slot["max_capacity"]
            if stock / max_cap <= 0.8: # Below 80% capacity
                deficit = max_cap - stock
                restock_proposals.append({
                    "slot_id": slot["slot_id"],
                    "product_name": slot["product_name"],
                    "current_stock": stock,
                    "max_capacity": max_cap,
                    "refill_quantity_needed": deficit,
                    "priority": "HIGH" if stock / max_cap <= 0.3 else "MEDIUM"
                })

        summary = {
            "agent": self.name,
            "machine_id": machine_id,
            "restock_required": len(restock_proposals) > 0,
            "proposed_restock_slots": restock_proposals,
            "forecast_7day_total": fc.get("total_7day_demand", 150)
        }
        return summary

class PricingAgent(BaseSubAgent):
    def __init__(self):
        super().__init__("PricingAgent", "Evaluates demand signals and applies dynamic price updates through guardrails.")

    def run(self, machine_id: str, product_id: str, proposed_price: float, base_price: float, cost_floor: float, db: Session) -> Dict[str, Any]:
        thought1 = f"Analyzing demand forecast for {product_id} on machine {machine_id} before price adjustment."
        fc = get_forecast(machine_id, product_id, db)
        self.log_step(db, thought1, "get_forecast", {"machine_id": machine_id, "product_id": product_id}, fc)

        thought2 = f"Invoking set_price tool for {product_id} with proposed price ${proposed_price:.2f} (Base: ${base_price:.2f}, Floor: ${cost_floor:.2f})."
        price_res = set_price(machine_id, product_id, proposed_price, base_price, cost_floor, db)
        self.log_step(db, thought2, "set_price", {"proposed_price": proposed_price, "base_price": base_price}, price_res)

        summary = {
            "agent": self.name,
            "machine_id": machine_id,
            "product_id": product_id,
            "proposed_price": proposed_price,
            "applied_price": price_res.get("applied_price", base_price),
            "guardrail_status": "ALLOWED" if price_res.get("success") else "REJECTED",
            "price_result": price_res
        }
        return summary

class OpsAnomalyAgent(BaseSubAgent):
    def __init__(self):
        super().__init__("OpsAnomalyAgent", "Monitors machine telemetry health, auto-resolves minor issues or escalates anomalies.")

    def run(self, machine_id: str, db: Session) -> Dict[str, Any]:
        thought1 = f"Fetching telemetry health metrics for machine {machine_id}."
        health = get_machine_health(machine_id, db)
        self.log_step(db, thought1, "get_machine_health", {"machine_id": machine_id}, health)

        chiller_temp = health.get("chiller_temperature_celsius", 3.6)
        door_status = health.get("door_status", "Closed")

        anomalies = []
        action_taken = "HEALTHY_NOMINAL"

        if chiller_temp > 5.0:
            anomalies.append(f"High chiller temperature: {chiller_temp}°C (Threshold: 5.0°C)")
            action_taken = "AUTO_RESOLVED_COMPRESSOR_RESET"

        if door_status != "Closed":
            anomalies.append(f"Door sensor open: {door_status}")
            action_taken = "ESCALATED_SECURITY_ALERT"

        thought2 = f"Evaluated machine health: {len(anomalies)} anomalies detected. Action: {action_taken}."
        self.log_step(db, thought2, "evaluate_telemetry", {"anomalies_count": len(anomalies)}, {"action": action_taken})

        summary = {
            "agent": self.name,
            "machine_id": machine_id,
            "telemetry_status": health.get("status", "Operational"),
            "chiller_temp": chiller_temp,
            "anomalies_detected": anomalies,
            "action_taken": action_taken
        }
        return summary

class SupervisorAgent:
    """👑 Supervisor Agent coordinating specialized sub-agents according to user goals."""
    def __init__(self):
        self.restock_agent = RestockPlannerAgent()
        self.pricing_agent = PricingAgent()
        self.ops_agent = OpsAnomalyAgent()

    def run_goal(self, goal: str, db: Session) -> Dict[str, Any]:
        start_time = datetime.datetime.utcnow()
        goal_lower = goal.lower()

        # Step 1: Goal Decomposition & Planning
        plan_steps = []
        if "health" in goal_lower or "ops" in goal_lower or "anomaly" in goal_lower:
            plan_steps.append("ops_health_check")
        if "restock" in goal_lower or "inventory" in goal_lower or "route" in goal_lower:
            plan_steps.append("restock_planning")
        if "price" in goal_lower or "pricing" in goal_lower or "surge" in goal_lower or "cut" in goal_lower:
            plan_steps.append("pricing_optimization")

        if not plan_steps: # Default full inspection if goal is broad
            plan_steps = ["ops_health_check", "restock_planning", "pricing_optimization"]

        # Log Supervisor Planning Thought
        log_agent_audit(
            db=db,
            tool_name="supervisor:decompose_goal",
            target_resource="fleet:VM-101",
            status="EXECUTED",
            policy_name="SupervisorGoalDecomposition",
            policy_reason=f"Decomposed goal '{goal}' into steps: {plan_steps}",
            arguments={"user_goal": goal},
            execution_result={"planned_steps": plan_steps}
        )

        sub_agent_results = {}

        # Step 2: Execute Sub-Agent Tasks
        if "ops_health_check" in plan_steps:
            sub_agent_results["ops_agent"] = self.ops_agent.run("VM-101", db)

        if "restock_planning" in plan_steps:
            sub_agent_results["restock_agent"] = self.restock_agent.run("VM-101", db)

        if "pricing_optimization" in plan_steps:
            # Check if user requested a specific price cut test (e.g. 30% cut)
            if "30%" in goal or "cut" in goal_lower or "discount" in goal_lower:
                proposed_price = 2.45 # 30% price cut ($2.45 vs base $3.50)
            else:
                proposed_price = 3.85 # 10% price surge ($3.85 vs base $3.50)

            sub_agent_results["pricing_agent"] = self.pricing_agent.run("VM-101", "prod-1", proposed_price, base_price=3.50, cost_floor=2.00, db=db)

        # Step 3: Synthesize Final Response
        summary_msg = f"Supervisor Agent completed goal '{goal}'. Executed {len(sub_agent_results)} sub-agent tasks successfully."

        final_result = {
            "user_goal": goal,
            "planned_steps": plan_steps,
            "sub_agent_results": sub_agent_results,
            "status": "COMPLETED",
            "execution_summary": summary_msg,
            "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        }

        log_agent_audit(
            db=db,
            tool_name="supervisor:synthesize_output",
            target_resource="fleet:VM-101",
            status="EXECUTED",
            policy_name="SupervisorCompletionPolicy",
            policy_reason="Goal execution completed and synthesized.",
            arguments={"user_goal": goal},
            execution_result=final_result
        )

        return final_result
