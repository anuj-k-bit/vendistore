# IntelliVend Enterprise System Architectural & MLOps Design Decisions

This document outlines the core architectural principles, ML engineering trade-offs, security patterns, and infrastructure design choices governing **IntelliVend**.

---

## 💳 1. Payment Processing Architecture: Stripe Test-Mode & Signed Webhooks

### Design Decision
Order transactions are decoupled from payment authorization using a **Two-Phase Async Webhook Verification Pattern**.

### Rationale & Trade-offs
- **Traditional Anti-Pattern**: Client creates an order $\rightarrow$ Server charges card $\rightarrow$ Server returns response. If the network drops during database write, the customer is charged without receiving inventory stock.
- **IntelliVend Pattern**:
  1. Frontend Kiosk requests a Stripe `PaymentIntent` via `POST /create-payment-intent`.
  2. Customer completes checkout via Stripe Elements/Test Card (`4242 4242 4242 4242`).
  3. Stripe asynchronously fires an HTTP POST webhook (`POST /webhook/stripe`) signed with a HMAC SHA-256 header (`stripe-signature`).
  4. `order-service` verifies the signature using `STRIPE_WEBHOOK_SECRET`. **ONLY upon receiving `payment_intent.succeeded` does PostgreSQL record the transaction and decrement stock inventory**.
- **Declined Card Handling**: Declined cards (e.g. `4000 0000 0000 0002`) fail client-side before webhook emission, preventing invalid database locks or inventory holds.

---

## 🤖 2. MLOps: Model Drift Detection & SHAP Feature Explainability

### Rolling MAE Drift Engine
- **Mechanism**: Every prediction is logged alongside ground-truth sales. Rolling Mean Absolute Error (MAE) is computed continuously over a 30-day sliding window.
- **Drift Threshold**: If rolling MAE exceeds $3.50$ units, the model status switches to `DRIFT_DETECTED`, surfacing a prominent alert in the Admin Operations Dashboard.
- **Retrain Stub Endpoint**: Exposes `POST /forecast/retrain` to trigger automated retraining pipelines (e.g., via Airflow or Kubeflow) and reset drift metrics.

### SHAP (SHapley Additive exPlanations) Feature Attributions
- **Mechanism**: Every forecast prediction exposes top feature contributions via `GET /forecast/{machine_id}/{product_id}/explain`.
- **Operator Transparency**: Instead of black-box numbers, operators see human-readable attributions:
  - *Day of Week (Friday)*: $+4.2$ units (Peak weekend demand)
  - *Sales Lag 1 (24-Hour Velocity)*: $+2.85$ units
  - *Price Multiplier (1.10x)*: $-0.85$ units (Elasticity effect)

---

## 🗺️ 3. Fleet GIS & Restock Route Visualization: Leaflet OpenStreetMap

### GIS Node Mapping & Dynamic Polyline Overlay
- **Mechanism**: Each simulated machine node (`VM-101`..`VM-110`) is assigned real-world San Francisco Bay Area latitude/longitude coordinates.
- **Priority Route Polyline**: Overlays the Restock Planner agent's proposed route as an ordered polyline path connecting critical nodes (`VM-104` $\rightarrow$ `VM-107` $\rightarrow$ `VM-101` $\rightarrow$ `VM-106`).
- **Color-Coded Status Pins**:
  - 🔴 **Critical**: Stock $\le 20\%$
  - 🟡 **Low Stock**: Stock $20\% - 50\%$
  - 🟢 **Nominal**: Stock $> 50\%$

---

## 🛡️ 4. Policy-Guarded Agentic Layer & ReAct Loops

### Deterministic Safety Enforcement vs. LLM Hallucination Risk
- **Design Rule**: State-changing agent tool calls (`set_price`, `issue_refund`) **must pass hardcoded Python guardrails** in `guardrails.py` before execution.
- **Guardrail Constraints**:
  - `set_price`: Price change must be $\le 15.0\%$ of base price, and $\ge \text{cost\_floor}$.
  - `issue_refund`: Refunds $\le \$10.00$ auto-approved; refunds $> \$10.00$ escalated to human manager with ticket tracking (`HumanEscalationPolicy`).
  - Restock Routes: Maximum 15 stops per dispatch route (`MaxRouteStopsPolicy`).
- **Append-Only Audit Log**: Every tool attempt (Pass, Reject, Escalate) is written to `agent_audit_log` for regulatory compliance and auditability.
