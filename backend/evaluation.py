"""
Payment Burst Sentinel -- Phase 5: Honest Evaluation & Held-Out Validation
============================================================================
PURPOSE: Evaluate the FROZEN Phase 4 detector on unseen test data.

CORE QUESTION: Does the frozen behavioral anomaly detector provide
meaningful signal on unseen data?

RULES:
  - Frozen policy: do NOT change thresholds, signals, or methodology
  - Fraud labels used ONLY for evaluation, never for tuning
  - Anomaly != fraud — maintain this distinction
  - Report honestly, even if results are unfavorable

EVALUATION FRAMEWORK:
  1. Build test baselines with temporal continuity from training
  2. Apply frozen detector unchanged
  3. Measure fraud enrichment (not classification accuracy)
  4. Analyze signal contributions
  5. Failure analysis
  6. Honest verdict
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple

from backend.config import (
    PROCESSED_DATA_DIR,
    COLUMN_MERCHANT,
    COLUMN_TIMESTAMP,
    COLUMN_AMOUNT,
    COLUMN_IS_FRAUD,
)
from backend.baseline_engine import (
    build_merchant_daily,
    compute_rolling_baseline,
    ROLLING_WINDOW_DAYS,
    MINIMUM_HISTORY_DAYS,
)
from backend.anomaly_detector import (
    compute_deviation_scores,
    classify_anomalies,
)

EVALUATION_DIR = PROCESSED_DATA_DIR / "evaluation"
BASELINE_DIR = PROCESSED_DATA_DIR / "baselines"


def build_test_baselines(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build baselines for test-period merchant-days using temporal continuity.

    For each merchant:
      1. Get the merchant's training-period daily aggregates
      2. Get the merchant's test-period daily aggregates
      3. Concatenate in temporal order
      4. Compute rolling baselines for the full sequence
      5. Extract only test-period rows

    This ensures test baselines use genuine prior history (training data
    + earlier test days) without any future leakage.

    Fraud labels are NEVER used in baseline construction — only
    transaction_count and total_amount drive the baseline.
    """
    # Aggregate both to merchant-day
    train_daily = build_merchant_daily(train_df)
    test_daily = build_merchant_daily(test_df)

    # Mark origin for later separation
    train_daily["_period"] = "train"
    test_daily["_period"] = "test"

    # Process per merchant
    results = []
    merchants = test_daily[COLUMN_MERCHANT].unique()
    total = len(merchants)

    for idx, merchant in enumerate(merchants):
        # Get training history for this merchant
        m_train = train_daily[train_daily[COLUMN_MERCHANT] == merchant].copy()
        m_test = test_daily[test_daily[COLUMN_MERCHANT] == merchant].copy()

        # Concatenate: training history + test period
        combined = pd.concat([m_train, m_test], ignore_index=True)
        combined = combined.sort_values("date").reset_index(drop=True)

        # Compute rolling baseline for the full sequence
        baseline = compute_rolling_baseline(combined)

        # Extract only test-period rows
        test_rows = baseline[baseline["_period"] == "test"].copy()
        test_rows = test_rows.drop(columns=["_period"])
        results.append(test_rows)

        if (idx + 1) % 100 == 0 or idx == total - 1:
            print(f"    Test baselines: {idx+1}/{total} merchants")

    # Also drop _period from any remaining
    result = pd.concat(results, ignore_index=True)
    if "_period" in result.columns:
        result = result.drop(columns=["_period"])

    return result


def compute_enrichment(
    flagged_fraud_rate: float,
    baseline_fraud_rate: float,
) -> float:
    """
    Enrichment ratio: how much more likely flagged days contain fraud
    compared to the baseline rate.
    """
    if baseline_fraud_rate == 0:
        return float("inf") if flagged_fraud_rate > 0 else 1.0
    return flagged_fraud_rate / baseline_fraud_rate


def volume_only_baseline(test_anomaly_df: pd.DataFrame, n_flags: int) -> dict:
    """
    Simple baseline: flag the top-N highest-volume merchant-days.
    This answers: does merchant-specific behavioral context add value
    beyond just flagging high-activity days?
    """
    sufficient = test_anomaly_df[
        test_anomaly_df["baseline_status"] == "sufficient_history"
    ].copy()

    # Flag top-N by raw transaction count
    threshold = sufficient["transaction_count"].nlargest(n_flags).min()
    volume_flagged = sufficient[sufficient["transaction_count"] >= threshold]

    fraud_rate_flagged = (volume_flagged["fraud_count"] > 0).mean()
    fraud_rate_normal = (
        sufficient[sufficient["transaction_count"] < threshold]["fraud_count"] > 0
    ).mean()

    return {
        "method": f"Top-{n_flags} highest daily tx count",
        "flagged_count": len(volume_flagged),
        "fraud_containing_rate_flagged": round(float(fraud_rate_flagged * 100), 3),
        "fraud_containing_rate_normal": round(float(fraud_rate_normal * 100), 3),
        "enrichment_vs_normal": round(
            float(compute_enrichment(fraud_rate_flagged, fraud_rate_normal)), 2
        ),
    }
