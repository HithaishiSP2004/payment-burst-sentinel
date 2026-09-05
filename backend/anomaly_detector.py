"""
Payment Burst Sentinel -- Phase 4: Behavioral Anomaly Detection Engine
=======================================================================
PURPOSE: Transform Phase 3 baseline outputs into an interpretable
behavioral anomaly detection system.

CRITICAL TRUTH:
  ANOMALY != FRAUD
  A detected event means: "This merchant's payment behavior deviated
  meaningfully from its historical behavioral baseline."
  It does NOT mean: "This merchant is experiencing confirmed fraud."

CORE SIGNALS (Phase 2 validated):
  1. Transaction velocity deviation (daily tx count vs baseline)
  2. Total amount deviation (daily total vs baseline)

DIRECTIONALITY:
  Only POSITIVE deviations (observed > expected) create burst risk.
  Decreased activity does not generate burst alerts.

DEVIATION FORMULA:
  deviation = max(0, (observed - expected) / variability)
  Where variability = MAD with safety floor (from Phase 3)

  This produces a non-negative score representing how many MAD-units
  the observed value exceeds the expected baseline.

  Interpretation:
    0.0 = at or below expected
    1.0 = 1 MAD above expected
    3.0 = 3 MADs above expected (unusual)
    5.0+ = very unusual

COMPOSITE DESIGN:
  NOT a black box. The detector preserves which signals contribute:
    - velocity_only: elevated tx count, normal amount
    - amount_only: elevated amount, normal tx count
    - combined: both elevated
    - normal: neither elevated
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional

from backend.config import (
    PROCESSED_DATA_DIR,
    COLUMN_MERCHANT,
)

# =====================================================================
# Configuration
# =====================================================================

BASELINE_DIR = PROCESSED_DATA_DIR / "baselines"
ANOMALIES_DIR = PROCESSED_DATA_DIR / "anomalies"


# =====================================================================
# Step 1: Compute deviation scores
# =====================================================================

def compute_deviation_scores(baseline_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each merchant-day with sufficient history, compute interpretable
    deviation scores for the two core signals.

    Deviation formula:
      positive_deviation = max(0, (observed - expected) / variability)

    Only POSITIVE deviations contribute to burst detection.
    Negative deviations (below-expected activity) are recorded but
    clamped to 0 for burst scoring.

    Raw (unclamped) deviations are also preserved for transparency.
    """
    df = baseline_df.copy()

    # Only score rows with sufficient history
    sufficient = df["baseline_status"] == "sufficient_history"

    # Raw deviation (can be negative)
    df["velocity_deviation_raw"] = np.where(
        sufficient,
        (df["transaction_count"] - df["expected_tx_count"]) / df["tx_count_variability"],
        np.nan,
    )

    df["amount_deviation_raw"] = np.where(
        sufficient,
        (df["total_amount"] - df["expected_total_amount"]) / df["total_amount_variability"],
        np.nan,
    )

    # Burst-relevant deviation: clamped to 0 (only upward deviations matter)
    df["velocity_deviation"] = np.where(
        sufficient,
        np.maximum(0.0, df["velocity_deviation_raw"]),
        np.nan,
    )

    df["amount_deviation"] = np.where(
        sufficient,
        np.maximum(0.0, df["amount_deviation_raw"]),
        np.nan,
    )

    return df


# =====================================================================
# Step 2: Analyze deviation distributions for threshold discovery
# =====================================================================

def analyze_deviation_distributions(scored_df: pd.DataFrame) -> dict:
    """
    Analyze the distribution of positive deviations to inform threshold
    selection. This uses ONLY training data -- no test data.

    Returns distribution statistics and candidate threshold analysis.
    """
    sufficient = scored_df[scored_df["baseline_status"] == "sufficient_history"]

    # Positive-only distributions (where deviation > 0)
    vel_positive = sufficient["velocity_deviation"][sufficient["velocity_deviation"] > 0]
    amt_positive = sufficient["amount_deviation"][sufficient["amount_deviation"] > 0]

    findings = {
        "total_sufficient_rows": len(sufficient),
        "velocity": {
            "total_positive": len(vel_positive),
            "pct_positive": round(len(vel_positive) / len(sufficient) * 100, 2),
            "percentiles": {
                "p50": round(float(vel_positive.quantile(0.50)), 2) if len(vel_positive) > 0 else 0,
                "p75": round(float(vel_positive.quantile(0.75)), 2) if len(vel_positive) > 0 else 0,
                "p90": round(float(vel_positive.quantile(0.90)), 2) if len(vel_positive) > 0 else 0,
                "p95": round(float(vel_positive.quantile(0.95)), 2) if len(vel_positive) > 0 else 0,
                "p99": round(float(vel_positive.quantile(0.99)), 2) if len(vel_positive) > 0 else 0,
                "max": round(float(vel_positive.max()), 2) if len(vel_positive) > 0 else 0,
            },
        },
        "amount": {
            "total_positive": len(amt_positive),
            "pct_positive": round(len(amt_positive) / len(sufficient) * 100, 2),
            "percentiles": {
                "p50": round(float(amt_positive.quantile(0.50)), 2) if len(amt_positive) > 0 else 0,
                "p75": round(float(amt_positive.quantile(0.75)), 2) if len(amt_positive) > 0 else 0,
                "p90": round(float(amt_positive.quantile(0.90)), 2) if len(amt_positive) > 0 else 0,
                "p95": round(float(amt_positive.quantile(0.95)), 2) if len(amt_positive) > 0 else 0,
                "p99": round(float(amt_positive.quantile(0.99)), 2) if len(amt_positive) > 0 else 0,
                "max": round(float(amt_positive.max()), 2) if len(amt_positive) > 0 else 0,
            },
        },
    }

    # Candidate threshold analysis: how many alerts at each level?
    candidates = [1.0, 2.0, 3.0, 4.0, 5.0]
    threshold_analysis = {}

    for t in candidates:
        vel_above = (sufficient["velocity_deviation"] >= t).sum()
        amt_above = (sufficient["amount_deviation"] >= t).sum()
        both_above = (
            (sufficient["velocity_deviation"] >= t) &
            (sufficient["amount_deviation"] >= t)
        ).sum()
        either_above = (
            (sufficient["velocity_deviation"] >= t) |
            (sufficient["amount_deviation"] >= t)
        ).sum()

        threshold_analysis[str(t)] = {
            "velocity_only": int(vel_above - both_above),
            "amount_only": int(amt_above - both_above),
            "combined": int(both_above),
            "total_flagged": int(either_above),
            "pct_flagged": round(int(either_above) / len(sufficient) * 100, 3),
            "daily_avg_alerts": round(int(either_above) / (len(sufficient) / 693), 2),
        }

    findings["threshold_analysis"] = threshold_analysis

    return findings


# =====================================================================
# Step 3: Classify anomalies
# =====================================================================

def classify_anomalies(
    scored_df: pd.DataFrame,
    elevated_threshold: float,
    high_threshold: float,
) -> pd.DataFrame:
    """
    Classify each merchant-day into anomaly types and risk levels.

    Anomaly types (based on which signals are elevated):
      - normal: neither signal elevated
      - velocity_anomaly: velocity elevated, amount not
      - amount_anomaly: amount elevated, velocity not
      - combined_anomaly: both signals elevated

    Risk levels (based on maximum deviation magnitude):
      - normal: max deviation < elevated_threshold
      - elevated: elevated_threshold <= max deviation < high_threshold
      - high: max deviation >= high_threshold

    Thresholds are determined by distribution analysis, NOT arbitrary.
    """
    df = scored_df.copy()
    sufficient = df["baseline_status"] == "sufficient_history"

    # Determine which signals are elevated
    vel_elevated = sufficient & (df["velocity_deviation"] >= elevated_threshold)
    amt_elevated = sufficient & (df["amount_deviation"] >= elevated_threshold)

    # Anomaly type
    df["anomaly_type"] = "not_scored"
    df.loc[sufficient, "anomaly_type"] = "normal"
    df.loc[vel_elevated & ~amt_elevated, "anomaly_type"] = "velocity_anomaly"
    df.loc[~vel_elevated & amt_elevated, "anomaly_type"] = "amount_anomaly"
    df.loc[vel_elevated & amt_elevated, "anomaly_type"] = "combined_anomaly"

    # Composite score: maximum of the two deviations
    # Using max preserves interpretability: the score represents the
    # strongest single signal, not an opaque combination
    df["composite_deviation"] = np.where(
        sufficient,
        np.maximum(df["velocity_deviation"], df["amount_deviation"]),
        np.nan,
    )

    # Risk level based on composite deviation
    df["risk_level"] = "not_scored"
    df.loc[sufficient, "risk_level"] = "normal"
    df.loc[sufficient & (df["composite_deviation"] >= elevated_threshold), "risk_level"] = "elevated"
    df.loc[sufficient & (df["composite_deviation"] >= high_threshold), "risk_level"] = "high"

    return df


# =====================================================================
# Step 4: Generate evidence statements
# =====================================================================

def generate_evidence(row: pd.Series) -> dict:
    """
    Generate deterministic, traceable evidence for a single merchant-day.

    Every statement maps directly to observed vs expected values.
    No LLM. No vague claims. No fraud probability.
    """
    evidence = {
        "merchant": row["merchant"],
        "date": str(row["date"]),
        "risk_level": row["risk_level"],
        "anomaly_type": row["anomaly_type"],
        "statements": [],
        "signals": {},
    }

    # Velocity evidence
    vel_dev = row["velocity_deviation"]
    if vel_dev > 0:
        obs_tx = int(row["transaction_count"])
        exp_tx = round(row["expected_tx_count"], 1)
        var_tx = round(row["tx_count_variability"], 1)

        evidence["signals"]["velocity"] = {
            "observed": obs_tx,
            "expected": exp_tx,
            "variability": var_tx,
            "deviation": round(vel_dev, 2),
        }

        if vel_dev >= 3.0:
            evidence["statements"].append(
                f"Daily transaction count ({obs_tx}) was substantially above "
                f"this merchant's recent historical range "
                f"(expected ~{exp_tx}, variability +/-{var_tx})."
            )
        elif vel_dev >= 1.0:
            evidence["statements"].append(
                f"Daily transaction count ({obs_tx}) was above this merchant's "
                f"expected level of ~{exp_tx}."
            )

    # Amount evidence
    amt_dev = row["amount_deviation"]
    if amt_dev > 0:
        obs_amt = round(row["total_amount"], 2)
        exp_amt = round(row["expected_total_amount"], 2)
        var_amt = round(row["total_amount_variability"], 2)

        evidence["signals"]["amount"] = {
            "observed": obs_amt,
            "expected": exp_amt,
            "variability": var_amt,
            "deviation": round(amt_dev, 2),
        }

        if amt_dev >= 3.0:
            evidence["statements"].append(
                f"Total payment value (${obs_amt:.2f}) was significantly above "
                f"the expected range "
                f"(expected ~${exp_amt:.2f}, variability +/-${var_amt:.2f})."
            )
        elif amt_dev >= 1.0:
            evidence["statements"].append(
                f"Total payment value (${obs_amt:.2f}) was above this merchant's "
                f"expected level of ~${exp_amt:.2f}."
            )

    # Combined evidence
    if row["anomaly_type"] == "combined_anomaly":
        evidence["statements"].append(
            "Both transaction volume and total payment value increased together, "
            "suggesting a coordinated behavioral shift."
        )

    # Normal statement
    if row["anomaly_type"] == "normal":
        evidence["statements"].append(
            "Activity was within the expected behavioral range for this merchant."
        )

    # Context
    evidence["context"] = {
        "day_of_week": int(row["day_of_week"]),
        "historical_days_used": int(row["historical_days_used"]),
        "baseline_window": int(row["baseline_window_days"]),
    }

    return evidence


def generate_all_evidence(anomaly_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate evidence for all anomalous merchant-days.
    Only generates full evidence for non-normal observations to save space.
    """
    df = anomaly_df.copy()

    # Generate summary evidence string for all rows
    evidence_summaries = []
    for _, row in df.iterrows():
        if row["risk_level"] == "not_scored" or row["anomaly_type"] == "normal":
            evidence_summaries.append("")
            continue

        evidence = generate_evidence(row)
        summary = " | ".join(evidence["statements"])
        evidence_summaries.append(summary)

    df["evidence_summary"] = evidence_summaries

    return df
