#!/usr/bin/env python3
"""
IntelliVend Dynamic Pricing Simulation Engine
Simulates 1,000 customer purchase sessions comparing:
1. Static Baseline Pricing (1.00x)
2. Rule-Based Heuristic Pricing (±15%)
3. LinUCB Contextual Bandit Dynamic Pricing

Saves revenue comparison metrics to `ml/pricing/data/revenue_comparison.json`.
"""

import os
import json
import random
import numpy as np
from pathlib import Path

from rule_based import calculate_rule_based_price
from linucb_bandit import LinUCBPricingBandit

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def simulate_customer_purchase(multiplier: float, base_price: float, stock_ratio: float, hour_of_day: int):
    """
    Simulates realistic price-elastic customer purchase conversion.
    Customers have higher willingness to pay during peak hours & low stock scarcity.
    """
    base_conv = 0.65 # 65% baseline conversion at 1.00x price

    # Price elasticity penalty / reward
    if multiplier > 1.0:
        elasticity_penalty = 0.45 * (multiplier - 1.0)
    else:
        elasticity_penalty = -0.35 * (1.0 - multiplier)

    # Contextual willingness-to-pay boosts
    peak_boost = 0.12 if hour_of_day in [12, 13, 17, 18, 19] else 0.0
    scarcity_boost = 0.10 if stock_ratio <= 0.25 else 0.0

    conv_prob = min(0.95, max(0.05, base_conv - elasticity_penalty + peak_boost + scarcity_boost))
    bought = 1 if random.random() < conv_prob else 0

    actual_price = round(base_price * multiplier, 2)
    revenue = actual_price if bought else 0.0

    return bought, revenue, round(conv_prob, 3)

def run_pricing_simulation(num_sessions=1000, random_seed=42):
    random.seed(random_seed)
    np.random.seed(random_seed)

    bandit = LinUCBPricingBandit(alpha=0.3)

    # Tracking metrics
    stats = {
        "static": {"revenue": 0.0, "purchases": 0, "total_sessions": 0},
        "rule_based": {"revenue": 0.0, "purchases": 0, "total_sessions": 0},
        "linucb": {"revenue": 0.0, "purchases": 0, "total_sessions": 0}
    }

    base_prices = [2.50, 3.00, 3.50, 4.00, 4.50]

    for session_idx in range(1, num_sessions + 1):
        # Sample realistic session context
        base_price = random.choice(base_prices)
        current_stock = random.randint(1, 15)
        stock_ratio = current_stock / 15.0
        hour_of_day = random.randint(0, 23)
        predicted_demand = float(random.uniform(5.0, 30.0))
        is_weekend = 1 if random.random() < 0.28 else 0

        # ----------------------------------------------------
        # 1. Static Strategy (1.00x)
        # ----------------------------------------------------
        static_mult = 1.00
        b_static, r_static, _ = simulate_customer_purchase(static_mult, base_price, stock_ratio, hour_of_day)
        stats["static"]["revenue"] += r_static
        stats["static"]["purchases"] += b_static
        stats["static"]["total_sessions"] += 1

        # ----------------------------------------------------
        # 2. Rule-Based Strategy (±15%)
        # ----------------------------------------------------
        rule_res = calculate_rule_based_price(base_price, current_stock, 15, hour_of_day, predicted_demand)
        rule_mult = rule_res["price_multiplier"]
        b_rule, r_rule, _ = simulate_customer_purchase(rule_mult, base_price, stock_ratio, hour_of_day)
        stats["rule_based"]["revenue"] += r_rule
        stats["rule_based"]["purchases"] += b_rule
        stats["rule_based"]["total_sessions"] += 1

        # ----------------------------------------------------
        # 3. LinUCB Contextual Bandit Strategy
        # ----------------------------------------------------
        ctx = bandit.construct_context(stock_ratio, hour_of_day, predicted_demand, is_weekend, base_price)
        arm_res = bandit.select_arm(ctx)
        linucb_arm_idx = arm_res["arm_index"]
        linucb_mult = arm_res["multiplier"]

        b_linucb, r_linucb, _ = simulate_customer_purchase(linucb_mult, base_price, stock_ratio, hour_of_day)
        stats["linucb"]["revenue"] += r_linucb
        stats["linucb"]["purchases"] += b_linucb
        stats["linucb"]["total_sessions"] += 1

        # Online update bandit with revenue reward
        bandit.update(linucb_arm_idx, ctx, r_linucb)

    # Save trained bandit weights
    bandit.save_model()

    # Calculate summary metrics
    static_rev = round(stats["static"]["revenue"], 2)
    rule_rev = round(stats["rule_based"]["revenue"], 2)
    linucb_rev = round(stats["linucb"]["revenue"], 2)

    static_conv = round((stats["static"]["purchases"] / num_sessions) * 100.0, 2)
    rule_conv = round((stats["rule_based"]["purchases"] / num_sessions) * 100.0, 2)
    linucb_conv = round((stats["linucb"]["purchases"] / num_sessions) * 100.0, 2)

    uplift_vs_static = round(((linucb_rev - static_rev) / static_rev) * 100.0, 2)
    uplift_vs_rule = round(((linucb_rev - rule_rev) / rule_rev) * 100.0, 2)

    comparison_results = {
        "num_simulated_sessions": num_sessions,
        "strategies": {
            "static_baseline": {
                "name": "Static Nominal Pricing (1.00x)",
                "total_revenue": static_rev,
                "conversion_rate_pct": static_conv,
                "purchases_count": stats["static"]["purchases"]
            },
            "rule_based": {
                "name": "Rule-Based Heuristic (±15%)",
                "total_revenue": rule_rev,
                "conversion_rate_pct": rule_conv,
                "purchases_count": stats["rule_based"]["purchases"]
            },
            "linucb_bandit": {
                "name": "LinUCB Contextual Bandit Dynamic Pricing",
                "total_revenue": linucb_rev,
                "conversion_rate_pct": linucb_conv,
                "purchases_count": stats["linucb"]["purchases"]
            }
        },
        "uplift_summary": {
            "revenue_uplift_vs_static_pct": uplift_vs_static,
            "revenue_uplift_vs_rule_based_pct": uplift_vs_rule,
            "additional_revenue_generated": round(linucb_rev - static_rev, 2)
        }
    }

    out_file = DATA_DIR / "revenue_comparison.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(comparison_results, f, indent=2)

    print("=" * 75)
    print("💰 INTELLIVEND DYNAMIC PRICING SIMULATION RESULTS (1,000 Sessions)")
    print("=" * 75)
    print(f"  Strategy                          | Revenue ($)   | Conv Rate | Purchases")
    print(f"  ----------------------------------+---------------+-----------+-----------")
    print(f"  1. Static Baseline (1.00x)        | ${static_rev:<12.2f} | {static_conv:<8.1f}% | {stats['static']['purchases']}")
    print(f"  2. Rule-Based Heuristic (±15%)    | ${rule_rev:<12.2f} | {rule_conv:<8.1f}% | {stats['rule_based']['purchases']}")
    print(f"  3. LinUCB Contextual Bandit       | ${linucb_rev:<12.2f} | {linucb_conv:<8.1f}% | {stats['linucb']['purchases']}")
    print(f"  ----------------------------------+---------------+-----------+-----------")
    print(f"  🚀 LinUCB Revenue Uplift vs Static | +{uplift_vs_static:.2f}% (+$ {linucb_rev - static_rev:.2f})")
    print(f"  📈 LinUCB Revenue Uplift vs Rule   | +{uplift_vs_rule:.2f}%")
    print("=" * 75)
    print(f"📄 Saved results to: {out_file}")

    return comparison_results

if __name__ == "__main__":
    run_pricing_simulation()
