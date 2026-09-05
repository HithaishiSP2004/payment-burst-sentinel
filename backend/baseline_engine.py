"""
Payment Burst Sentinel -- Phase 3: Behavioral Baseline Engine
==============================================================
PURPOSE: Learn what "normal" looks like for each merchant.

For every merchant-day, answer:
  "Based only on historical data preceding this day, what activity
   would normally be expected for this merchant?"

This module does NOT:
  - detect anomalies
  - assign risk scores
  - predict fraud
  - build UI

CORE DIMENSIONS (from Phase 2):
  1. Daily transaction count
  2. Daily total transaction amount

BASELINE METHOD:
  Rolling 30-day history per merchant.
  Robust statistics: median + MAD (median absolute deviation)
  for resilience against outliers.

TEMPORAL INTEGRITY:
  A day's baseline uses ONLY data from dates strictly BEFORE that day.
  No future leakage. No same-day inclusion.

WARM-UP HANDLING:
  - minimum_history = 7 days
  - Days with < 7 prior observations: status = "warmup"
  - Days with >= 7 prior observations: status = "sufficient_history"
  - Days with 0 prior observations: status = "insufficient_history"

ZERO-VARIANCE HANDLING:
  When MAD = 0 (all prior values identical), use a floor value:
  floor = max(1.0, 0.1 * median) to prevent division-by-zero
  and produce interpretable deviation measures.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional

from backend.config import (
    PROCESSED_DATA_DIR,
    COLUMN_TIMESTAMP,
    COLUMN_MERCHANT,
    COLUMN_AMOUNT,
    COLUMN_IS_FRAUD,
    COLUMN_CATEGORY,
)

# =====================================================================
# Configuration
# =====================================================================

ROLLING_WINDOW_DAYS = 30
MINIMUM_HISTORY_DAYS = 7

# Baseline output directory
BASELINE_DIR = PROCESSED_DATA_DIR / "baselines"


# =====================================================================
# Step 1: Aggregate to merchant-day level
# =====================================================================

def build_merchant_daily(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate transaction-level data to merchant-day observations.

    For each merchant-day, compute:
      - transaction_count: number of transactions
      - total_amount: sum of transaction amounts
      - avg_amount: mean transaction amount (derived, for inspection)
      - fraud_count: number of fraud-labelled transactions (metadata only)
      - day_of_week: 0=Monday through 6=Sunday
    """
    # Ensure date column exists
    if "date" not in df.columns:
        df = df.copy()
        df["date"] = pd.to_datetime(df[COLUMN_TIMESTAMP]).dt.date

    daily = df.groupby([COLUMN_MERCHANT, "date"]).agg(
        transaction_count=(COLUMN_AMOUNT, "count"),
        total_amount=(COLUMN_AMOUNT, "sum"),
        avg_amount=(COLUMN_AMOUNT, "mean"),
        fraud_count=(COLUMN_IS_FRAUD, "sum"),
    ).reset_index()

    # Add day of week
    daily["day_of_week"] = pd.to_datetime(daily["date"]).dt.dayofweek

    # Sort by merchant and date for temporal ordering
    daily = daily.sort_values([COLUMN_MERCHANT, "date"]).reset_index(drop=True)

    return daily


# =====================================================================
# Step 2: Compute rolling baselines
# =====================================================================

def compute_rolling_baseline(merchant_daily: pd.DataFrame) -> pd.DataFrame:
    """
    For a SINGLE merchant's daily data (already sorted by date),
    compute the rolling baseline using only prior observations.

    For each day:
      - Look back up to ROLLING_WINDOW_DAYS prior days
      - Compute median and MAD of transaction_count and total_amount
      - Record how many historical days were used
      - Assign baseline_status

    Returns a DataFrame with baseline columns added.

    TEMPORAL INTEGRITY: Each row's baseline uses ONLY rows with
    earlier dates (strictly < current date).
    """
    n = len(merchant_daily)
    dates = merchant_daily["date"].values
    tx_counts = merchant_daily["transaction_count"].values.astype(float)
    total_amounts = merchant_daily["total_amount"].values.astype(float)

    # Pre-allocate output arrays
    expected_tx_count = np.full(n, np.nan)
    tx_count_variability = np.full(n, np.nan)
    expected_total_amount = np.full(n, np.nan)
    total_amount_variability = np.full(n, np.nan)
    historical_days_used = np.zeros(n, dtype=int)
    baseline_status = ["insufficient_history"] * n

    for i in range(n):
        current_date = dates[i]

        # Find prior observations: dates strictly before current date
        # and within the rolling window
        if i == 0:
            prior_mask = np.array([], dtype=bool)
        else:
            prior_dates = dates[:i]
            # Convert to comparable format
            current_dt = pd.Timestamp(current_date)
            cutoff_dt = current_dt - pd.Timedelta(days=ROLLING_WINDOW_DAYS)
            prior_mask = np.array([
                pd.Timestamp(d) >= cutoff_dt for d in prior_dates
            ])

        if prior_mask.sum() == 0:
            historical_days_used[i] = 0
            baseline_status[i] = "insufficient_history"
            continue

        prior_tx = tx_counts[:i][prior_mask]
        prior_amt = total_amounts[:i][prior_mask]
        n_prior = len(prior_tx)
        historical_days_used[i] = n_prior

        if n_prior < MINIMUM_HISTORY_DAYS:
            baseline_status[i] = "warmup"
        else:
            baseline_status[i] = "sufficient_history"

        # Compute robust baseline: median + MAD
        # Transaction count
        median_tx = float(np.median(prior_tx))
        mad_tx = float(np.median(np.abs(prior_tx - median_tx)))

        # Apply MAD floor to prevent zero-variance issues
        # Floor = max(1.0, 0.1 * median) ensures minimum variability
        mad_tx_safe = max(mad_tx, max(1.0, 0.1 * median_tx))

        expected_tx_count[i] = median_tx
        tx_count_variability[i] = mad_tx_safe

        # Total amount
        median_amt = float(np.median(prior_amt))
        mad_amt = float(np.median(np.abs(prior_amt - median_amt)))

        # Floor for amount: max(10.0, 0.1 * median)
        mad_amt_safe = max(mad_amt, max(10.0, 0.1 * abs(median_amt)))

        expected_total_amount[i] = median_amt
        total_amount_variability[i] = mad_amt_safe

    # Add columns to dataframe
    result = merchant_daily.copy()
    result["expected_tx_count"] = expected_tx_count
    result["tx_count_variability"] = tx_count_variability
    result["expected_total_amount"] = expected_total_amount
    result["total_amount_variability"] = total_amount_variability
    result["historical_days_used"] = historical_days_used
    result["baseline_window_days"] = ROLLING_WINDOW_DAYS
    result["baseline_status"] = baseline_status

    return result


def build_all_baselines(daily: pd.DataFrame) -> pd.DataFrame:
    """
    Build rolling baselines for ALL merchants.

    Groups by merchant, computes per-merchant rolling baseline,
    then concatenates results.
    """
    results = []
    merchants = daily[COLUMN_MERCHANT].unique()
    total = len(merchants)

    for idx, merchant in enumerate(merchants):
        merchant_data = daily[daily[COLUMN_MERCHANT] == merchant].copy()
        merchant_data = merchant_data.sort_values("date").reset_index(drop=True)

        baseline = compute_rolling_baseline(merchant_data)
        results.append(baseline)

        if (idx + 1) % 100 == 0 or idx == total - 1:
            print(f"    Baseline computed: {idx+1}/{total} merchants")

    return pd.concat(results, ignore_index=True)


# =====================================================================
# Step 3: Validation utilities
# =====================================================================

def validate_no_leakage(baseline_df: pd.DataFrame, n_samples: int = 5) -> list:
    """
    Verify temporal integrity: for sampled rows, confirm that the
    baseline was computed from dates strictly before the observation date,
    using the same 30-calendar-day window as the engine.

    Returns list of validation results.
    """
    validations = []
    sample = baseline_df[
        baseline_df["baseline_status"] == "sufficient_history"
    ].sample(n=min(n_samples, len(baseline_df)), random_state=42)

    for _, row in sample.iterrows():
        merchant = row[COLUMN_MERCHANT]
        obs_date = row["date"]

        # Replicate the engine's exact logic:
        # prior dates = dates strictly before obs_date AND within 30 calendar days
        import datetime
        if isinstance(obs_date, datetime.date):
            cutoff_date = obs_date - datetime.timedelta(days=ROLLING_WINDOW_DAYS)
        else:
            cutoff_date = pd.Timestamp(obs_date) - pd.Timedelta(days=ROLLING_WINDOW_DAYS)
            cutoff_date = cutoff_date.date() if hasattr(cutoff_date, "date") else cutoff_date

        merchant_data = baseline_df[
            (baseline_df[COLUMN_MERCHANT] == merchant) &
            (baseline_df["date"] < obs_date) &
            (baseline_df["date"] >= cutoff_date)
        ]

        if len(merchant_data) > 0:
            # Verify the expected values match what we'd compute from prior data
            prior_tx = merchant_data["transaction_count"].values
            recomputed_median = float(np.median(prior_tx))

            validations.append({
                "merchant": merchant,
                "date": str(obs_date),
                "expected_tx_count_in_baseline": row["expected_tx_count"],
                "recomputed_from_prior": recomputed_median,
                "match": abs(row["expected_tx_count"] - recomputed_median) < 0.01,
                "prior_dates_range": f"{merchant_data['date'].min()} to {merchant_data['date'].max()}",
                "historical_days": int(row["historical_days_used"]),
                "prior_rows_used": len(merchant_data),
            })

    return validations


def inspect_merchant_baseline(
    baseline_df: pd.DataFrame,
    merchant: str,
    n_days: int = 10,
) -> pd.DataFrame:
    """
    Show baseline inspection for a specific merchant.
    Returns last n_days of baseline data.
    """
    m_data = baseline_df[baseline_df[COLUMN_MERCHANT] == merchant].tail(n_days)
    display_cols = [
        "date", "transaction_count", "expected_tx_count", "tx_count_variability",
        "total_amount", "expected_total_amount", "total_amount_variability",
        "historical_days_used", "baseline_status", "day_of_week",
    ]
    return m_data[display_cols]
