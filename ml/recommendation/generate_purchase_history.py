#!/usr/bin/env python3
"""
IntelliVend Recommendation - Synthetic Purchase History Generator
Generates 1,200 purchase transactions for 100 customers across 8 vending products.
Incorporates customer preference clusters:
- Coffee & Snack Enthusiasts
- Health & Fresh Juice Fans
- Hydration & Fitness Seekers
Saved to `ml/recommendation/data/purchase_history.csv`.
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

CUSTOMERS = [f"CUST-{100+i}" for i in range(1, 101)]

PRODUCTS = {
    "prod-1": {"name": "Nitro Cold Brew", "category": "Coffee & Tea", "price": 4.50},
    "prod-2": {"name": "Matcha Green Tea Latte", "category": "Coffee & Tea", "price": 4.00},
    "prod-3": {"name": "Electrolyte Spark Hydration", "category": "Hydration", "price": 3.25},
    "prod-4": {"name": "Dark Chocolate Almond Bar", "category": "Snacks", "price": 2.75},
    "prod-5": {"name": "Dragonfruit Sparkling Water", "category": "Hydration", "price": 2.50},
    "prod-6": {"name": "Organic Protein Crunch Bar", "category": "Snacks", "price": 3.50},
    "prod-7": {"name": "Detox Green Juice", "category": "Fresh Juices", "price": 5.00},
    "prod-8": {"name": "Mango Passion Kombucha", "category": "Fresh Juices", "price": 4.25}
}

# Customer Personas & Co-occurrence Affinities
PERSONAS = [
    # Persona 0: Coffee & Snacks (Cold Brew, Matcha, Chocolate, Protein Bar)
    {"weights": [0.35, 0.25, 0.05, 0.20, 0.02, 0.10, 0.01, 0.02]},
    # Persona 1: Health & Juices (Green Juice, Kombucha, Matcha, Dragonfruit)
    {"weights": [0.03, 0.20, 0.05, 0.02, 0.15, 0.05, 0.25, 0.25]},
    # Persona 2: Fitness & Hydration (Electrolyte, Protein Bar, Sparkling Water, Cold Brew)
    {"weights": [0.20, 0.02, 0.30, 0.05, 0.20, 0.20, 0.02, 0.01]},
    # Persona 3: General Snacker (Chocolate Bar, Protein Bar, Cold Brew, Kombucha)
    {"weights": [0.15, 0.10, 0.10, 0.25, 0.05, 0.25, 0.02, 0.08]}
]

def generate_synthetic_purchases(total_transactions=1200, random_seed=42):
    random.seed(random_seed)
    np.random.seed(random_seed)

    product_ids = list(PRODUCTS.keys())
    records = []

    start_date = datetime.datetime(2026, 1, 1)

    # Assign each customer a persona
    customer_personas = {c: random.choice(PERSONAS) for c in CUSTOMERS}

    for tx_id in range(1, total_transactions + 1):
        cust_id = random.choice(CUSTOMERS)
        persona = customer_personas[cust_id]
        
        # Sample product according to customer persona weights
        pid = np.random.choice(product_ids, p=persona["weights"])
        p_info = PRODUCTS[pid]

        # Random timestamp over 90 days
        days_offset = random.randint(0, 89)
        hours_offset = random.randint(7, 22)
        tx_time = start_date + datetime.timedelta(days=days_offset, hours=hours_offset, minutes=random.randint(0, 59))

        # Quantity (mostly 1 or 2)
        qty = np.random.choice([1, 2, 3], p=[0.82, 0.14, 0.04])
        # Implicit rating / interaction weight based on repeat purchases
        rating = float(random.randint(4, 5)) if qty > 1 else float(random.randint(3, 5))

        records.append({
            "transaction_id": f"TX-{tx_id:05d}",
            "customer_id": cust_id,
            "product_id": pid,
            "product_name": p_info["name"],
            "category": p_info["category"],
            "unit_price": p_info["price"],
            "quantity": qty,
            "implicit_rating": rating,
            "timestamp": tx_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    df = pd.DataFrame(records)
    csv_path = DATA_DIR / "purchase_history.csv"
    df.to_csv(csv_path, index=False)

    print(f"✅ Generated {len(df)} synthetic purchase records across {len(CUSTOMERS)} customers and {len(PRODUCTS)} products.")
    print(f"📄 Saved dataset to: {csv_path}")
    return df

if __name__ == "__main__":
    generate_synthetic_purchases()
