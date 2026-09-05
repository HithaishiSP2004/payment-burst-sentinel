"""
Payment Burst Sentinel -- Phase 5: Evaluation Script
======================================================
Execute the complete honest evaluation pipeline on held-out test data.

  Step 1: Build test baselines (temporal continuity from training)
  Step 2: Apply frozen Phase 4 detector
  Step 3: Primary metrics (enrichment, risk levels, anomaly types)
  Step 4: Secondary analysis (amount dominance, velocity value)
  Step 5: Proxy classification metrics
  Step 6: Baseline comparison
  Step 7: Failure analysis
  Step 8: Decision

Usage:
  python scripts/evaluate_detector.py
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
from backend.anomaly_detector import (
    compute_deviation_scores,
    classify_anomalies,
    generate_evidence,
)
from backend.evaluation import (
    build_test_baselines,
    compute_enrichment,
    volume_only_baseline,
    EVALUATION_DIR,
)

# Frozen thresholds from Phase 4
ELEVATED_THRESHOLD = 4.0
HIGH_THRESHOLD = 5.0


def ps(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def run_phase_5():
    ps("PAYMENT BURST SENTINEL - PHASE 5: HONEST EVALUATION")
    print("\n  Evaluating the FROZEN Phase 4 detector on unseen test data.")
    print("  Anomaly != Fraud. Enrichment over classification.")
    print("  No threshold tuning. No model changes. Absolute honesty.")

    # ─── STEP 1: BUILD TEST BASELINES ────────────────────────
    ps("STEP 1: BUILD HELD-OUT TEST BASELINES")

    print("  Loading data...")
    train_df = load_processed("train")
    test_df = load_processed("test")
    print(f"    Train: {len(train_df):,} transactions")
    print(f"    Test:  {len(test_df):,} transactions")

    train_end = pd.to_datetime(train_df["trans_date_trans_time"]).max()
    test_start = pd.to_datetime(test_df["trans_date_trans_time"]).min()
    test_end = pd.to_datetime(test_df["trans_date_trans_time"]).max()
    print(f"    Train ends:  {train_end}")
    print(f"    Test starts: {test_start}")
    print(f"    Test ends:   {test_end}")
    print(f"    Gap: {(test_start - train_end).total_seconds():.0f} seconds")

    print("\n  Building test baselines with temporal continuity...")
    print("  (Training history feeds into test baseline lookback)")
    test_baseline_df = build_test_baselines(train_df, test_df)
    print(f"    Test merchant-days: {len(test_baseline_df):,}")
    print(f"    Merchants: {test_baseline_df[COLUMN_MERCHANT].nunique()}")

    # Status distribution
    status = test_baseline_df["baseline_status"].value_counts()
    for s, c in status.items():
        print(f"    {s}: {c:,} ({c/len(test_baseline_df)*100:.1f}%)")

    # Temporal integrity spot-check
    sufficient = test_baseline_df[test_baseline_df["baseline_status"] == "sufficient_history"]
    print(f"\n  Temporal integrity check:")
    print(f"    All sufficient-history rows have >= 7 historical days: "
          f"{'YES' if (sufficient['historical_days_used'] >= 7).all() else 'NO'}")

    # ─── STEP 2: APPLY FROZEN DETECTOR ───────────────────────
    ps("STEP 2: APPLY FROZEN PHASE 4 DETECTOR")

    print(f"  Frozen policy: elevated >= {ELEVATED_THRESHOLD}, high >= {HIGH_THRESHOLD}")
    print("  No threshold changes. No signal changes.")

    scored = compute_deviation_scores(test_baseline_df)
    anomaly_df = classify_anomalies(scored, ELEVATED_THRESHOLD, HIGH_THRESHOLD)
    suf = anomaly_df[anomaly_df["baseline_status"] == "sufficient_history"].copy()

    type_counts = suf["anomaly_type"].value_counts()
    risk_counts = suf["risk_level"].value_counts()

    print(f"\n  Test anomaly distribution ({len(suf):,} eligible merchant-days):")
    for t, c in type_counts.items():
        print(f"    {t:25s}: {c:>7,} ({c/len(suf)*100:>5.2f}%)")

    print(f"\n  Test risk levels:")
    for r, c in risk_counts.items():
        print(f"    {r:25s}: {c:>7,} ({c/len(suf)*100:>5.2f}%)")

    # ─── STEP 3: PRIMARY METRICS ─────────────────────────────
    ps("STEP 3: PRIMARY METRICS")

    # A. Overall fraud prevalence
    total_fraud_days = (suf["fraud_count"] > 0).sum()
    total_fraud_rate = total_fraud_days / len(suf)
    total_fraud_tx = suf["fraud_count"].sum()
    total_tx = suf["transaction_count"].sum()

    print(f"\n  A. OVERALL FRAUD PREVALENCE (test set)")
    print(f"    Merchant-days containing fraud: {total_fraud_days:,} / {len(suf):,} ({total_fraud_rate*100:.3f}%)")
    print(f"    Total fraud transactions: {int(total_fraud_tx):,} / {int(total_tx):,} ({total_fraud_tx/total_tx*100:.4f}%)")

    # B. Flagged vs non-flagged enrichment
    flagged = suf[suf["anomaly_type"] != "normal"]
    normal = suf[suf["anomaly_type"] == "normal"]

    flagged_fraud_rate = (flagged["fraud_count"] > 0).mean() if len(flagged) > 0 else 0
    normal_fraud_rate = (normal["fraud_count"] > 0).mean() if len(normal) > 0 else 0

    enrichment_vs_overall = compute_enrichment(flagged_fraud_rate, total_fraud_rate)
    enrichment_vs_normal = compute_enrichment(flagged_fraud_rate, normal_fraud_rate)

    print(f"\n  B. FLAGGED vs NON-FLAGGED ENRICHMENT")
    print(f"    Flagged merchant-days: {len(flagged):,}")
    print(f"    Normal merchant-days:  {len(normal):,}")
    print(f"    Fraud-containing rate (flagged):  {flagged_fraud_rate*100:.3f}%")
    print(f"    Fraud-containing rate (normal):   {normal_fraud_rate*100:.3f}%")
    print(f"    Fraud-containing rate (overall):  {total_fraud_rate*100:.3f}%")
    print(f"    ENRICHMENT vs overall: {enrichment_vs_overall:.2f}x")
    print(f"    ENRICHMENT vs normal:  {enrichment_vs_normal:.2f}x")

    # C. Risk-level comparison
    print(f"\n  C. RISK-LEVEL COMPARISON")
    print(f"  {'Risk Level':<12s} | {'Count':>7s} | {'Fraud Days':>10s} | {'Fraud Rate':>10s} | {'Fraud Tx':>8s} | Enrichment")
    print(f"  {'-'*12}-+-{'-'*7}-+-{'-'*10}-+-{'-'*10}-+-{'-'*8}-+-{'-'*12}")

    risk_results = {}
    for level in ["normal", "elevated", "high"]:
        subset = suf[suf["risk_level"] == level]
        if len(subset) == 0:
            continue
        fr = (subset["fraud_count"] > 0).mean()
        ftx = int(subset["fraud_count"].sum())
        enr = compute_enrichment(fr, total_fraud_rate)
        risk_results[level] = {
            "count": len(subset),
            "fraud_days": int((subset["fraud_count"] > 0).sum()),
            "fraud_rate": round(fr * 100, 3),
            "fraud_tx": ftx,
            "enrichment": round(enr, 2),
        }
        print(f"  {level:<12s} | {len(subset):>7,} | {(subset['fraud_count']>0).sum():>10,} | "
              f"{fr*100:>9.3f}% | {ftx:>8,} | {enr:.2f}x")

    # D. Anomaly-type comparison
    print(f"\n  D. ANOMALY-TYPE COMPARISON")
    print(f"  {'Anomaly Type':<20s} | {'Count':>7s} | {'Fraud Days':>10s} | {'Fraud Rate':>10s} | Enrichment")
    print(f"  {'-'*20}-+-{'-'*7}-+-{'-'*10}-+-{'-'*10}-+-{'-'*12}")

    type_results = {}
    for atype in ["normal", "velocity_anomaly", "amount_anomaly", "combined_anomaly"]:
        subset = suf[suf["anomaly_type"] == atype]
        if len(subset) == 0:
            continue
        fr = (subset["fraud_count"] > 0).mean()
        enr = compute_enrichment(fr, total_fraud_rate)
        type_results[atype] = {
            "count": len(subset),
            "fraud_days": int((subset["fraud_count"] > 0).sum()),
            "fraud_rate": round(fr * 100, 3),
            "enrichment": round(enr, 2),
        }
        print(f"  {atype:<20s} | {len(subset):>7,} | {(subset['fraud_count']>0).sum():>10,} | "
              f"{fr*100:>9.3f}% | {enr:.2f}x")

    # E. Alert volume
    total_flagged = len(flagged)
    print(f"\n  E. ALERT VOLUME")
    print(f"    Total eligible: {len(suf):,}")
    print(f"    Total flagged:  {total_flagged:,} ({total_flagged/len(suf)*100:.2f}%)")

    # ─── STEP 4: SECONDARY ANALYSIS ──────────────────────────
    ps("STEP 4: SECONDARY ANALYSIS")

    # Amount signal dominance
    print("\n  AMOUNT SIGNAL DOMINANCE:")
    if len(flagged) > 0:
        amt_flags = len(suf[suf["anomaly_type"] == "amount_anomaly"])
        vel_flags = len(suf[suf["anomaly_type"] == "velocity_anomaly"])
        comb_flags = len(suf[suf["anomaly_type"] == "combined_anomaly"])

        amt_pct = amt_flags / total_flagged * 100
        vel_pct = vel_flags / total_flagged * 100
        comb_pct = comb_flags / total_flagged * 100

        print(f"    Amount-only anomalies: {amt_flags:,} ({amt_pct:.1f}% of flags)")
        print(f"    Velocity-only anomalies: {vel_flags:,} ({vel_pct:.1f}% of flags)")
        print(f"    Combined anomalies: {comb_flags:,} ({comb_pct:.1f}% of flags)")

        if amt_pct > 60:
            print(f"    -> Amount anomalies DOMINATE ({amt_pct:.0f}% of all flags)")
        elif amt_pct > 40:
            print(f"    -> Amount anomalies are the primary driver ({amt_pct:.0f}%)")
        else:
            print(f"    -> Flags are balanced across signal types")

    # Velocity signal value
    print("\n  VELOCITY SIGNAL VALUE:")
    for atype in ["velocity_anomaly", "combined_anomaly", "amount_anomaly"]:
        subset = suf[suf["anomaly_type"] == atype]
        if len(subset) > 0:
            fr = (subset["fraud_count"] > 0).mean() * 100
            print(f"    {atype:20s}: fraud-containing rate = {fr:.3f}%")

    # Is combined > individual?
    comb_fr = type_results.get("combined_anomaly", {}).get("fraud_rate", 0)
    vel_fr = type_results.get("velocity_anomaly", {}).get("fraud_rate", 0)
    amt_fr = type_results.get("amount_anomaly", {}).get("fraud_rate", 0)

    if comb_fr > vel_fr and comb_fr > amt_fr:
        print("    -> Combined anomalies show STRONGEST fraud enrichment")
    elif vel_fr > amt_fr:
        print("    -> Velocity-only anomalies show stronger enrichment than amount-only")
    else:
        print("    -> Amount-only anomalies show stronger enrichment than velocity-only")

    # Alert efficiency
    print("\n  ALERT EFFICIENCY:")
    if len(flagged) > 0:
        fraud_in_flagged = (flagged["fraud_count"] > 0).sum()
        efficiency = fraud_in_flagged / len(flagged) * 100
        print(f"    Flagged days containing fraud: {fraud_in_flagged:,} / {len(flagged):,} ({efficiency:.2f}%)")
        print(f"    (This is 'proxy precision' -- not true burst-detection precision)")

    # ─── STEP 5: PROXY CLASSIFICATION METRICS ─────────────────
    ps("STEP 5: PROXY CLASSIFICATION METRICS")
    print("  NOTE: These use fraud-containing-day as a PROXY label.")
    print("  A fraud-containing day is NOT necessarily a 'burst attack'.")

    is_fraud_day = (suf["fraud_count"] > 0).values
    is_flagged = (suf["anomaly_type"] != "normal").values

    tp = int((is_flagged & is_fraud_day).sum())
    fp = int((is_flagged & ~is_fraud_day).sum())
    fn = int((~is_flagged & is_fraud_day).sum())
    tn = int((~is_flagged & ~is_fraud_day).sum())

    proxy_precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    proxy_recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    proxy_f1 = 2 * proxy_precision * proxy_recall / (proxy_precision + proxy_recall) if (proxy_precision + proxy_recall) > 0 else 0

    print(f"\n  PROXY CONFUSION MATRIX:")
    print(f"                        Predicted Anomaly  Predicted Normal")
    print(f"    Fraud-containing:   TP={tp:>7,}         FN={fn:>7,}")
    print(f"    Non-fraud:          FP={fp:>7,}         TN={tn:>7,}")
    print(f"\n  Proxy precision: {proxy_precision*100:.2f}%")
    print(f"  Proxy recall:    {proxy_recall*100:.2f}%")
    print(f"  Proxy F1:        {proxy_f1*100:.2f}%")
    print(f"\n  IMPORTANT: These metrics treat 'fraud-containing day' as ground truth.")
    print(f"  This is a proxy. Many fraud-containing days have 1 fraud tx among many legit.")

    # ─── STEP 6: BASELINE COMPARISON ──────────────────────────
    ps("STEP 6: BASELINE COMPARISON")

    # Baseline 1: Random flagging (overall prevalence)
    print("\n  BASELINE 1: Random flagging (prevalence reference)")
    print(f"    If we randomly flagged {total_flagged:,} merchant-days:")
    expected_fraud_random = total_fraud_rate * total_flagged
    print(f"    Expected fraud-containing days: ~{expected_fraud_random:.0f}")
    actual_fraud_flagged = (flagged["fraud_count"] > 0).sum()
    print(f"    Actual fraud-containing days:    {actual_fraud_flagged:,}")
    random_enrichment = actual_fraud_flagged / expected_fraud_random if expected_fraud_random > 0 else 0
    print(f"    Enrichment vs random: {random_enrichment:.2f}x")

    # Baseline 2: Volume-only flagging
    print("\n  BASELINE 2: Volume-only flagging (top-N by raw tx count)")
    vol_baseline = volume_only_baseline(anomaly_df, total_flagged)
    print(f"    Method: {vol_baseline['method']}")
    print(f"    Flagged: {vol_baseline['flagged_count']:,}")
    print(f"    Fraud-containing rate: {vol_baseline['fraud_containing_rate_flagged']}%")
    print(f"    Enrichment vs normal: {vol_baseline['enrichment_vs_normal']}x")
    print(f"\n    Our detector enrichment: {enrichment_vs_normal:.2f}x")
    print(f"    Volume-only enrichment: {vol_baseline['enrichment_vs_normal']}x")

    if enrichment_vs_normal > vol_baseline["enrichment_vs_normal"]:
        print("    -> Behavioral context ADDS value over simple volume flagging")
    elif abs(enrichment_vs_normal - vol_baseline["enrichment_vs_normal"]) < 0.1:
        print("    -> Behavioral context provides SIMILAR value to volume flagging")
    else:
        print("    -> Simple volume flagging provides BETTER enrichment")

    # ─── STEP 7: FAILURE ANALYSIS ─────────────────────────────
    ps("STEP 7: FAILURE ANALYSIS")

    # 7a. False-positive proxy examples (flagged, no fraud)
    fp_examples = suf[(suf["anomaly_type"] != "normal") & (suf["fraud_count"] == 0)]
    print(f"\n  A. FALSE-POSITIVE PROXY EXAMPLES (flagged, no fraud)")
    print(f"     Total: {len(fp_examples):,}")

    if len(fp_examples) > 0:
        # Show 3 representative examples
        for i, (_, ex) in enumerate(fp_examples.sample(min(3, len(fp_examples)), random_state=42).iterrows()):
            evidence = generate_evidence(ex)
            print(f"\n    Example {i+1}: {ex[COLUMN_MERCHANT]}")
            print(f"      Date: {ex['date']}, Type: {ex['anomaly_type']}, Risk: {ex['risk_level']}")
            print(f"      Velocity: {int(ex['transaction_count'])} tx vs {ex['expected_tx_count']:.1f} expected ({ex['velocity_deviation']:.1f} MADs)")
            print(f"      Amount: ${ex['total_amount']:.2f} vs ${ex['expected_total_amount']:.2f} expected ({ex['amount_deviation']:.1f} MADs)")
            print(f"      -> Legitimate behavioral deviation (no fraud present)")

    # 7b. False-negative proxy examples (not flagged, has fraud)
    fn_examples = suf[(suf["anomaly_type"] == "normal") & (suf["fraud_count"] > 0)]
    print(f"\n  B. FALSE-NEGATIVE PROXY EXAMPLES (not flagged, has fraud)")
    print(f"     Total: {len(fn_examples):,}")

    if len(fn_examples) > 0:
        for i, (_, ex) in enumerate(fn_examples.sample(min(3, len(fn_examples)), random_state=42).iterrows()):
            print(f"\n    Example {i+1}: {ex[COLUMN_MERCHANT]}")
            print(f"      Date: {ex['date']}, Fraud tx: {int(ex['fraud_count'])}/{int(ex['transaction_count'])}")
            print(f"      Velocity deviation: {ex['velocity_deviation_raw']:.2f} MADs (raw)")
            print(f"      Amount deviation: {ex['amount_deviation_raw']:.2f} MADs (raw)")
            print(f"      -> Fraud occurred during BEHAVIORALLY NORMAL activity")
            print(f"      -> This is expected: Phase 2 proved fraud doesn't concentrate in bursts")

    # 7c. Strongest anomaly examples
    print(f"\n  C. STRONGEST ANOMALY EXAMPLES (highest composite deviation)")
    top_anomalies = suf.nlargest(5, "composite_deviation")
    for i, (_, ex) in enumerate(top_anomalies.iterrows()):
        has_fraud = "YES" if ex["fraud_count"] > 0 else "NO"
        print(f"\n    #{i+1}: {ex[COLUMN_MERCHANT]}")
        print(f"      Date: {ex['date']}, Composite: {ex['composite_deviation']:.1f} MADs")
        print(f"      Velocity: {int(ex['transaction_count'])} tx ({ex['velocity_deviation']:.1f} MADs)")
        print(f"      Amount: ${ex['total_amount']:.2f} ({ex['amount_deviation']:.1f} MADs)")
        print(f"      Contains fraud: {has_fraud} (fraud_count={int(ex['fraud_count'])})")

    # ─── STEP 8: DECISION ─────────────────────────────────────
    ps("STEP 8: HONEST VERDICT")

    # Determine verdict based on evidence
    if enrichment_vs_overall >= 1.5 and enrichment_vs_normal >= 1.3:
        verdict = "OPTION A: Meaningful enrichment"
        verdict_detail = (
            "The behavioral anomaly detector provides meaningful fraud enrichment "
            "on unseen data. Flagged merchant-days contain fraud at a meaningfully "
            "higher rate than normal or random baselines."
        )
    elif enrichment_vs_overall >= 1.1:
        verdict = "OPTION B: Limited enrichment"
        verdict_detail = (
            "The detector provides limited but non-zero enrichment. It identifies "
            "genuine behavioral anomalies but their correlation with fraud is weak. "
            "The system has value as behavioral monitoring even if fraud enrichment is modest."
        )
    else:
        verdict = "OPTION C: No meaningful enrichment"
        verdict_detail = (
            "The detector does not provide meaningful fraud enrichment on this dataset. "
            "However, it may still function as a behavioral deviation monitor."
        )

    print(f"\n  VERDICT: {verdict}")
    print(f"  {verdict_detail}")
    print(f"\n  Evidence supporting verdict:")
    print(f"    Enrichment vs overall: {enrichment_vs_overall:.2f}x")
    print(f"    Enrichment vs normal:  {enrichment_vs_normal:.2f}x")
    print(f"    Proxy precision: {proxy_precision*100:.2f}%")
    print(f"    Proxy recall:    {proxy_recall*100:.2f}%")

    # ─── SAVE OUTPUTS ──────────────────────────────────────────
    ps("SAVING OUTPUTS")

    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)

    # Save test anomaly dataset
    out_path = EVALUATION_DIR / "test_anomalies.parquet"
    anomaly_df.to_parquet(out_path, index=False)
    print(f"  Saved: {out_path}")

    # Save evaluation report
    report = {
        "evaluation_setup": {
            "train_transactions": len(train_df),
            "test_transactions": len(test_df),
            "train_end": str(train_end),
            "test_start": str(test_start),
            "test_end": str(test_end),
            "frozen_elevated_threshold": ELEVATED_THRESHOLD,
            "frozen_high_threshold": HIGH_THRESHOLD,
        },
        "dataset_coverage": {
            "eligible_merchant_days": len(suf),
            "merchants_covered": int(suf[COLUMN_MERCHANT].nunique()),
            "status_distribution": status.to_dict(),
        },
        "primary_results": {
            "overall_fraud_prevalence": {
                "fraud_containing_days": int(total_fraud_days),
                "fraud_containing_rate_pct": round(total_fraud_rate * 100, 3),
                "fraud_tx_count": int(total_fraud_tx),
                "fraud_tx_rate_pct": round(float(total_fraud_tx / total_tx * 100), 4),
            },
            "flagged_vs_normal": {
                "flagged_count": len(flagged),
                "normal_count": len(normal),
                "flagged_fraud_rate_pct": round(flagged_fraud_rate * 100, 3),
                "normal_fraud_rate_pct": round(normal_fraud_rate * 100, 3),
                "enrichment_vs_overall": round(enrichment_vs_overall, 2),
                "enrichment_vs_normal": round(enrichment_vs_normal, 2),
            },
            "risk_levels": risk_results,
            "anomaly_types": type_results,
            "alert_volume": {
                "total_flagged": total_flagged,
                "pct_flagged": round(total_flagged / len(suf) * 100, 2),
            },
        },
        "amount_dominance": {
            "amount_only_pct_of_flags": round(amt_pct, 1) if len(flagged) > 0 else 0,
            "velocity_only_pct_of_flags": round(vel_pct, 1) if len(flagged) > 0 else 0,
            "combined_pct_of_flags": round(comb_pct, 1) if len(flagged) > 0 else 0,
        },
        "proxy_classification": {
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "proxy_precision_pct": round(proxy_precision * 100, 2),
            "proxy_recall_pct": round(proxy_recall * 100, 2),
            "proxy_f1_pct": round(proxy_f1 * 100, 2),
        },
        "baseline_comparison": {
            "random_enrichment": round(random_enrichment, 2),
            "volume_only": vol_baseline,
        },
        "verdict": verdict,
        "verdict_detail": verdict_detail,
    }

    report_path = EVALUATION_DIR / "evaluation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"  Saved: {report_path}")

    # ─── COMPLETION ───────────────────────────────────────────
    ps("PHASE 5 COMPLETE -- HONEST EVALUATION")
    print(f"\n  VERDICT: {verdict}\n")

    print(f"{'='*70}")
    print(f"  Phase 5 - Honest Evaluation - COMPLETE")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    run_phase_5()
