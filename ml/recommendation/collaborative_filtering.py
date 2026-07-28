#!/usr/bin/env python3
"""
IntelliVend Recommendation Engine - Item-Based Collaborative Filtering
Calculates Item-Item Cosine Similarity Matrix and predicts top-3 product recommendations per customer.
Exports trained recommender model artifact to `ml/recommendation/models/recommender_model.pkl`.
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity

from generate_purchase_history import generate_synthetic_purchases, PRODUCTS

MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATA_PATH = Path(__file__).parent / "data" / "purchase_history.csv"

class ItemBasedRecommender:
    def __init__(self):
        self.item_similarity_df = None
        self.user_item_matrix = None
        self.product_metadata = PRODUCTS
        self.popular_products = []

    def fit(self, df):
        """Constructs User-Item Matrix and calculates Item-Item Cosine Similarity Matrix."""
        # Calculate implicit rating score per customer-product pair
        user_item_scores = df.groupby(["customer_id", "product_id"]).agg(
            frequency=("transaction_id", "count"),
            avg_rating=("implicit_rating", "mean"),
            total_qty=("quantity", "sum")
        ).reset_index()

        # Score formula: log(1 + total_qty) * avg_rating
        user_item_scores["score"] = np.log1p(user_item_scores["total_qty"]) * user_item_scores["avg_rating"]

        # Pivot to User-Item Matrix (Rows = Customers, Columns = Products)
        self.user_item_matrix = user_item_scores.pivot(
            index="customer_id",
            columns="product_id",
            values="score"
        ).fillna(0.0)

        # Compute Item-Item Cosine Similarity Matrix (Columns vs Columns)
        item_matrix = self.user_item_matrix.values.T # Shape: (Num_Products, Num_Users)
        similarity_matrix = cosine_similarity(item_matrix)

        product_ids = self.user_item_matrix.columns.tolist()
        self.item_similarity_df = pd.DataFrame(similarity_matrix, index=product_ids, columns=product_ids)

        # Calculate overall popular products for cold-start fallbacks
        popularity = df.groupby("product_id")["quantity"].sum().sort_values(ascending=False)
        self.popular_products = popularity.index.tolist()

        print("✅ Fitted Item-Based Collaborative Filtering Model.")
        print(f"📊 User-Item Matrix Shape: {self.user_item_matrix.shape}")
        print(f"📐 Item Similarity Matrix Shape: {self.item_similarity_df.shape}")
        return self

    def recommend(self, customer_id: str, top_n: int = 3):
        """Predicts top-N product recommendations for a target customer ID."""
        all_products = list(self.product_metadata.keys())

        # Cold start fallback if customer not in training dataset
        if self.user_item_matrix is None or customer_id not in self.user_item_matrix.index:
            top_popular = self.popular_products[:top_n]
            return [
                {
                    "product_id": pid,
                    "product_name": self.product_metadata[pid]["name"],
                    "category": self.product_metadata[pid]["category"],
                    "price": self.product_metadata[pid]["price"],
                    "recommendation_score": 0.85,
                    "match_reason": "Popular Fleet Bestseller (Cold-Start Customer)"
                }
                for pid in top_popular
            ]

        # Customer's historical interaction scores
        user_ratings = self.user_item_matrix.loc[customer_id]
        purchased_products = user_ratings[user_ratings > 0].index.tolist()

        predicted_scores = {}

        for target_item in all_products:
            # Score candidate item based on similarity to items customer has bought
            sim_scores = self.item_similarity_df[target_item]
            
            numerator = 0.0
            denominator = 0.0

            for purchased_item in purchased_products:
                sim = sim_scores[purchased_item]
                rating = user_ratings[purchased_item]
                
                numerator += sim * rating
                denominator += abs(sim)

            if denominator > 0:
                pred_score = numerator / denominator
            else:
                pred_score = 0.0

            # Slightly penalize items already heavily purchased to promote discovery
            if target_item in purchased_products:
                pred_score *= 0.65

            predicted_scores[target_item] = pred_score

        # Sort recommendations by score descending
        sorted_items = sorted(predicted_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

        recommendations = []
        for pid, score in sorted_items:
            p_info = self.product_metadata[pid]
            # Find top matching item from customer's history for match explanation
            best_match_item = None
            if purchased_products:
                sims = self.item_similarity_df[pid][purchased_products]
                best_match_item = sims.idxmax()

            match_explanation = f"Because you purchased {self.product_metadata[best_match_item]['name']}" if best_match_item else "Recommended based on user preferences"

            recommendations.append({
                "product_id": pid,
                "product_name": p_info["name"],
                "category": p_info["category"],
                "price": p_info["price"],
                "recommendation_score": round(float(score), 3),
                "match_reason": match_explanation
            })

        return recommendations

def train_and_export():
    if not DATA_PATH.exists():
        df_raw = generate_synthetic_purchases()
    else:
        df_raw = pd.read_csv(DATA_PATH)

    recommender = ItemBasedRecommender()
    recommender.fit(df_raw)

    model_save_path = MODELS_DIR / "recommender_model.pkl"
    with open(model_save_path, "wb") as f:
        pickle.dump(recommender, f)

    print(f"💾 Saved Recommender Model artifact to: {model_save_path}")
    return recommender

if __name__ == "__main__":
    train_and_export()
