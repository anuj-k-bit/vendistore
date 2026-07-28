import os
import sys
import json
import pickle
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RecommendationService")

WORKSPACE_ROOT = Path(__file__).parent.parent.parent.parent
MODEL_PATH = WORKSPACE_ROOT / "ml" / "recommendation" / "models" / "recommender_model.pkl"

sys.path.insert(0, str(WORKSPACE_ROOT / "ml" / "recommendation"))
from collaborative_filtering import ItemBasedRecommender, train_and_export

recommender_model = None

def load_recommender_model():
    global recommender_model
    if not MODEL_PATH.exists():
        logger.warning(f"Recommender model not found at {MODEL_PATH}. Training model now...")
        recommender_model = train_and_export()
    else:
        with open(MODEL_PATH, "rb") as f:
            recommender_model = pickle.load(f)
        logger.info("Successfully loaded Item-Based Collaborative Filtering Recommender Model.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_recommender_model()
    yield

app = FastAPI(
    title="IntelliVend Personalized Recommendation Microservice",
    version="1.0.0",
    description="Item-Based Collaborative Filtering recommendation service suggesting top 3 products per customer",
    lifespan=lifespan
)

class RecommendedProductItem(BaseModel):
    product_id: str
    product_name: str
    category: str
    price: float
    recommendation_score: float
    match_reason: str

class RecommendationResponse(BaseModel):
    customer_id: str
    total_recommendations: int
    recommendations: List[RecommendedProductItem]
    customer_past_purchases: List[str]

    model_config = ConfigDict(from_attributes=True)

@app.get("/")
def read_root():
    return {
        "service": "IntelliVend Recommendation Microservice",
        "status": "HEALTHY",
        "endpoints": {
            "get_recommendations": "GET /recommendations/{customer_id}",
            "similar_products": "GET /similar-products/{product_id}",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "recommendation-service",
        "model_loaded": recommender_model is not None
    }

@app.get("/recommendations/{customer_id}", response_model=RecommendationResponse)
def get_customer_recommendations(customer_id: str):
    """
    Returns top-3 product recommendations for a specific customer ID using Item-Based Collaborative Filtering.
    """
    if not recommender_model:
        raise HTTPException(status_code=500, detail="Recommender model not initialized.")

    recs = recommender_model.recommend(customer_id, top_n=3)

    # Fetch customer's past purchase history for context
    past_purchases = []
    if (recommender_model.user_item_matrix is not None and 
        customer_id in recommender_model.user_item_matrix.index):
        user_series = recommender_model.user_item_matrix.loc[customer_id]
        bought_pids = user_series[user_series > 0].index.tolist()
        past_purchases = [recommender_model.product_metadata[pid]["name"] for pid in bought_pids]

    return RecommendationResponse(
        customer_id=customer_id,
        total_recommendations=len(recs),
        recommendations=[RecommendedProductItem(**r) for r in recs],
        customer_past_purchases=past_purchases
    )

@app.get("/similar-products/{product_id}")
def get_similar_products(product_id: str):
    """Returns top 3 similar products based on item-item cosine similarity."""
    if not recommender_model or recommender_model.item_similarity_df is None:
        raise HTTPException(status_code=500, detail="Recommender model not initialized.")

    if product_id not in recommender_model.item_similarity_df.index:
        raise HTTPException(status_code=404, detail=f"Product ID '{product_id}' not found.")

    sim_series = recommender_model.item_similarity_df[product_id].drop(product_id).sort_values(ascending=False)[:3]
    
    similar_items = []
    for pid, sim in sim_series.items():
        p_info = recommender_model.product_metadata[pid]
        similar_items.append({
            "product_id": pid,
            "product_name": p_info["name"],
            "similarity_score": round(float(sim), 3)
        })

    return {
        "target_product_id": product_id,
        "target_product_name": recommender_model.product_metadata[product_id]["name"],
        "similar_products": similar_items
    }
