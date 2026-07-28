#!/usr/bin/env python3
"""
IntelliVend Demand Forecasting - Synthetic Data Generator
Generates 90 days of daily sales data for 10 vending machines x 8 products (80 time series).
Incorporates trend, weekday/weekend seasonality, machine-product baselines, and noise.
Saved to `ml/forecasting/data/synthetic_sales.csv`.
"""

import os
import json
import random
import datetime
import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MACHINES = [f"VM-10{i}" if i < 10 else f"VM-{100+i}" for i in range(1, 11)]

PRODUCTS = [
    {"product_id": "prod-1", "product_name": "Nitro Cold Brew", "category": "Coffee & Tea", "base_range": (10, 25)},
    {"product_id": "prod-2", "product_name": "Matcha Green Tea Latte", "category": "Coffee & Tea", "base_range": (8, 20)},
    {"product_id": "prod-3", "product_name": "Electrolyte Spark Hydration", "category": "Hydration", "base_range": (6, 18)},
    {"product_id": "prod-4", "product_name": "Dark Chocolate Almond Bar", "category": "Snacks", "base_range": (12, 28)},
    {"product_id": "prod-5", "product_name": "Dragonfruit Sparkling Water", "category": "Hydration", "base_range": (5, 15)},
    {"product_id": "prod-6", "product_name": "Organic Protein Crunch Bar", "category": "Snacks", "base_range": (8, 22)},
    {"product_id": "prod-7", "product_name": "Detox Green Juice", "category": "Fresh Juices", "base_range": (4, 14)},
    {"product_id": "prod-8", "product_name": "Mango Passion Kombucha", "category": "Fresh Juices", "base_range": (7, 19)},
]

# Weekday seasonality multiplier: Mon(0) .. Sun(6)
WEEKDAY_MULTIPLIERS = [0.85, 0.95, 1.0, 1.05, 1.30, 1.35, 1.15]

def generate_synthetic_sales_data(days=90, start_date_str="2026-01-01", random_seed=42):
    np.random.seed(random_seed)
    random.seed(random_seed)

    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
    date_list = [start_date + datetime.timedelta(days=i) for i in range(days)]

    records = []

    # Assign machine-product specific demand baselines and trends
    series_params = {}
    for m in MACHINES:
        for p in PRODUCTS:
            key = (m, p["product_id"])
            base = np.random.uniform(p["base_range"][0], p["base_range"][1])
            trend_slope = np.random.uniform(-0.03, 0.05) # slight growth or decay
            series_params[key] = {
                "base": base,
                "trend_slope": trend_slope,
                "product_name": p["product_name"],
                "category": p["category"]
            }

    for day_idx, current_date in enumerate(date_list):
        weekday = current_date.weekday()
        weekday_mult = WEEKDAY_MULTIPLIERS[weekday]
        date_str = current_date.strftime("%Y-%m-%d")
        is_weekend = 1 if weekday >= 5 else 0

        for m in MACHINES:
            # Machine location multiplier (e.g. Airport/Metro higher volume)
            machine_mult = 1.3 if m in ["VM-102", "VM-103"] else 1.0

            for p in PRODUCTS:
                pid = p["product_id"]
                params = series_params[(m, pid)]
                
                # Demand equation: (Base + Trend*t) * Weekday_Multiplier * Machine_Multiplier + Noise
                trend_val = params["base"] + (params["trend_slope"] * day_idx)
                expected_demand = trend_val * weekday_mult * machine_mult

                # Add noise
                noise = np.random.normal(0, scale=max(1.0, expected_demand * 0.15))
                sales_count = int(np.clip(round(expected_demand + noise), 0, 100))

                records.append({
                    "date": date_str,
                    "day_idx": day_idx,
                    "day_of_week": weekday,
                    "is_weekend": is_weekend,
                    "machine_id": m,
                    "product_id": pid,
                    "product_name": params["product_name"],
                    "category": params["category"],
                    "daily_sales": sales_count
                })

    df = pd.DataFrame(records)
    csv_path = DATA_DIR / "synthetic_sales.csv"
    df.to_csv(csv_path, index=False)
    print(f"✅ Generated {len(df)} synthetic daily sales records across {len(MACHINES)} machines and {len(PRODUCTS)} products.")
    print(f"📄 Saved to: {csv_path}")
    return df

if __name__ == "__main__":
    generate_synthetic_sales_data()
