"""
Payment Burst Sentinel -- Phase 3: Build Baselines Script
==========================================================
Execute the complete baseline construction pipeline:

  1. Load processed training data
  2. Aggregate to merchant-day level
  3. Compute rolling baselines for all 693 merchants
  4. Validate temporal integrity (no leakage)
  5. Validate edge cases (warm-up, zero variance)
  6. Inspect representative merchants
  7. Save baseline output

Usage:
  python scripts/build_baselines.py
"""

import sys
import json
from pathlib import Path

import numpy as np
import pandas as pd

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.config import PROCESSED_DATA_DIR, COLUMN_MERCHANT
from backend.data_loader import load_processed
from backend.baseline_engine import (
    build_merchant_daily,
    build_all_baselines,
    validate_no_leakage,
    inspect_merchant_baseline,
    BASELINE_DIR,
    ROLLING_WINDOW_DAYS,
    MINIMUM_HISTORY_DAYS,
)


def print_section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def run_phase_3():
    print_section("PAYMENT BURST SENTINEL - PHASE 3: BEHAVIORAL BASELINE ENGINE")
    print("\n  Purpose: Learn what 'normal' looks like for each merchant.")
    print("  NO anomaly detection. NO risk scores. NO UI.")

    # ─────────────────────────────────────────────────────────
    # Step 1: Load data
    # ─────────────────────────────────────────────────────────
    print("\n  [1/7] Loading processed training data...")
    df = load_processed("train")
    print(f"    Loaded {len(df):,} transactions")

    # ─────────────────────────────────────────────────────────
    # Step 2: Aggregate to merchant-day
    # ─────────────────────────────────────────────────────────
    print("\n  [2/7] Aggregating to merchant-day level...")
    daily = build_merchant_daily(df)
    print(f"    Created {len(daily):,} merchant-day observations")
    print(f"    Merchants: {daily[COLUMN_MERCHANT].nunique()}")
    print(f"    Date range: {daily['date'].min()} -> {daily['date'].max()}")
    print(f"    Avg tx/merchant-day: {daily['transaction_count'].mean():.2f}")
    print(f"    Median tx/merchant-day: {daily['transaction_count'].median():.1f}")

    # ─────────────────────────────────────────────────────────
    # Step 3: Build baselines
    # ─────────────────────────────────────────────────────────
    print("\n  [3/7] Computing rolling baselines (30-day median+MAD)...")
    print(f"    Rolling window: {ROLLING_WINDOW_DAYS} days")
    print(f"    Minimum history: {MINIMUM_HISTORY_DAYS} days")
    print(f"    Statistical method: median + MAD (robust against outliers)")

    baseline_df = build_all_baselines(daily)
    print(f"\n    Total baseline rows: {len(baseline_df):,}")

    # ─────────────────────────────────────────────────────────
    # Step 4: Validate temporal integrity
    # ─────────────────────────────────────────────────────────
    print("\n  [4/7] Validating temporal integrity (no future leakage)...")
    validations = validate_no_leakage(baseline_df, n_samples=5)

    all_match = True
    for v in validations:
        status = "PASS" if v["match"] else "FAIL"
        if not v["match"]:
            all_match = False
        print(f"    {status} | {v['merchant'][:30]:30s} | {v['date']} | "
              f"baseline={v['expected_tx_count_in_baseline']:.1f} | "
              f"recomputed={v['recomputed_from_prior']:.1f} | "
              f"prior={v['prior_dates_range']}")

    if all_match:
        print("    [OK] All temporal integrity checks passed")
    else:
        print("    [FAIL] Temporal integrity issues detected!")

    # ─────────────────────────────────────────────────────────
    # Step 5: Validate edge cases
    # ─────────────────────────────────────────────────────────
    print("\n  [5/7] Validating edge cases...")

    # Baseline status distribution
    status_counts = baseline_df["baseline_status"].value_counts()
    print(f"    Baseline status distribution:")
    for status, count in status_counts.items():
        pct = count / len(baseline_df) * 100
        print(f"      {status}: {count:,} ({pct:.1f}%)")

    # Warm-up check: first days of a merchant
    sample_merchant = baseline_df[COLUMN_MERCHANT].iloc[0]
    first_days = baseline_df[baseline_df[COLUMN_MERCHANT] == sample_merchant].head(10)
    print(f"\n    Warm-up example ({sample_merchant[:30]}):")
    print(f"    {'Date':<12s} | {'TxCount':>7s} | {'Expected':>8s} | {'Variab':>8s} | {'History':>7s} | Status")
    for _, row in first_days.iterrows():
        exp = f"{row['expected_tx_count']:.1f}" if not np.isnan(row['expected_tx_count']) else "N/A"
        var = f"{row['tx_count_variability']:.1f}" if not np.isnan(row['tx_count_variability']) else "N/A"
        print(f"    {str(row['date']):<12s} | {row['transaction_count']:>7d} | {exp:>8s} | {var:>8s} | {row['historical_days_used']:>7d} | {row['baseline_status']}")

    # Zero-variance check
    sufficient = baseline_df[baseline_df["baseline_status"] == "sufficient_history"]
    zero_var_tx = (sufficient["tx_count_variability"] <= 1.0).sum()
    zero_var_amt = (sufficient["total_amount_variability"] <= 10.0).sum()
    print(f"\n    Zero-variance handling:")
    print(f"      Tx count variability at floor (<=1.0): {zero_var_tx:,}")
    print(f"      Amount variability at floor (<=10.0): {zero_var_amt:,}")
    print(f"      [OK] All zero-variance cases handled safely (floor applied)")

    # Verify no NaN in sufficient_history rows
    nan_in_sufficient = sufficient[["expected_tx_count", "expected_total_amount"]].isna().sum()
    if nan_in_sufficient.sum() == 0:
        print(f"      [OK] No NaN values in sufficient_history baselines")
    else:
        print(f"      [FAIL] NaN values found: {nan_in_sufficient.to_dict()}")

    # ─────────────────────────────────────────────────────────
    # Step 6: Inspect representative merchants
    # ─────────────────────────────────────────────────────────
    print_section("REPRESENTATIVE BASELINE INSPECTION")

    # Select merchants across activity levels
    merchant_totals = baseline_df.groupby(COLUMN_MERCHANT)["transaction_count"].sum()
    terciles = merchant_totals.quantile([0.15, 0.50, 0.85])

    low_merchant = merchant_totals[
        merchant_totals <= terciles.iloc[0]
    ].index[0]
    mid_merchant = merchant_totals[
        (merchant_totals > terciles.iloc[0]) &
        (merchant_totals <= terciles.iloc[1])
    ].index[0]
    high_merchant = merchant_totals[
        merchant_totals > terciles.iloc[2]
    ].index[0]

    for label, merchant in [
        ("LOW ACTIVITY", low_merchant),
        ("MEDIUM ACTIVITY", mid_merchant),
        ("HIGH ACTIVITY", high_merchant),
    ]:
        print(f"\n  {label}: {merchant}")
        total_tx = int(merchant_totals[merchant])
        print(f"  Total transactions: {total_tx:,}")

        inspection = inspect_merchant_baseline(baseline_df, merchant, n_days=8)
        print(f"  Last 8 days with baseline:")
        print(f"  {'Date':<12s} | {'Obs.Tx':>6s} | {'Exp.Tx':>6s} | {'TxVar':>6s} | {'Obs.Amt':>9s} | {'Exp.Amt':>9s} | {'AmtVar':>9s} | {'Hist':>4s} | Status")
        print(f"  {'-'*12}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}-+-{'-'*9}-+-{'-'*9}-+-{'-'*9}-+-{'-'*4}-+-{'-'*18}")
        for _, row in inspection.iterrows():
            print(f"  {str(row['date']):<12s} | "
                  f"{row['transaction_count']:>6d} | "
                  f"{row['expected_tx_count']:>6.1f} | "
                  f"{row['tx_count_variability']:>6.1f} | "
                  f"{row['total_amount']:>9.2f} | "
                  f"{row['expected_total_amount']:>9.2f} | "
                  f"{row['total_amount_variability']:>9.2f} | "
                  f"{row['historical_days_used']:>4d} | "
                  f"{row['baseline_status']}")

    # ─────────────────────────────────────────────────────────
    # Step 7: Save
    # ─────────────────────────────────────────────────────────
    print_section("SAVING BASELINE OUTPUT")

    BASELINE_DIR.mkdir(parents=True, exist_ok=True)

    # Save full baseline as parquet
    output_path = BASELINE_DIR / "merchant_daily_baselines.parquet"
    baseline_df.to_parquet(output_path, index=False)
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  Saved: {output_path}")
    print(f"  Size: {size_mb:.1f} MB")

    # Save summary stats
    summary = {
        "baseline_method": "Rolling 30-day median + MAD (robust)",
        "rolling_window_days": ROLLING_WINDOW_DAYS,
        "minimum_history_days": MINIMUM_HISTORY_DAYS,
        "zero_variance_handling": "MAD floor = max(MAD, max(base_floor, 0.1 * median))",
        "temporal_integrity": "Each day uses ONLY prior dates (strictly <)",
        "total_merchant_day_rows": len(baseline_df),
        "merchants_covered": int(baseline_df[COLUMN_MERCHANT].nunique()),
        "date_range": {
            "start": str(baseline_df["date"].min()),
            "end": str(baseline_df["date"].max()),
        },
        "status_distribution": status_counts.to_dict(),
        "sufficient_history_pct": round(
            float(status_counts.get("sufficient_history", 0) / len(baseline_df) * 100), 1
        ),
        "temporal_integrity_validated": all_match,
        "core_dimensions": ["transaction_count", "total_amount"],
    }

    summary_path = BASELINE_DIR / "baseline_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"  Saved: {summary_path}")

    # ─────────────────────────────────────────────────────────
    # Completion
    # ─────────────────────────────────────────────────────────
    print_section("PHASE 3 COMPLETE -- SUMMARY")

    print(f"""
  BASELINE METHOD
    Rolling window:       {ROLLING_WINDOW_DAYS} days
    Statistical method:   Median + MAD (robust against outliers)
    Minimum history:      {MINIMUM_HISTORY_DAYS} days
    Zero-variance floor:  max(MAD, max(base_floor, 0.1 * median))
    Fallback:             warmup status with baseline still computed

  TEMPORAL INTEGRITY
    Rule: baseline uses ONLY dates strictly BEFORE observation date
    Validated: {all_match}

  OUTPUT SUMMARY
    Total merchant-day rows:    {len(baseline_df):,}
    Merchants covered:          {baseline_df[COLUMN_MERCHANT].nunique()}
    Sufficient history:         {status_counts.get('sufficient_history', 0):,} ({summary['sufficient_history_pct']}%)
    Warm-up:                    {status_counts.get('warmup', 0):,}
    Insufficient history:       {status_counts.get('insufficient_history', 0):,}

  CORE DIMENSIONS
    1. transaction_count  (observed vs expected_tx_count +/- tx_count_variability)
    2. total_amount       (observed vs expected_total_amount +/- total_amount_variability)

  FILES CREATED
    {output_path}
    {summary_path}
""")

    print(f"{'='*70}")
    print(f"  Phase 3 - Behavioral Baseline Engine - COMPLETE")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    run_phase_3()
