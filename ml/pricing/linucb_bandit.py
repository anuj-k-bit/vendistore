#!/usr/bin/env python3
"""
IntelliVend Dynamic Pricing - LinUCB Contextual Bandit Model
Selects optimal price multiplier arm (0.85x, 0.95x, 1.00x, 1.10x, 1.15x) given slot context.
Learns online from purchase conversion feedback (reward = revenue generated).
"""

import os
import json
import pickle
import numpy as np
from pathlib import Path

MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

class LinUCBPricingBandit:
    def __init__(self, arms=[0.85, 0.95, 1.00, 1.10, 1.15], alpha=0.5, d=6):
        self.arms = arms # Available price multiplier arms
        self.k = len(arms)
        self.alpha = alpha # Exploration parameter
        self.d = d # Context vector dimension

        # Initialize A_a matrix (d x d) and b_a vector (d x 1) for each arm
        self.A = [np.identity(self.d) for _ in range(self.k)]
        self.b = [np.zeros((self.d, 1)) for _ in range(self.k)]

    def construct_context(self, stock_ratio: float, hour_of_day: int, predicted_demand: float, is_weekend: int, base_price: float):
        """Constructs 6-dimensional normalized context vector x_t."""
        x = np.array([
            float(stock_ratio),
            float(hour_of_day / 24.0),
            float(min(1.0, predicted_demand / 30.0)),
            float(is_weekend),
            float(min(1.0, base_price / 5.0)),
            1.0 # Bias feature
        ]).reshape((self.d, 1))
        return x

    def select_arm(self, context_vector):
        """Calculates LinUCB scores for all arms and returns selected arm and multiplier."""
        x = context_vector
        p = np.zeros(self.k)
        confidence_bounds = np.zeros(self.k)

        for a in range(self.k):
            A_inv = np.linalg.inv(self.A[a])
            theta_a = A_inv.dot(self.b[a])
            
            # Variance estimate
            var = np.sqrt(x.T.dot(A_inv).dot(x))[0, 0]
            ucb = self.alpha * var
            
            p[a] = float(theta_a.T.dot(x)[0, 0] + ucb)
            confidence_bounds[a] = float(ucb)

        selected_arm_idx = int(np.argmax(p))
        selected_multiplier = self.arms[selected_arm_idx]

        return {
            "arm_index": selected_arm_idx,
            "multiplier": selected_multiplier,
            "ucb_score": round(float(p[selected_arm_idx]), 4),
            "confidence_bound": round(float(confidence_bounds[selected_arm_idx]), 4),
            "all_ucb_scores": [round(float(s), 4) for s in p]
        }

    def update(self, arm_index: int, context_vector, reward: float):
        """Online ridge regression update based on customer conversion reward."""
        x = context_vector
        self.A[arm_index] += x.dot(x.T)
        self.b[arm_index] += reward * x

    def save_model(self, filepath=None):
        if filepath is None:
            filepath = MODEL_DIR / "linucb_bandit.pkl"
        with open(filepath, "wb") as f:
            pickle.dump({
                "arms": self.arms,
                "alpha": self.alpha,
                "d": self.d,
                "A": self.A,
                "b": self.b
            }, f)

    @classmethod
    def load_model(cls, filepath=None):
        if filepath is None:
            filepath = MODEL_DIR / "linucb_bandit.pkl"
        if not Path(filepath).exists():
            instance = cls()
            instance.save_model(filepath)
            return instance

        with open(filepath, "rb") as f:
            data = pickle.load(f)

        instance = cls(arms=data["arms"], alpha=data["alpha"], d=data["d"])
        instance.A = data["A"]
        instance.b = data["b"]
        return instance

if __name__ == "__main__":
    bandit = LinUCBPricingBandit()
    ctx = bandit.construct_context(stock_ratio=0.2, hour_of_day=13, predicted_demand=22.0, is_weekend=0, base_price=3.50)
    choice = bandit.select_arm(ctx)
    print("LinUCB Selected Arm:", choice)
