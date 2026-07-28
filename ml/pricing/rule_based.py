#!/usr/bin/env python3
"""
IntelliVend Dynamic Pricing - Rule-Based Baseline Engine
Calculates price adjustments within ±15% based on:
1. Stock Scarcity (<20% stock -> +10%, >80% stock -> -8%)
2. Time of Day (Peak hours 12-2 PM & 5-7 PM -> +5%, Off-peak -> -5%)
3. Demand Forecast (High demand -> +5%)
"""

def calculate_rule_based_price(base_price: float, current_stock: int, max_capacity: int = 15, hour_of_day: int = 12, predicted_7day_demand: float = 15.0):
    stock_ratio = current_stock / max_capacity if max_capacity > 0 else 0.5
    multiplier = 1.0

    # 1. Stock Scarcity Adjustment
    if stock_ratio <= 0.20:
        multiplier += 0.10 # Surge price for low stock (+10%)
    elif stock_ratio <= 0.40:
        multiplier += 0.05 # Mild surge (+5%)
    elif stock_ratio >= 0.85:
        multiplier -= 0.08 # Discount excess inventory (-8%)

    # 2. Time of Day Adjustment
    if hour_of_day in [12, 13, 17, 18, 19]:
        multiplier += 0.05 # Lunch & dinner peak (+5%)
    elif hour_of_day in [23, 0, 1, 2, 3, 4]:
        multiplier -= 0.05 # Late night off-peak (-5%)

    # 3. Forecast Demand Adjustment
    if predicted_7day_demand >= 20.0:
        multiplier += 0.05 # High demand (+5%)
    elif predicted_7day_demand <= 8.0:
        multiplier -= 0.05 # Low demand (-5%)

    # Clamp total multiplier between 0.85 (-15%) and 1.15 (+15%)
    clamped_multiplier = max(0.85, min(1.15, multiplier))
    calculated_price = round(base_price * clamped_multiplier, 2)

    return {
        "calculated_price": calculated_price,
        "price_multiplier": round(clamped_multiplier, 3),
        "adjustment_percent": round((clamped_multiplier - 1.0) * 100.0, 1),
        "rule_factors": {
            "stock_ratio": round(stock_ratio, 2),
            "hour_of_day": hour_of_day,
            "predicted_7day_demand": predicted_7day_demand
        }
    }

if __name__ == "__main__":
    res = calculate_rule_based_price(base_price=3.50, current_stock=2, hour_of_day=13, predicted_7day_demand=25.0)
    print("Rule-Based Price Result:", res)
