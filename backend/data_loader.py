"""
Payment Burst Sentinel — Data Loader
=====================================
Phase 1: Load, clean, validate, and prepare raw transaction data.

This module handles:
  1. CSV ingestion from raw data files
  2. Column selection (drop PII and irrelevant columns)
  3. Merchant name cleaning (strip synthetic "fraud_" prefix)
  4. Timestamp parsing and validation
  5. Data quality checks (missing values, types, ranges)
  6. Export of clean processed data

Assumptions documented per constitution requirement:
  - Dataset is Kaggle synthetic fraud data, NOT real Razorpay production data
  - "fraud_" prefix on merchant names is a dataset artifact, not meaningful
  - Transaction-level is_fraud labels exist but burst-level labels do not
  - Timestamps have second-level precision
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

from backend.config import (
    TRAIN_CSV,
    TEST_CSV,
    PROCESSED_DATA_DIR,
    RETAINED_COLUMNS,
    EXCLUDED_COLUMNS,
    COLUMN_TIMESTAMP,
    COLUMN_UNIX_TIME,
    COLUMN_MERCHANT,
    COLUMN_AMOUNT,
    COLUMN_IS_FRAUD,
    COLUMN_CATEGORY,
    COLUMN_CC_NUM,
    COLUMN_LAT,
    COLUMN_LONG,
    COLUMN_STATE,
    COLUMN_MERCH_LAT,
    COLUMN_MERCH_LONG,
    MERCHANT_NAME_PREFIX,
    TIMESTAMP_FORMAT,
)


def load_raw_csv(filepath: Path) -> pd.DataFrame:
    """
    Load a raw CSV file and return a DataFrame.

    Uses the first unnamed column as the index.
    Does not perform any cleaning — returns raw data as-is.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Dataset not found: {filepath}")

    df = pd.read_csv(filepath, index_col=0)
    return df


def clean_merchant_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strip the synthetic 'fraud_' prefix from merchant names.

    The Kaggle dataset prefixes all merchant names with 'fraud_' as
    a dataset convention. This is not meaningful for our analysis.
    """
    df = df.copy()
    df[COLUMN_MERCHANT] = (
        df[COLUMN_MERCHANT]
        .str.replace(MERCHANT_NAME_PREFIX, "", n=1, regex=False)
        .str.strip()
    )
    return df


def parse_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse the string timestamp column into proper datetime objects.

    Also extracts useful temporal components for later analysis:
      - hour of day
      - day of week (0=Monday, 6=Sunday)
      - date (day-level grouping)

    These are structural fields needed for behavioral baseline
    construction in later phases.
    """
    df = df.copy()

    # Parse the string timestamp to datetime
    df[COLUMN_TIMESTAMP] = pd.to_datetime(
        df[COLUMN_TIMESTAMP], format=TIMESTAMP_FORMAT
    )

    # Extract temporal components useful for behavioral analysis
    df["hour"] = df[COLUMN_TIMESTAMP].dt.hour
    df["day_of_week"] = df[COLUMN_TIMESTAMP].dt.dayofweek
    df["date"] = df[COLUMN_TIMESTAMP].dt.date

    return df


def select_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retain only columns relevant to burst detection.
    Drop PII and irrelevant columns per Phase 0 findings.

    Retained:
      Critical: trans_date_trans_time, unix_time, merchant, amt, is_fraud
      Behavioral: category, cc_num
      Contextual: lat, long, state, merch_lat, merch_long

    Dropped:
      PII/irrelevant: first, last, gender, street, city, zip,
                       city_pop, job, dob, trans_num
    """
    df = df.copy()

    # Keep only relevant columns (plus temporal components added by parse_timestamps)
    keep = [c for c in RETAINED_COLUMNS if c in df.columns]

    # Also keep derived temporal columns if they exist
    for derived_col in ["hour", "day_of_week", "date"]:
        if derived_col in df.columns:
            keep.append(derived_col)

    df = df[keep]
    return df


def validate_data_quality(df: pd.DataFrame, dataset_name: str) -> dict:
    """
    Run data quality checks and return a validation report.

    Checks:
      1. Missing values per column
      2. Data types
      3. Value ranges for critical columns
      4. Class imbalance (fraud vs legitimate)
      5. Timestamp range and continuity
      6. Merchant and category distributions
    """
    report = {
        "dataset_name": dataset_name,
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
    }

    # 1. Missing values
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    report["missing_values"] = {
        col: {"count": int(missing[col]), "pct": float(missing_pct[col])}
        for col in df.columns
        if missing[col] > 0
    }
    report["has_missing"] = len(report["missing_values"]) > 0

    # 2. Data types
    report["dtypes"] = {col: str(df[col].dtype) for col in df.columns}

    # 3. Amount range
    if COLUMN_AMOUNT in df.columns:
        report["amount"] = {
            "min": float(df[COLUMN_AMOUNT].min()),
            "max": float(df[COLUMN_AMOUNT].max()),
            "mean": float(df[COLUMN_AMOUNT].mean()),
            "median": float(df[COLUMN_AMOUNT].median()),
            "std": float(df[COLUMN_AMOUNT].std()),
        }

    # 4. Class imbalance
    if COLUMN_IS_FRAUD in df.columns:
        fraud_counts = df[COLUMN_IS_FRAUD].value_counts()
        total = len(df)
        report["class_balance"] = {
            "legitimate": int(fraud_counts.get(0, 0)),
            "fraud": int(fraud_counts.get(1, 0)),
            "fraud_rate_pct": round(
                fraud_counts.get(1, 0) / total * 100, 4
            ),
        }

    # 5. Timestamp range
    if COLUMN_TIMESTAMP in df.columns:
        report["time_range"] = {
            "start": str(df[COLUMN_TIMESTAMP].min()),
            "end": str(df[COLUMN_TIMESTAMP].max()),
            "duration_days": int(
                (df[COLUMN_TIMESTAMP].max() - df[COLUMN_TIMESTAMP].min()).days
            ),
        }

    # 6. Merchant distribution
    if COLUMN_MERCHANT in df.columns:
        merchant_counts = df[COLUMN_MERCHANT].value_counts()
        report["merchants"] = {
            "unique_count": int(df[COLUMN_MERCHANT].nunique()),
            "min_tx_per_merchant": int(merchant_counts.min()),
            "max_tx_per_merchant": int(merchant_counts.max()),
            "mean_tx_per_merchant": round(float(merchant_counts.mean()), 1),
            "median_tx_per_merchant": int(merchant_counts.median()),
        }

    # 7. Category distribution
    if COLUMN_CATEGORY in df.columns:
        report["categories"] = {
            "unique_count": int(df[COLUMN_CATEGORY].nunique()),
            "distribution": df[COLUMN_CATEGORY]
            .value_counts()
            .to_dict(),
        }

    return report


def process_dataset(
    filepath: Path,
    dataset_name: str,
    save: bool = True,
) -> tuple[pd.DataFrame, dict]:
    """
    Full Phase 1 processing pipeline for a single CSV file.

    Steps:
      1. Load raw CSV
      2. Clean merchant names
      3. Parse timestamps
      4. Select relevant columns
      5. Validate data quality
      6. Optionally save processed output

    Returns:
      (cleaned_dataframe, validation_report)
    """
    print(f"\n{'='*60}")
    print(f"Processing: {dataset_name}")
    print(f"Source: {filepath}")
    print(f"{'='*60}")

    # Step 1: Load
    print("\n[1/5] Loading raw CSV...")
    df = load_raw_csv(filepath)
    print(f"  Loaded {len(df):,} rows x {len(df.columns)} columns")

    # Step 2: Clean merchant names
    print("\n[2/5] Cleaning merchant names...")
    sample_before = df[COLUMN_MERCHANT].iloc[0]
    df = clean_merchant_names(df)
    sample_after = df[COLUMN_MERCHANT].iloc[0]
    print(f"  Example: '{sample_before}' -> '{sample_after}'")
    print(f"  Unique merchants: {df[COLUMN_MERCHANT].nunique()}")

    # Step 3: Parse timestamps
    print("\n[3/5] Parsing timestamps...")
    df = parse_timestamps(df)
    print(f"  Time range: {df[COLUMN_TIMESTAMP].min()} -> {df[COLUMN_TIMESTAMP].max()}")
    print(f"  Duration: {(df[COLUMN_TIMESTAMP].max() - df[COLUMN_TIMESTAMP].min()).days} days")

    # Step 4: Select columns
    print("\n[4/5] Selecting relevant columns...")
    original_cols = list(df.columns)
    df = select_columns(df)
    dropped = set(original_cols) - set(df.columns)
    print(f"  Retained: {len(df.columns)} columns")
    print(f"  Dropped: {len(dropped)} columns ({', '.join(sorted(dropped)) if dropped else 'none'})")

    # Step 5: Validate
    print("\n[5/5] Validating data quality...")
    report = validate_data_quality(df, dataset_name)

    # Print validation summary
    print(f"\n  Total rows: {report['total_rows']:,}")
    print(f"  Columns: {report['columns']}")

    if report["has_missing"]:
        print(f"  [!] Missing values found:")
        for col, info in report["missing_values"].items():
            print(f"    {col}: {info['count']:,} ({info['pct']}%)")
    else:
        print(f"  [OK] No missing values")

    if "class_balance" in report:
        cb = report["class_balance"]
        print(f"  Class balance:")
        print(f"    Legitimate: {cb['legitimate']:,}")
        print(f"    Fraud:      {cb['fraud']:,} ({cb['fraud_rate_pct']}%)")

    if "merchants" in report:
        m = report["merchants"]
        print(f"  Merchants: {m['unique_count']} unique")
        print(f"    Tx range: {m['min_tx_per_merchant']} - {m['max_tx_per_merchant']} per merchant")

    # Save processed data
    if save:
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        output_path = PROCESSED_DATA_DIR / f"{dataset_name}_clean.parquet"
        df.to_parquet(output_path, index=False)
        print(f"\n  [OK] Saved to: {output_path}")
        print(f"    Size: {output_path.stat().st_size / (1024*1024):.1f} MB")

    return df, report


def load_processed(dataset_name: str) -> pd.DataFrame:
    """
    Load a previously processed and saved dataset.
    Used by later phases to avoid re-processing raw CSV each time.
    """
    path = PROCESSED_DATA_DIR / f"{dataset_name}_clean.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Processed dataset not found: {path}. "
            f"Run process_dataset() first."
        )
    return pd.read_parquet(path)
