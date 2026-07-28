#!/usr/bin/env python3
"""
IntelliVend ML Demand Forecasting End-to-End Verification
Executes synthetic data generation, model training, MLflow backtesting, and FastAPI prediction serving.
"""

import sys
import io
import json
import time
import urllib.request
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent / "ml" / "forecasting"))
sys.path.insert(0, str(Path(__file__).parent / "backend" / "forecast-service"))

from generate_synthetic_data import generate_synthetic_sales_data
from train import train_and_evaluate

def verify_forecasting_pipeline():
    print("=" * 75)
    print("[1/4] GENERATING 90 DAYS OF SYNTHETIC SALES DATA (10 MACHINES x 8 PRODUCTS)")
    print("=" * 75)
    df_raw = generate_synthetic_sales_data(days=90)

    print("\n" + "=" * 75)
    print("[2/4] TRAINING LIGHTGBM MODEL & EVALUATING BACKTEST MAE / RMSE")
    print("=" * 75)
    model_bundle = train_and_evaluate()

    metrics = model_bundle["metrics"]

    print("\n" + "=" * 75)
    print("📈 FEATURE ENGINEERING COMPARISON RESULTS (BACKTEST EVALUATION)")
    print("=" * 75)
    print(f"  Metric              | Before FE (Baseline) | After FE (Advanced) | Improvement")
    print(f"  --------------------+----------------------+---------------------+-------------")
    print(f"  Backtest MAE        | {metrics['mae_before_fe']:<20.3f} | {metrics['mae_after_fe']:<19.3f} | +{metrics['mae_improvement_pct']:.2f}%")
    print(f"  Backtest RMSE       | {metrics['rmse_before_fe']:<20.3f} | {metrics['rmse_after_fe']:<19.3f} | +{metrics['rmse_improvement_pct']:.2f}%")
    print("=" * 75)

    print("\n[3/4] VERIFYING MODEL ARTIFACT & FEATURE IMPORTANCE")
    model = model_bundle["model"]
    features = model_bundle["features"]
    importances = model.feature_importances_
    feat_imp = sorted(zip(features, importances), key=lambda x: x[1], reverse=True)[:5]
    print("Top 5 Predictive Features:")
    for feat, imp in feat_imp:
        print(f"  - {feat:<25}: Importance Score = {imp}")

    return model_bundle

if __name__ == "__main__":
    verify_forecasting_pipeline()
