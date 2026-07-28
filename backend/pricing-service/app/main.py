import os
import sys
import json
import logging
import datetime
import httpx
import numpy as np
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PricingService")

WORKSPACE_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "ml" / "pricing"))

from rule_based import calculate_rule_based_price
from linucb_bandit import LinUCBPricingBandit
from simulate_revenue import run_pricing_simulation

COMPARISON_JSON = WORKSPACE_ROOT / "ml" / "pricing" / "data" / "revenue_comparison.json"
FORECAST_SERVICE_URL = "http://localhost:8082"

bandit_model = None

def init_pricing_engine():
    global bandit_model
    if not COMPARISON_JSON.exists():
        logger.info("Running initial dynamic pricing revenue simulation...")
        run_pricing_simulation(num_sessions=1000)
    
    bandit_model = LinUCBPricingBandit.load_model()
    logger.info("LinUCB Contextual Bandit Dynamic Pricing Engine initialized.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pricing_engine()
    yield

app = FastAPI(
    title="IntelliVend Dynamic Pricing Microservice",
    version="1.0.0",
    description="Contextual Bandit (LinUCB) and Rule-Based dynamic pricing service integrating with demand forecast",
    lifespan=lifespan
)

class PricingRequest(BaseModel):
    base_price: float = 3.50
    current_stock: int = 4
    max_capacity: int = 15
    strategy: str = "linucb" # Options: "linucb", "rule_based", "static"

class DynamicPriceResponse(BaseModel):
    machine_id: str
    product_id: str
    base_price: float
    dynamic_price: float
    price_multiplier: float
    strategy_used: str
    confidence_bound: Optional[float] = None
    forecast_demand_7day: float
    explanation: str

    model_config = ConfigDict(from_attributes=True)

class FeedbackRequest(BaseModel):
    arm_index: int
    stock_ratio: float
    hour_of_day: int
    predicted_demand: float
    is_weekend: int
    base_price: float
    converted: bool # True if bought, False if rejected
    revenue: float

@app.get("/")
def read_root():
    return {
        "service": "IntelliVend Dynamic Pricing Microservice",
        "status": "HEALTHY",
        "endpoints": {
            "calculate_price": "POST /price/{machine_id}/{product_id}",
            "revenue_comparison": "GET /metrics/revenue-comparison",
            "feedback": "POST /feedback",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "pricing-service",
        "bandit_model_loaded": bandit_model is not None
    }

@app.get("/metrics/revenue-comparison")
def get_revenue_comparison_metrics():
    """Serves the static vs rule-based vs LinUCB contextual bandit revenue comparison results."""
    if not COMPARISON_JSON.exists():
        res = run_pricing_simulation(num_sessions=1000)
        return res

    with open(COMPARISON_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

@app.post("/price/{machine_id}/{product_id}", response_model=DynamicPriceResponse)
async def calculate_price(machine_id: str, product_id: str, req: PricingRequest):
    """
    Calculates dynamic price for machine & product based on stock, forecast demand, time of day, and LinUCB bandit strategy.
    """
    now = datetime.datetime.now()
    hour_of_day = now.hour
    is_weekend = 1 if now.weekday() >= 5 else 0

    # Attempt to fetch 7-day predicted demand from forecast-service
    predicted_demand = 15.0 # Fallback
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{FORECAST_SERVICE_URL}/forecast/{machine_id}/{product_id}")
            if resp.status_code == 200:
                fc_data = resp.json()
                predicted_demand = float(fc_data.get("total_7day_demand", 15.0))
    except Exception as e:
        logger.warning(f"Could not connect to forecast-service ({e}). Using default forecast demand {predicted_demand}")

    stock_ratio = req.current_stock / req.max_capacity if req.max_capacity > 0 else 0.5

    if req.strategy == "static":
        dynamic_price = req.base_price
        multiplier = 1.00
        explanation = "Static Nominal Baseline Pricing (1.00x multiplier)."
        confidence_bound = 0.0

    elif req.strategy == "rule_based":
        rb_res = calculate_rule_based_price(req.base_price, req.current_stock, req.max_capacity, hour_of_day, predicted_demand)
        dynamic_price = rb_res["calculated_price"]
        multiplier = rb_res["price_multiplier"]
        explanation = f"Rule-based heuristic pricing ({rb_res['adjustment_percent']:+}% adjustment based on stock & peak hours)."
        confidence_bound = 0.0

    else: # LinUCB Contextual Bandit (default)
        ctx = bandit_model.construct_context(stock_ratio, hour_of_day, predicted_demand, is_weekend, req.base_price)
        arm_res = bandit_model.select_arm(ctx)
        multiplier = arm_res["multiplier"]
        dynamic_price = round(req.base_price * multiplier, 2)
        confidence_bound = arm_res["confidence_bound"]
        explanation = f"LinUCB Contextual Bandit optimal price arm selected ({multiplier:.2f}x multiplier, UCB confidence bound = {confidence_bound:.3f})."

    return DynamicPriceResponse(
        machine_id=machine_id,
        product_id=product_id,
        base_price=req.base_price,
        dynamic_price=dynamic_price,
        price_multiplier=multiplier,
        strategy_used=req.strategy,
        confidence_bound=confidence_bound,
        forecast_demand_7day=predicted_demand,
        explanation=explanation
    )

@app.post("/feedback")
def submit_purchase_feedback(fb: FeedbackRequest):
    """Updates LinUCB bandit online weights with customer conversion outcome."""
    if not bandit_model:
        raise HTTPException(status_code=500, detail="Bandit model not initialized.")

    ctx = bandit_model.construct_context(fb.stock_ratio, fb.hour_of_day, fb.predicted_demand, fb.is_weekend, fb.base_price)
    reward = fb.revenue if fb.converted else 0.0

    bandit_model.update(fb.arm_index, ctx, reward)
    bandit_model.save_model()

    return {"status": "SUCCESS", "message": "LinUCB bandit policy updated online."}
