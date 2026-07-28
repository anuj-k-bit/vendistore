#!/usr/bin/env python3
"""
IntelliVend Demand Forecasting Model Training & MLflow Backtester
Compares Backtest MAE / RMSE before and after feature engineering.
Logs experiments to MLflow and exports winning model to `ml/forecasting/models/forecast_model.pkl`.
"""

import os
import json
import pickle
import datetime
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error

import lightgbm as lgb
import mlflow

from generate_synthetic_data import generate_synthetic_sales_data

MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATA_PATH = Path(__file__).parent / "data" / "synthetic_sales.csv"

def build_baseline_features(df):
    """Builds basic baseline features (Before Feature Engineering)."""
    df_base = df.copy()
    df_base["date"] = pd.to_datetime(df_base["date"])
    df_base = df_base.sort_values(["machine_id", "product_id", "date"]).reset_index(drop=True)

    # Basic Lags
    df_base["lag_1"] = df_base.groupby(["machine_id", "product_id"])["daily_sales"].shift(1)
    df_base["lag_7"] = df_base.groupby(["machine_id", "product_id"])["daily_sales"].shift(7)

    # Encode categoricals
    df_base["machine_code"] = df_base["machine_id"].astype("category").cat.codes
    df_base["product_code"] = df_base["product_id"].astype("category").cat.codes

    df_base = df_base.dropna().reset_index(drop=True)
    features = ["machine_code", "product_code", "day_of_week", "lag_1", "lag_7"]
    return df_base, features

def build_advanced_features(df):
    """Builds rich engineered features (After Feature Engineering)."""
    df_adv = df.copy()
    df_adv["date"] = pd.to_datetime(df_adv["date"])
    df_adv = df_adv.sort_values(["machine_id", "product_id", "date"]).reset_index(drop=True)

    # Lags
    for lag in [1, 2, 3, 7, 14]:
        df_adv[f"lag_{lag}"] = df_adv.groupby(["machine_id", "product_id"])["daily_sales"].shift(lag)

    # Rolling window statistics
    for w in [7, 14]:
        df_adv[f"rolling_mean_{w}"] = df_adv.groupby(["machine_id", "product_id"])["daily_sales"].transform(
            lambda x: x.shift(1).rolling(window=w, min_periods=3).mean()
        )
        df_adv[f"rolling_std_{w}"] = df_adv.groupby(["machine_id", "product_id"])["daily_sales"].transform(
            lambda x: x.shift(1).rolling(window=w, min_periods=3).std()
        )
        df_adv[f"rolling_max_{w}"] = df_adv.groupby(["machine_id", "product_id"])["daily_sales"].transform(
            lambda x: x.shift(1).rolling(window=w, min_periods=3).max()
        )

    # Fleet-level cross-group aggregations
    product_fleet_daily = df_adv.groupby(["date", "product_id"])["daily_sales"].transform("sum")
    df_adv["product_fleet_daily_sales"] = product_fleet_daily.groupby(df_adv["product_id"]).shift(1)

    machine_daily_total = df_adv.groupby(["date", "machine_id"])["daily_sales"].transform("sum")
    df_adv["machine_daily_total_sales"] = machine_daily_total.groupby(df_adv["machine_id"]).shift(1)

    # Expanding mean demand
    df_adv["expanding_mean"] = df_adv.groupby(["machine_id", "product_id"])["daily_sales"].transform(
        lambda x: x.shift(1).expanding().mean()
    )

    # Cyclical day of week encoding
    df_adv["sin_dow"] = np.sin(2 * np.pi * df_adv["day_of_week"] / 7.0)
    df_adv["cos_dow"] = np.cos(2 * np.pi * df_adv["day_of_week"] / 7.0)

    # Categorical codes
    df_adv["machine_code"] = df_adv["machine_id"].astype("category").cat.codes
    df_adv["product_code"] = df_adv["product_id"].astype("category").cat.codes

    df_adv = df_adv.dropna().reset_index(drop=True)

    features = [
        "machine_code", "product_code", "day_of_week", "is_weekend",
        "sin_dow", "cos_dow",
        "lag_1", "lag_2", "lag_3", "lag_7", "lag_14",
        "rolling_mean_7", "rolling_std_7", "rolling_max_7",
        "rolling_mean_14", "rolling_std_14",
        "product_fleet_daily_sales", "machine_daily_total_sales",
        "expanding_mean"
    ]
    return df_adv, features

def train_and_evaluate():
    print("=" * 70)
    print("🤖 INTELLIVEND DEMAND FORECASTING TRAINING & BACKTESTER")
    print("=" * 70)

    if not DATA_PATH.exists():
        df_raw = generate_synthetic_sales_data()
    else:
        df_raw = pd.read_csv(DATA_PATH)

    # Set up MLflow experiment
    mlflow.set_experiment("IntelliVend_Demand_Forecasting")

    # Train/Test Chronological Split: Train Days 0-74, Test Days 75-89 (Last 15 days)
    split_day = 75

    with mlflow.start_run(run_name="Feature_Engineering_Comparison"):
        # ----------------------------------------------------
        # 1. STAGE 1: BEFORE FEATURE ENGINEERING (BASELINE)
        # ----------------------------------------------------
        print("\n[1/3] Training Baseline Model (BEFORE Feature Engineering)...")
        df_base, features_base = build_baseline_features(df_raw)

        train_base = df_base[df_base["day_idx"] < split_day]
        test_base = df_base[df_base["day_idx"] >= split_day]

        X_train_base, y_train_base = train_base[features_base], train_base["daily_sales"]
        X_test_base, y_test_base = test_base[features_base], test_base["daily_sales"]

        model_base = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.05, random_state=42, verbose=-1)
        model_base.fit(X_train_base, y_train_base)

        preds_base = model_base.predict(X_test_base)
        mae_base = mean_absolute_error(y_test_base, preds_base)
        rmse_base = np.sqrt(mean_squared_error(y_test_base, preds_base))

        print(f"  --> Baseline Model (Before FE): MAE = {mae_base:.3f} | RMSE = {rmse_base:.3f}")

        # ----------------------------------------------------
        # 2. STAGE 2: AFTER FEATURE ENGINEERING (ADVANCED)
        # ----------------------------------------------------
        print("\n[2/3] Training Advanced Model (AFTER Feature Engineering)...")
        df_adv, features_adv = build_advanced_features(df_raw)

        train_adv = df_adv[df_adv["day_idx"] < split_day]
        test_adv = df_adv[df_adv["day_idx"] >= split_day]

        X_train_adv, y_train_adv = train_adv[features_adv], train_adv["daily_sales"]
        X_test_adv, y_test_adv = test_adv[features_adv], test_adv["daily_sales"]

        model_adv = lgb.LGBMRegressor(
            n_estimators=200,
            learning_rate=0.03,
            max_depth=6,
            num_leaves=31,
            random_state=42,
            verbose=-1
        )
        model_adv.fit(X_train_adv, y_train_adv)

        preds_adv = model_adv.predict(X_test_adv)
        mae_adv = mean_absolute_error(y_test_adv, preds_adv)
        rmse_adv = np.sqrt(mean_squared_error(y_test_adv, preds_adv))

        print(f"  --> Advanced Model (After FE):  MAE = {mae_adv:.3f} | RMSE = {rmse_adv:.3f}")

        # Calculate Improvement Percentages
        mae_imp_pct = ((mae_base - mae_adv) / mae_base) * 100.0
        rmse_imp_pct = ((rmse_base - rmse_adv) / rmse_base) * 100.0

        # ----------------------------------------------------
        # 3. LOG METRICS TO MLFLOW
        # ----------------------------------------------------
        mlflow.log_param("n_estimators_base", 100)
        mlflow.log_param("n_estimators_adv", 200)
        mlflow.log_param("learning_rate_adv", 0.03)

        mlflow.log_metric("mae_before_fe", mae_base)
        mlflow.log_metric("rmse_before_fe", rmse_base)
        mlflow.log_metric("mae_after_fe", mae_adv)
        mlflow.log_metric("rmse_after_fe", rmse_adv)
        mlflow.log_metric("mae_improvement_pct", mae_imp_pct)
        mlflow.log_metric("rmse_improvement_pct", rmse_imp_pct)

        # ----------------------------------------------------
        # 4. SAVE MODEL & METADATA ARTIFACTS
        # ----------------------------------------------------
        machine_mapping = {m: i for i, m in enumerate(df_raw["machine_id"].unique())}
        product_mapping = {p: i for i, p in enumerate(df_raw["product_id"].unique())}

        model_bundle = {
            "model": model_adv,
            "features": features_adv,
            "machine_mapping": machine_mapping,
            "product_mapping": product_mapping,
            "metrics": {
                "mae_before_fe": round(mae_base, 3),
                "rmse_before_fe": round(rmse_base, 3),
                "mae_after_fe": round(mae_adv, 3),
                "rmse_after_fe": round(rmse_adv, 3),
                "mae_improvement_pct": round(mae_imp_pct, 2),
                "rmse_improvement_pct": round(rmse_imp_pct, 2)
            },
            "last_historical_date": df_raw["date"].max(),
            "raw_dataset": df_adv
        }

        save_path = MODELS_DIR / "forecast_model.pkl"
        with open(save_path, "wb") as f:
            pickle.dump(model_bundle, f)

        print("\n" + "=" * 70)
        print("📊 BACKTEST EVALUATION SUMMARY")
        print("=" * 70)
        print(f"  Stage                        | Backtest MAE | Backtest RMSE")
        print(f"  -----------------------------+--------------+--------------")
        print(f"  1. Before FE (Baseline)      | {mae_base:<12.3f} | {rmse_base:<12.3f}")
        print(f"  2. After FE (Advanced LGBM)  | {mae_adv:<12.3f} | {rmse_adv:<12.3f}")
        print(f"  -----------------------------+--------------+--------------")
        print(f"  🎯 Improvement               | {mae_imp_pct:<11.2f}% | {rmse_imp_pct:<11.2f}%")
        print("=" * 70)
        print(f"💾 Model Bundle Artifact saved to: {save_path}")

        return model_bundle

if __name__ == "__main__":
    train_and_evaluate()
