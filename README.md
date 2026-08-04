# IntelliVend: Autonomous AI-Powered Vending Machine & Fleet Management System

[![CI Pipeline](https://github.com/intellivend/intellivend/actions/workflows/ci.yml/badge.svg)](https://github.com/intellivend/intellivend/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-cyan.svg)](https://react.dev/)
[![Stripe](https://img.shields.io/badge/Stripe-Test%20Mode-6772E5.svg)](https://stripe.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-HPA-326CE5.svg)](https://kubernetes.io/)

**IntelliVend** is an enterprise-grade, autonomous vending machine and fleet management platform combining **Real-Time Event Streaming (Kafka/MQTT)**, **Stripe Test-Mode Payments with Signed Webhooks**, **MLOps (LightGBM Demand Forecasting with SHAP Explainability & Rolling MAE Drift Detection, PyTorch Computer Vision, LinUCB Contextual Bandits, Collaborative Filtering)**, **Leaflet OpenStreetMap Restock Polyline Routing**, and a **Policy-Guarded Multi-Agent System (Supervisor, Restock Planner, Pricing Agent, Ops/Anomaly Agent)**.

---

## 🚀 Live Deployments

| Component | Description | Live Deployment URL |
| :--- | :--- | :--- |
| 🎛️ **Admin Operations Dashboard** | Fleet GIS Map, Restock Priority, Agent Audit Feed & SHAP | https://vendistore.vercel.app/ |
| 🛒 **Customer Touch Kiosk UI** | Interactive Vending Kiosk with Stripe Checkout & AI Support Chat | https://vendistore-78h9.vercel.app/ |
| ⚙️ **Order & Payment API** | Order processing microservice with signed Stripe webhooks | [https://vendistore-1.onrender.com/docs](https://vendistore-1.onrender.com/docs) |
| 📦 **Inventory Microservice** | PostgreSQL fleet inventory manager & Kafka consumer | [https://vendistore-inventory.onrender.com/docs](https://vendistore-inventory.onrender.com/docs) |

---

## 🏛️ System Architecture

```mermaid
graph TD
    subgraph Edge & Touch Terminals
        Kiosk["🛒 Touch Screen Kiosk UI (Stripe Checkout - Port 3000)"]
        Simulator["📡 Python Machine Telemetry Simulator (MQTT)"]
    end

    subgraph Messaging & Event Ingestion
        MQTT["Mosquitto MQTT Broker (Port 1883)"]
        Bridge["🌉 MQTT-Kafka Bridge"]
        Kafka[("⚡ Apache Kafka Event Engine (Purchases, Restocks, Sensors)")]
    end

    subgraph Core Microservices & Payments
        Postgres[("🐘 PostgreSQL / SQLAlchemy DB")]
        InvSvc["📦 Inventory Service (Port 8080)"]
        OrdSvc["💳 Order Service + Stripe Webhooks (Port 8081)"]
    end

    subgraph Machine Learning Inference & MLOps Stack
        ForecastSvc["🤖 Demand Forecast ML + SHAP & Drift (Port 8082)"]
        VisionSvc["👁️ Computer Vision Slot Detector (PyTorch - Port 8083)"]
        PricingSvc["💰 Dynamic Pricing Engine (LinUCB Bandit - Port 8084)"]
        RecSvc["🌟 Collaborative Filtering Recommender (Port 8085)"]
    end

    subgraph Autonomous Agentic Tool Layer & Guardrails
        AgenticLayer["🛡️ Agentic Tool Layer & Policy Engine (Port 8086)"]
        Guardrails["🔒 Guardrails: Price ±15%, Cost Floor, Refund <= $10"]
        AuditLog[("📜 Append-Only agent_audit_log Table")]
        Supervisor["👑 Supervisor & Multi-Agent ReAct Engine"]
    end

    subgraph Fleet Control Center
        AdminDash["🎛️ Admin Operations Dashboard (Leaflet Map - Port 3001)"]
    end

    Simulator --> MQTT
    MQTT --> Bridge
    Bridge --> Kafka
    Kafka --> InvSvc
    Kiosk --> OrdSvc
    OrdSvc -->|Signed Webhook| Postgres
    InvSvc --> Postgres

    AgenticLayer --> Guardrails
    AgenticLayer --> AuditLog
    Supervisor --> AgenticLayer
    AgenticLayer --> InvSvc
    AgenticLayer --> ForecastSvc
    AgenticLayer --> PricingSvc

    Kiosk --> RecSvc
    AdminDash --> InvSvc
    AdminDash --> ForecastSvc
    AdminDash --> PricingSvc
    AdminDash --> AuditLog
```

---

## 🌟 Key Features & 3 Enterprise Enhancements

1. **Stripe Test-Mode Payments & Signed Webhooks**:
   - `order-service` creates Stripe `PaymentIntents` (`POST /create-payment-intent`).
   - Webhook listener `POST /webhook/stripe` verifies HMAC signature (`stripe-signature`) and **only deducts stock & logs transactions upon receiving `payment_intent.succeeded`**.
   - Handles declined test cards (`4000 0000 0000 0002`) gracefully.

2. **ML Model Drift Detection & SHAP Feature Explainability**:
   - **Rolling MAE Drift**: Logs prediction vs actual demand, flags `drift_detected: true` if rolling MAE $> 3.50$, and exposes `POST /forecast/retrain`.
   - **SHAP Value Explanations**: `GET /forecast/{machine_id}/{product_id}/explain` breaks down top contributing demand factors (*"demand is up because: day_of_week=Friday (+4.2 units), recent trend up (+2.8 units)"*).

3. **Leaflet OpenStreetMap Restock Polyline Route Map**:
   - Renders 10 San Francisco vending nodes with color-coded status pins (Red: Critical, Amber: Low Stock, Green: Nominal).
   - Overlays polyline connected path following the Restock Planner agent's priority route (`VM-104` $\rightarrow$ `VM-107` $\rightarrow$ `VM-101` $\rightarrow$ `VM-106`).

4. **Autonomous Multi-Agent System**:
   - 👑 **Supervisor Agent**, 🚚 **Restock Planner Agent**, 🏷️ **Pricing Agent**, and 🛠️ **Ops / Anomaly Agent** executing ReAct reasoning traces (*Thought $\rightarrow$ Action $\rightarrow$ Observation*).

5. **Deterministic Guardrails Policy Engine**:
   - Max $\pm 15\%$ price change, cost floor protection, auto-approved refunds $\le \$10.00$ ($> \$10.00$ escalated to human manager with ticket tracking).

---

## ⚡ Quickstart Setup Guide

### Option 1: Docker Compose (Local Stack)

```bash
# 1. Clone Repository
git clone https://github.com/intellivend/intellivend.git
cd intellivend

# 2. Build and Start Full Container Stack
docker-compose up --build -d

# 3. Verify Running Services
docker-compose ps
```

### Option 2: Kubernetes Deployment & HPA

```bash
# 1. Apply Kubernetes Deployments & Services
kubectl apply -f deploy/k8s/deployments.yaml

# 2. Enable Horizontal Pod Autoscalers (HPA) for ML Inference Services
kubectl apply -f deploy/k8s/ml-hpa.yaml

# 3. Check HPA Status
kubectl get hpa -n intellivend
```

---

## 📐 Architectural Design Trade-Offs

Detailed architectural and MLOps design decisions are documented in [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md).

---

## 📈 Scaling to 10,000 Machines

To scale IntelliVend to 10,000 connected vending machines, the system deploys:
1. **128-Partition Kafka Cluster**: Topic partitioning by `city_geohash` processing 50,000 telemetry msgs/sec.
2. **Edge Compute (PyTorch ONNX)**: Vision models executed directly on Raspberry Pi 5 / Jetson Nano edge devices.
3. **Redis Enterprise Distributed Caching**: 5-minute TTL caching layer reducing database read load by $95\%$.
4. **Ray / Apache Spark MLOps**: Daily batch retraining of 10,000 forecasting models in parallel.

---

## 📄 License
Distributed under the **MIT License**. See `LICENSE` for more information.
