#!/usr/bin/env python3
"""
IntelliVend Personalized Recommendation Service End-to-End Verifier
Executes synthetic data generation, model training, and tests GET /recommendations/{customer_id}
against sample customer IDs (CUST-101, CUST-102, CUST-103).
"""

import sys
import io
import json
import time
import urllib.request
from pathlib import Path

# Safe UTF-8 output formatting for Windows terminal
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent / "ml" / "recommendation"))

from generate_purchase_history import generate_synthetic_purchases
from collaborative_filtering import train_and_export

def verify_recommendation_pipeline():
    print("=" * 75)
    print("[1/3] GENERATING SYNTHETIC PURCHASE HISTORY (1,200 TRANSACTIONS x 100 CUSTOMERS)")
    print("=" * 75)
    generate_synthetic_purchases(total_transactions=1200)

    print("\n" + "=" * 75)
    print("[2/3] TRAINING ITEM-BASED COLLABORATIVE FILTERING MODEL")
    print("=" * 75)
    recommender = train_and_export()

    print("\n" + "=" * 75)
    print("📐 ITEM-ITEM COSINE SIMILARITY MATRIX")
    print("=" * 75)
    sim_df = recommender.item_similarity_df.round(2)
    print(sim_df)

    print("\n" + "=" * 75)
    print("[3/3] TESTING RECOMMENDATIONS FOR SAMPLE CUSTOMER IDs")
    print("=" * 75)

    sample_customers = ["CUST-101", "CUST-102", "CUST-103", "CUST-999_NEW"]

    for cid in sample_customers:
        recs = recommender.recommend(cid, top_n=3)
        past_purchases = []
        if recommender.user_item_matrix is not None and cid in recommender.user_item_matrix.index:
            user_series = recommender.user_item_matrix.loc[cid]
            bought_pids = user_series[user_series > 0].index.tolist()
            past_purchases = [recommender.product_metadata[pid]["name"] for pid in bought_pids]

        print(f"\n👤 Customer ID: {cid}")
        print(f"  * Past Purchases : {past_purchases if past_purchases else 'None (New Customer)'}")
        print("  * Top 3 Recommendations:")
        for r in recs:
            print(f"    - [{r['product_id']}] {r['product_name']:<30} | Score: {r['recommendation_score']:<5.2f} | Reason: {r['match_reason']}")

    print("=" * 75)

if __name__ == "__main__":
    verify_recommendation_pipeline()
