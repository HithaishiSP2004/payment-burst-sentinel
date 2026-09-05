"""
Payment Burst Sentinel — Phase 1: Data Processing Script
=========================================================
Run this script to execute the complete Phase 1 pipeline:

  1. Load and clean fraudTrain.csv
  2. Load and clean fraudTest.csv
  3. Validate data quality for both
  4. Save processed parquet files
  5. Print comprehensive validation report

Usage:
  python scripts/process_data.py

Output:
  data/processed/train_clean.parquet
  data/processed/test_clean.parquet
"""

import sys
import json
from pathlib import Path

# Add project root to path so we can import backend modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.config import TRAIN_CSV, TEST_CSV, PROCESSED_DATA_DIR
from backend.data_loader import process_dataset


def print_separator(title: str = ""):
    """Print a visual separator for readability."""
    print(f"\n{'='*70}")
    if title:
        print(f"  {title}")
        print(f"{'='*70}")


def run_phase_1():
    """Execute the complete Phase 1 data processing pipeline."""

    print_separator("PAYMENT BURST SENTINEL - PHASE 1: DATA LOADING & PREPROCESSING")
    print()
    print("Following the constitution:")
    print("  1. Load datasets")
    print("  2. Clean merchant names")
    print("  3. Parse timestamps")
    print("  4. Select relevant columns")
    print("  5. Validate data quality")
    print("  6. Save processed output")
    print()
    print("NO detection logic. NO baselines. NO UI.")

    # ─────────────────────────────────────────────────────────
    # Process Training Data
    # ─────────────────────────────────────────────────────────

    train_df, train_report = process_dataset(
        filepath=TRAIN_CSV,
        dataset_name="train",
        save=True,
    )

    # ─────────────────────────────────────────────────────────
    # Process Test Data (held-out — do not use for development)
    # ─────────────────────────────────────────────────────────

    test_df, test_report = process_dataset(
        filepath=TEST_CSV,
        dataset_name="test",
        save=True,
    )

    # ─────────────────────────────────────────────────────────
    # Cross-dataset Consistency Check
    # ─────────────────────────────────────────────────────────

    print_separator("CROSS-DATASET CONSISTENCY CHECK")

    # Column match
    train_cols = set(train_df.columns)
    test_cols = set(test_df.columns)
    if train_cols == test_cols:
        print("  [OK] Column schemas match between train and test")
    else:
        diff = train_cols.symmetric_difference(test_cols)
        print(f"  [!] Column mismatch: {diff}")

    # Merchant overlap
    train_merchants = set(train_df["merchant"].unique())
    test_merchants = set(test_df["merchant"].unique())
    overlap = train_merchants & test_merchants
    train_only = train_merchants - test_merchants
    test_only = test_merchants - train_merchants
    print(f"  Merchants in train: {len(train_merchants)}")
    print(f"  Merchants in test:  {len(test_merchants)}")
    print(f"  Overlap:            {len(overlap)}")
    if train_only:
        print(f"  Train-only:         {len(train_only)}")
    if test_only:
        print(f"  Test-only:          {len(test_only)}")

    # Category overlap
    train_cats = set(train_df["category"].unique())
    test_cats = set(test_df["category"].unique())
    if train_cats == test_cats:
        print(f"  [OK] All {len(train_cats)} categories present in both datasets")
    else:
        print(f"  [!] Category mismatch")

    # Time range check (train should precede test for proper held-out evaluation)
    train_end = train_df["trans_date_trans_time"].max()
    test_start = test_df["trans_date_trans_time"].min()
    print(f"  Train ends:   {train_end}")
    print(f"  Test starts:  {test_start}")
    if train_end < test_start:
        print(f"  [OK] Clean temporal separation — no data leakage risk")
    else:
        print(f"  [!] Temporal overlap detected — handle carefully in later phases")

    # ─────────────────────────────────────────────────────────
    # Phase 1 Summary
    # ─────────────────────────────────────────────────────────

    print_separator("PHASE 1 COMPLETE — SUMMARY")

    print(f"""
  TRAINING DATA
    Rows:       {len(train_df):,}
    Columns:    {len(train_df.columns)}
    Merchants:  {train_df['merchant'].nunique()}
    Categories: {train_df['category'].nunique()}
    Fraud rate: {train_report['class_balance']['fraud_rate_pct']}%
    Time span:  {train_report['time_range']['start']} -> {train_report['time_range']['end']}
    Duration:   {train_report['time_range']['duration_days']} days

  TEST DATA (HELD-OUT)
    Rows:       {len(test_df):,}
    Columns:    {len(test_df.columns)}
    Merchants:  {test_df['merchant'].nunique()}
    Categories: {test_df['category'].nunique()}
    Fraud rate: {test_report['class_balance']['fraud_rate_pct']}%
    Time span:  {test_report['time_range']['start']} -> {test_report['time_range']['end']}
    Duration:   {test_report['time_range']['duration_days']} days

  OUTPUT FILES
    {PROCESSED_DATA_DIR / 'train_clean.parquet'}
    {PROCESSED_DATA_DIR / 'test_clean.parquet'}

  DATA QUALITY
    Missing values:  {'None' if not train_report['has_missing'] else 'Found'}
    Schema match:    {'Yes' if train_cols == test_cols else 'No'}

  ASSUMPTIONS DOCUMENTED
    1. Dataset is Kaggle synthetic fraud data, not Razorpay production data.
    2. "fraud_" prefix stripped from merchant names (dataset artifact).
    3. Transaction-level is_fraud labels exist; burst-level labels do not.
    4. PII columns dropped (name, address, job, DOB) — irrelevant to burst detection.
    5. Temporal components (hour, day_of_week, date) extracted for later phases.

  READY FOR PHASE 2
    The clean, validated data is available for exploratory analysis
    and baseline construction in subsequent phases.
""")

    # Save reports as JSON for programmatic access
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name, report in [("train", train_report), ("test", test_report)]:
        report_path = PROCESSED_DATA_DIR / f"{name}_validation_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"  Validation report saved: {report_path}")

    print(f"\n{'='*70}")
    print(f"  Phase 1 - Data Loading & Preprocessing - COMPLETE")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    run_phase_1()
