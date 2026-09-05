"""
Payment Burst Sentinel — Phase 2: Exploratory Analysis for Burst Detection
==========================================================================
Purpose: Discover what "normal payment rhythm" looks like and how a
meaningful behavioral payment burst should be defined using this data.

This is NOT general EDA. Every analysis answers a design question for
Phase 3 (Baseline Engine) and Phase 4 (Burst Detection Engine).

Analysis Areas:
  1. Merchant Activity Rhythms (daily, hourly, day-of-week)
  2. Observation Window Discovery
  3. Merchant Baseline Stability
  4. Transaction Amount Behavior
  5. Activity Concentration
  6. Fraud Context
  7. Behavioral Signal Selection

Usage:
  python scripts/analyze_bursts.py
"""

import sys
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore", category=FutureWarning)

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.config import (
    PROCESSED_DATA_DIR,
    COLUMN_TIMESTAMP,
    COLUMN_UNIX_TIME,
    COLUMN_MERCHANT,
    COLUMN_AMOUNT,
    COLUMN_IS_FRAUD,
    COLUMN_CATEGORY,
    COLUMN_CC_NUM,
)

RESULTS_DIR = PROCESSED_DATA_DIR / "phase2_analysis"


def load_train_data() -> pd.DataFrame:
    """Load processed training data from Phase 1."""
    path = PROCESSED_DATA_DIR / "train_clean.parquet"
    df = pd.read_parquet(path)
    # Ensure datetime type
    df[COLUMN_TIMESTAMP] = pd.to_datetime(df[COLUMN_TIMESTAMP])
    return df


def save_finding(name: str, data: dict):
    """Save an analysis finding as JSON."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def print_section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


# =====================================================================
# ANALYSIS AREA 1: MERCHANT ACTIVITY RHYTHMS
# =====================================================================

def analyze_merchant_rhythms(df: pd.DataFrame) -> dict:
    """
    Design question: Is a simple merchant-wide average sufficient,
    or do we need time-aware baselines?
    """
    print_section("AREA 1: MERCHANT ACTIVITY RHYTHMS")
    findings = {}

    # --- A. Daily activity per merchant ---
    print("\n  A. Daily Activity Analysis")
    daily = df.groupby([COLUMN_MERCHANT, "date"]).size().reset_index(name="tx_count")

    # Per-merchant daily stats
    merchant_daily_stats = daily.groupby(COLUMN_MERCHANT)["tx_count"].agg(
        ["mean", "std", "min", "max", "median"]
    )
    merchant_daily_stats["cv"] = merchant_daily_stats["std"] / merchant_daily_stats["mean"]

    findings["daily_activity"] = {
        "mean_daily_tx_across_merchants": round(float(merchant_daily_stats["mean"].mean()), 2),
        "median_daily_tx": round(float(merchant_daily_stats["median"].mean()), 2),
        "avg_daily_std": round(float(merchant_daily_stats["std"].mean()), 2),
        "avg_coefficient_of_variation": round(float(merchant_daily_stats["cv"].mean()), 3),
        "cv_distribution": {
            "p25": round(float(merchant_daily_stats["cv"].quantile(0.25)), 3),
            "p50": round(float(merchant_daily_stats["cv"].quantile(0.50)), 3),
            "p75": round(float(merchant_daily_stats["cv"].quantile(0.75)), 3),
            "p90": round(float(merchant_daily_stats["cv"].quantile(0.90)), 3),
        },
    }

    avg_cv = merchant_daily_stats["cv"].mean()
    print(f"    Mean daily tx per merchant: {findings['daily_activity']['mean_daily_tx_across_merchants']}")
    print(f"    Avg coefficient of variation: {avg_cv:.3f}")
    print(f"    -> {'Moderate' if avg_cv < 0.5 else 'High'} variability in daily activity")

    # --- B. Hourly activity ---
    print("\n  B. Hourly Activity Analysis")
    hourly = df.groupby([COLUMN_MERCHANT, "hour"]).size().reset_index(name="tx_count")
    hourly_profile = df.groupby("hour").size()
    hourly_pct = (hourly_profile / hourly_profile.sum() * 100).round(2)

    # Find peak and trough hours
    peak_hour = int(hourly_pct.idxmax())
    trough_hour = int(hourly_pct.idxmin())
    peak_trough_ratio = float(hourly_pct.max() / hourly_pct.min())

    findings["hourly_activity"] = {
        "peak_hour": peak_hour,
        "peak_pct": float(hourly_pct.max()),
        "trough_hour": trough_hour,
        "trough_pct": float(hourly_pct.min()),
        "peak_trough_ratio": round(peak_trough_ratio, 2),
        "hourly_distribution": {str(h): float(p) for h, p in hourly_pct.items()},
    }

    print(f"    Peak hour: {peak_hour}:00 ({hourly_pct.max():.1f}% of all tx)")
    print(f"    Trough hour: {trough_hour}:00 ({hourly_pct.min():.1f}% of all tx)")
    print(f"    Peak/trough ratio: {peak_trough_ratio:.1f}x")
    print(f"    -> {'Strong' if peak_trough_ratio > 3 else 'Moderate'} hourly pattern")

    # Check if merchants have DIFFERENT hourly patterns
    merchant_peak_hours = hourly.loc[
        hourly.groupby(COLUMN_MERCHANT)["tx_count"].idxmax()
    ]["hour"]
    peak_hour_std = float(merchant_peak_hours.std())
    findings["hourly_activity"]["merchant_peak_hour_std"] = round(peak_hour_std, 2)
    print(f"    Merchant peak hour std: {peak_hour_std:.2f}")
    print(f"    -> Merchants {'vary significantly' if peak_hour_std > 3 else 'share similar'} peak hours")

    # --- C. Day-of-week analysis ---
    print("\n  C. Day-of-Week Analysis")
    dow = df.groupby("day_of_week").size()
    dow_pct = (dow / dow.sum() * 100).round(2)
    dow_cv = float(dow.std() / dow.mean())

    findings["day_of_week"] = {
        "distribution": {str(d): float(p) for d, p in dow_pct.items()},
        "coefficient_of_variation": round(dow_cv, 3),
        "weekday_vs_weekend": {
            "weekday_avg_pct": round(float(dow_pct.iloc[:5].mean()), 2),
            "weekend_avg_pct": round(float(dow_pct.iloc[5:].mean()), 2),
        }
    }

    print(f"    Day-of-week CV: {dow_cv:.3f}")
    wd = dow_pct.iloc[:5].mean()
    we = dow_pct.iloc[5:].mean()
    print(f"    Weekday avg: {wd:.1f}%, Weekend avg: {we:.1f}%")
    print(f"    -> Day-of-week {'matters' if dow_cv > 0.05 else 'has minimal impact'}")

    # CONCLUSION
    conclusion = []
    if peak_trough_ratio > 3:
        conclusion.append("Hour-of-day significantly affects activity -> hour-aware baselines recommended")
    else:
        conclusion.append("Hourly patterns moderate -> simple daily baselines may suffice")
    if dow_cv > 0.05:
        conclusion.append("Day-of-week shows some variation -> consider as context")
    else:
        conclusion.append("Day-of-week variation minimal -> not a priority signal")

    findings["rhythm_conclusion"] = conclusion
    for c in conclusion:
        print(f"\n  CONCLUSION: {c}")

    save_finding("area1_merchant_rhythms", findings)
    return findings


# =====================================================================
# ANALYSIS AREA 2: OBSERVATION WINDOW DISCOVERY
# =====================================================================

def analyze_observation_windows(df: pd.DataFrame) -> dict:
    """
    Design question: What time resolution captures meaningful behavioral
    changes while providing enough transactions for stable analysis?
    """
    print_section("AREA 2: OBSERVATION WINDOW DISCOVERY")
    findings = {}

    # Test 3 candidate windows: 1-hour, 4-hour, daily
    windows = {
        "1h": "1h",
        "4h": "4h",
        "1d": "1D",
    }

    for label, freq in windows.items():
        print(f"\n  Window: {label}")

        # Group by merchant + time window
        windowed = df.set_index(COLUMN_TIMESTAMP).groupby(
            [COLUMN_MERCHANT, pd.Grouper(freq=freq)]
        ).agg(
            tx_count=(COLUMN_AMOUNT, "count"),
            total_amount=(COLUMN_AMOUNT, "sum"),
            avg_amount=(COLUMN_AMOUNT, "mean"),
            fraud_count=(COLUMN_IS_FRAUD, "sum"),
        ).reset_index()

        # Only non-zero windows
        active_windows = windowed[windowed["tx_count"] > 0]

        stats_dict = {
            "total_windows": len(active_windows),
            "tx_per_window": {
                "mean": round(float(active_windows["tx_count"].mean()), 2),
                "median": float(active_windows["tx_count"].median()),
                "p5": float(active_windows["tx_count"].quantile(0.05)),
                "p25": float(active_windows["tx_count"].quantile(0.25)),
                "p75": float(active_windows["tx_count"].quantile(0.75)),
                "p95": float(active_windows["tx_count"].quantile(0.95)),
                "max": float(active_windows["tx_count"].max()),
            },
            "windows_with_1_tx_pct": round(
                float((active_windows["tx_count"] == 1).mean() * 100), 1
            ),
            "windows_with_fraud": int((active_windows["fraud_count"] > 0).sum()),
            "pct_windows_with_fraud": round(
                float((active_windows["fraud_count"] > 0).mean() * 100), 2
            ),
        }

        findings[label] = stats_dict

        print(f"    Active windows: {stats_dict['total_windows']:,}")
        print(f"    Avg tx/window: {stats_dict['tx_per_window']['mean']}")
        print(f"    Median tx/window: {stats_dict['tx_per_window']['median']}")
        print(f"    Single-tx windows: {stats_dict['windows_with_1_tx_pct']}%")
        print(f"    Windows with fraud: {stats_dict['windows_with_fraud']:,} ({stats_dict['pct_windows_with_fraud']}%)")

    # CONCLUSION
    # Choose the window with enough tx for stable stats but granular enough
    print("\n  WINDOW COMPARISON:")
    for label in windows:
        f = findings[label]
        stability = "UNSTABLE" if f["tx_per_window"]["median"] < 2 else (
            "MARGINAL" if f["tx_per_window"]["median"] < 5 else "STABLE"
        )
        print(f"    {label}: median={f['tx_per_window']['median']} tx/window -> {stability}")

    # Determine recommended window
    if findings["1h"]["tx_per_window"]["median"] >= 2:
        recommended = "1h"
        reason = "Hourly provides sufficient granularity with stable tx counts"
    elif findings["4h"]["tx_per_window"]["median"] >= 3:
        recommended = "4h"
        reason = "4-hour needed for stable tx counts; hourly too sparse"
    else:
        recommended = "1d"
        reason = "Daily is the only window with reliable tx counts"

    findings["recommendation"] = {
        "window": recommended,
        "reason": reason,
    }

    print(f"\n  RECOMMENDATION: {recommended} ({reason})")

    save_finding("area2_observation_windows", findings)
    return findings


# =====================================================================
# ANALYSIS AREA 3: MERCHANT BASELINE STABILITY
# =====================================================================

def analyze_baseline_stability(df: pd.DataFrame) -> dict:
    """
    Design question: Is merchant behavior stable enough for historical
    baselines? Should we use global, rolling, or time-aware baselines?
    """
    print_section("AREA 3: MERCHANT BASELINE STABILITY")
    findings = {}

    # Classify merchants by activity level
    merchant_total = df.groupby(COLUMN_MERCHANT).size()
    terciles = merchant_total.quantile([0.33, 0.67])
    low_thresh = float(terciles.iloc[0])
    high_thresh = float(terciles.iloc[1])

    low_merchants = merchant_total[merchant_total <= low_thresh].index[:5]
    mid_merchants = merchant_total[
        (merchant_total > low_thresh) & (merchant_total <= high_thresh)
    ].index[:5]
    high_merchants = merchant_total[merchant_total > high_thresh].index[:5]

    categories = {
        "low_activity": list(low_merchants),
        "medium_activity": list(mid_merchants),
        "high_activity": list(high_merchants),
    }

    # Analyze stability across monthly windows
    df_temp = df.copy()
    df_temp["month"] = df_temp[COLUMN_TIMESTAMP].dt.to_period("M")

    stability_results = {}
    for cat_name, merchants in categories.items():
        cat_stats = []
        for m in merchants:
            m_data = df_temp[df_temp[COLUMN_MERCHANT] == m]
            monthly = m_data.groupby("month").agg(
                tx_count=(COLUMN_AMOUNT, "count"),
                avg_amount=(COLUMN_AMOUNT, "mean"),
            )
            if len(monthly) > 1:
                tx_cv = float(monthly["tx_count"].std() / monthly["tx_count"].mean())
                amt_cv = float(monthly["avg_amount"].std() / monthly["avg_amount"].mean())
            else:
                tx_cv = 0.0
                amt_cv = 0.0
            cat_stats.append({
                "merchant": m,
                "months_active": len(monthly),
                "tx_count_cv": round(tx_cv, 3),
                "avg_amount_cv": round(amt_cv, 3),
            })
        stability_results[cat_name] = cat_stats

    findings["merchant_stability"] = stability_results

    # Overall stability assessment
    all_cvs = []
    for cat_stats in stability_results.values():
        for ms in cat_stats:
            all_cvs.append(ms["tx_count_cv"])

    avg_tx_cv = np.mean(all_cvs)
    findings["overall_tx_cv"] = round(float(avg_tx_cv), 3)

    print(f"  Avg monthly tx count CV (sample): {avg_tx_cv:.3f}")
    for cat_name, cat_stats in stability_results.items():
        print(f"\n  {cat_name}:")
        for ms in cat_stats:
            print(f"    {ms['merchant'][:30]:30s} | months={ms['months_active']} | tx_cv={ms['tx_count_cv']:.3f} | amt_cv={ms['avg_amount_cv']:.3f}")

    # Test: does a rolling window outperform global for prediction?
    # Use last 30 days vs all history for a sample merchant
    print("\n  Rolling vs Global Baseline Test:")
    sample_merchant = high_merchants[0]
    m_data = df[df[COLUMN_MERCHANT] == sample_merchant].sort_values(COLUMN_TIMESTAMP)
    m_daily = m_data.groupby("date").size().reset_index(name="tx_count")

    if len(m_daily) > 60:
        # Global baseline: mean of first 80% of days
        split_idx = int(len(m_daily) * 0.8)
        global_mean = m_daily["tx_count"].iloc[:split_idx].mean()
        test_days = m_daily.iloc[split_idx:]
        global_mae = float(np.abs(test_days["tx_count"] - global_mean).mean())

        # Rolling 30-day baseline
        rolling_mean = m_daily["tx_count"].rolling(30, min_periods=7).mean()
        rolling_pred = rolling_mean.iloc[split_idx - 1:-1].values
        actual = test_days["tx_count"].values[:len(rolling_pred)]
        rolling_mae = float(np.abs(actual - rolling_pred).mean())

        findings["rolling_vs_global"] = {
            "merchant": sample_merchant,
            "global_mae": round(global_mae, 2),
            "rolling_30d_mae": round(rolling_mae, 2),
            "rolling_better": rolling_mae < global_mae,
            "improvement_pct": round((1 - rolling_mae / global_mae) * 100, 1) if global_mae > 0 else 0,
        }
        print(f"    Merchant: {sample_merchant}")
        print(f"    Global MAE: {global_mae:.2f}")
        print(f"    Rolling 30d MAE: {rolling_mae:.2f}")
        print(f"    -> Rolling {'better' if rolling_mae < global_mae else 'worse'} by {abs(1 - rolling_mae/global_mae)*100:.1f}%")

    # CONCLUSION
    if avg_tx_cv < 0.3:
        baseline_rec = "Global merchant history sufficient; low month-to-month variation"
    elif avg_tx_cv < 0.5:
        baseline_rec = "Rolling window recommended; moderate variation over time"
    else:
        baseline_rec = "Rolling window essential; high temporal variation"

    findings["baseline_recommendation"] = baseline_rec
    print(f"\n  CONCLUSION: {baseline_rec}")

    save_finding("area3_baseline_stability", findings)
    return findings


# =====================================================================
# ANALYSIS AREA 4: TRANSACTION AMOUNT BEHAVIOR
# =====================================================================

def analyze_amount_behavior(df: pd.DataFrame) -> dict:
    """
    Design question: Does amount behavior add meaningful context
    beyond transaction count for burst detection?
    """
    print_section("AREA 4: TRANSACTION AMOUNT BEHAVIOR")
    findings = {}

    # Overall amount distribution
    amt = df[COLUMN_AMOUNT]
    findings["overall_amount"] = {
        "mean": round(float(amt.mean()), 2),
        "median": round(float(amt.median()), 2),
        "std": round(float(amt.std()), 2),
        "p5": round(float(amt.quantile(0.05)), 2),
        "p95": round(float(amt.quantile(0.95)), 2),
        "max": round(float(amt.max()), 2),
    }
    print(f"  Overall: mean=${amt.mean():.2f}, median=${amt.median():.2f}, std=${amt.std():.2f}")

    # Compare fraud vs legit amount distributions
    fraud_amt = df[df[COLUMN_IS_FRAUD] == 1][COLUMN_AMOUNT]
    legit_amt = df[df[COLUMN_IS_FRAUD] == 0][COLUMN_AMOUNT]

    findings["fraud_vs_legit_amount"] = {
        "fraud_mean": round(float(fraud_amt.mean()), 2),
        "fraud_median": round(float(fraud_amt.median()), 2),
        "legit_mean": round(float(legit_amt.mean()), 2),
        "legit_median": round(float(legit_amt.median()), 2),
        "mean_ratio": round(float(fraud_amt.mean() / legit_amt.mean()), 2),
    }

    print(f"\n  Fraud amount:  mean=${fraud_amt.mean():.2f}, median=${fraud_amt.median():.2f}")
    print(f"  Legit amount:  mean=${legit_amt.mean():.2f}, median=${legit_amt.median():.2f}")
    print(f"  Fraud/legit mean ratio: {fraud_amt.mean()/legit_amt.mean():.2f}x")

    # Per-merchant amount variability
    merchant_amt = df.groupby(COLUMN_MERCHANT)[COLUMN_AMOUNT].agg(["mean", "std"])
    merchant_amt["cv"] = merchant_amt["std"] / merchant_amt["mean"]

    findings["merchant_amount_variability"] = {
        "avg_cv": round(float(merchant_amt["cv"].mean()), 3),
        "median_cv": round(float(merchant_amt["cv"].median()), 3),
    }
    print(f"\n  Merchant amount CV: avg={merchant_amt['cv'].mean():.3f}, median={merchant_amt['cv'].median():.3f}")

    # Does amount deviation during high-activity windows differ from low?
    daily = df.groupby([COLUMN_MERCHANT, "date"]).agg(
        tx_count=(COLUMN_AMOUNT, "count"),
        avg_amount=(COLUMN_AMOUNT, "mean"),
        total_amount=(COLUMN_AMOUNT, "sum"),
    ).reset_index()

    # Per-merchant: compare amount in top-10% activity days vs bottom-50%
    amount_during_bursts = []
    for m in df[COLUMN_MERCHANT].unique()[:50]:  # Sample 50 merchants
        m_daily = daily[daily[COLUMN_MERCHANT] == m]
        if len(m_daily) < 20:
            continue
        p90 = m_daily["tx_count"].quantile(0.90)
        p50 = m_daily["tx_count"].quantile(0.50)
        high_days = m_daily[m_daily["tx_count"] >= p90]["avg_amount"]
        normal_days = m_daily[m_daily["tx_count"] <= p50]["avg_amount"]
        if len(high_days) > 0 and len(normal_days) > 0:
            amount_during_bursts.append({
                "high_day_avg_amount": float(high_days.mean()),
                "normal_day_avg_amount": float(normal_days.mean()),
                "ratio": float(high_days.mean() / normal_days.mean()) if normal_days.mean() > 0 else 1.0,
            })

    if amount_during_bursts:
        ratios = [x["ratio"] for x in amount_during_bursts]
        avg_ratio = np.mean(ratios)
        findings["amount_during_high_activity"] = {
            "avg_amount_ratio_high_vs_normal": round(float(avg_ratio), 3),
            "merchants_sampled": len(amount_during_bursts),
        }
        print(f"\n  Amount during high-activity days vs normal:")
        print(f"    Avg ratio: {avg_ratio:.3f} (sample of {len(amount_during_bursts)} merchants)")
        print(f"    -> Amount {'changes meaningfully' if abs(avg_ratio - 1.0) > 0.1 else 'stays similar'} during high-activity periods")

    # KS test: fraud vs legit amount distributions
    ks_stat, ks_pvalue = stats.ks_2samp(
        fraud_amt.sample(min(5000, len(fraud_amt)), random_state=42),
        legit_amt.sample(5000, random_state=42),
    )
    findings["ks_test_fraud_vs_legit"] = {
        "ks_statistic": round(float(ks_stat), 4),
        "p_value": float(ks_pvalue),
        "distributions_differ": ks_pvalue < 0.01,
    }
    print(f"\n  KS test (fraud vs legit amounts): stat={ks_stat:.4f}, p={ks_pvalue:.2e}")
    print(f"  -> Distributions {'significantly different' if ks_pvalue < 0.01 else 'similar'}")

    # CONCLUSION
    is_useful = (
        findings["fraud_vs_legit_amount"]["mean_ratio"] > 1.5
        or findings["ks_test_fraud_vs_legit"]["distributions_differ"]
    )
    findings["conclusion"] = {
        "amount_is_useful_signal": is_useful,
        "reason": "Fraud amounts differ significantly from legitimate" if is_useful
        else "Amount patterns do not strongly differentiate fraud from legitimate"
    }
    print(f"\n  CONCLUSION: Amount as signal -> {'CORE/SUPPORTING' if is_useful else 'WEAK'}")
    print(f"    {findings['conclusion']['reason']}")

    save_finding("area4_amount_behavior", findings)
    return findings


# =====================================================================
# ANALYSIS AREA 5: ACTIVITY CONCENTRATION
# =====================================================================

def analyze_activity_concentration(df: pd.DataFrame) -> dict:
    """
    Design question: Does suspicious/fraudulent activity demonstrate
    temporal concentration?
    """
    print_section("AREA 5: ACTIVITY CONCENTRATION")
    findings = {}

    # Hourly windows with fraud concentration
    hourly = df.set_index(COLUMN_TIMESTAMP).groupby(
        [COLUMN_MERCHANT, pd.Grouper(freq="1h")]
    ).agg(
        tx_count=(COLUMN_AMOUNT, "count"),
        fraud_count=(COLUMN_IS_FRAUD, "sum"),
        unique_cards=(COLUMN_CC_NUM, "nunique"),
    ).reset_index()

    active = hourly[hourly["tx_count"] > 0].copy()
    active["fraud_rate"] = active["fraud_count"] / active["tx_count"]
    active["has_fraud"] = active["fraud_count"] > 0

    # Compare activity level in fraud-containing windows vs clean
    fraud_windows = active[active["has_fraud"]]
    clean_windows = active[~active["has_fraud"]]

    findings["fraud_window_activity"] = {
        "fraud_windows_count": len(fraud_windows),
        "clean_windows_count": len(clean_windows),
        "fraud_window_avg_tx": round(float(fraud_windows["tx_count"].mean()), 2),
        "clean_window_avg_tx": round(float(clean_windows["tx_count"].mean()), 2),
        "fraud_window_avg_cards": round(float(fraud_windows["unique_cards"].mean()), 2),
        "clean_window_avg_cards": round(float(clean_windows["unique_cards"].mean()), 2),
    }

    print(f"  Fraud-containing windows: {len(fraud_windows):,}")
    print(f"  Clean windows: {len(clean_windows):,}")
    print(f"  Avg tx in fraud windows: {fraud_windows['tx_count'].mean():.1f}")
    print(f"  Avg tx in clean windows: {clean_windows['tx_count'].mean():.1f}")
    print(f"  Avg unique cards (fraud): {fraud_windows['unique_cards'].mean():.1f}")
    print(f"  Avg unique cards (clean): {clean_windows['unique_cards'].mean():.1f}")

    # Does high activity correlate with higher fraud rate?
    active["activity_percentile"] = active["tx_count"].rank(pct=True)

    low_activity = active[active["activity_percentile"] <= 0.5]
    high_activity = active[active["activity_percentile"] >= 0.9]

    low_fraud_rate = float(low_activity["has_fraud"].mean() * 100)
    high_fraud_rate = float(high_activity["has_fraud"].mean() * 100)

    findings["activity_vs_fraud"] = {
        "low_activity_fraud_pct": round(low_fraud_rate, 3),
        "high_activity_fraud_pct": round(high_fraud_rate, 3),
        "ratio": round(high_fraud_rate / low_fraud_rate, 2) if low_fraud_rate > 0 else 0,
    }

    print(f"\n  Fraud prevalence by activity level:")
    print(f"    Bottom 50% activity: {low_fraud_rate:.3f}% windows contain fraud")
    print(f"    Top 10% activity:    {high_fraud_rate:.3f}% windows contain fraud")
    if low_fraud_rate > 0:
        print(f"    Ratio: {high_fraud_rate/low_fraud_rate:.2f}x")

    # Unique cardholder analysis
    active["cards_per_tx"] = active["unique_cards"] / active["tx_count"]
    fraud_cpt = fraud_windows["unique_cards"].sum() / fraud_windows["tx_count"].sum()
    clean_cpt = clean_windows["unique_cards"].sum() / clean_windows["tx_count"].sum()

    findings["cardholder_concentration"] = {
        "fraud_unique_cards_per_tx": round(float(fraud_cpt), 3),
        "clean_unique_cards_per_tx": round(float(clean_cpt), 3),
    }
    print(f"\n  Unique cards per transaction:")
    print(f"    Fraud windows: {fraud_cpt:.3f}")
    print(f"    Clean windows: {clean_cpt:.3f}")

    # CONCLUSION
    concentration_useful = (
        findings["activity_vs_fraud"]["ratio"] > 1.5
        if findings["activity_vs_fraud"]["ratio"] > 0 else False
    )
    findings["conclusion"] = {
        "concentration_is_signal": concentration_useful,
        "reason": "High-activity periods show elevated fraud rate" if concentration_useful
        else "Fraud distribution does not strongly concentrate in high-activity windows"
    }
    print(f"\n  CONCLUSION: Temporal concentration -> {'USEFUL' if concentration_useful else 'WEAK'}")

    save_finding("area5_activity_concentration", findings)
    return findings


# =====================================================================
# ANALYSIS AREA 6: FRAUD CONTEXT
# =====================================================================

def analyze_fraud_context(df: pd.DataFrame) -> dict:
    """
    Design question: Can transaction-level fraud labels support
    a reasonable burst-event evaluation strategy?
    """
    print_section("AREA 6: FRAUD CONTEXT")
    findings = {}

    # Fraud distribution across merchants
    merchant_fraud = df.groupby(COLUMN_MERCHANT).agg(
        total_tx=(COLUMN_AMOUNT, "count"),
        fraud_tx=(COLUMN_IS_FRAUD, "sum"),
    )
    merchant_fraud["fraud_rate"] = merchant_fraud["fraud_tx"] / merchant_fraud["total_tx"]

    findings["merchant_fraud_distribution"] = {
        "merchants_with_fraud": int((merchant_fraud["fraud_tx"] > 0).sum()),
        "merchants_without_fraud": int((merchant_fraud["fraud_tx"] == 0).sum()),
        "avg_merchant_fraud_rate": round(float(merchant_fraud["fraud_rate"].mean() * 100), 4),
        "max_merchant_fraud_rate": round(float(merchant_fraud["fraud_rate"].max() * 100), 2),
        "fraud_rate_std": round(float(merchant_fraud["fraud_rate"].std() * 100), 4),
    }

    print(f"  Merchants with fraud: {(merchant_fraud['fraud_tx'] > 0).sum()}/{len(merchant_fraud)}")
    print(f"  Avg merchant fraud rate: {merchant_fraud['fraud_rate'].mean()*100:.4f}%")
    print(f"  Max merchant fraud rate: {merchant_fraud['fraud_rate'].max()*100:.2f}%")

    # Fraud over time
    daily_fraud = df.groupby("date").agg(
        total_tx=(COLUMN_AMOUNT, "count"),
        fraud_tx=(COLUMN_IS_FRAUD, "sum"),
    )
    daily_fraud["fraud_rate"] = daily_fraud["fraud_tx"] / daily_fraud["total_tx"]

    findings["temporal_fraud"] = {
        "avg_daily_fraud": round(float(daily_fraud["fraud_tx"].mean()), 1),
        "daily_fraud_std": round(float(daily_fraud["fraud_tx"].std()), 1),
        "daily_fraud_rate_cv": round(float(daily_fraud["fraud_rate"].std() / daily_fraud["fraud_rate"].mean()), 3),
    }

    print(f"\n  Avg daily fraud tx: {daily_fraud['fraud_tx'].mean():.1f}")
    print(f"  Daily fraud std: {daily_fraud['fraud_tx'].std():.1f}")

    # KEY QUESTION: Is fraud rate higher during behavioral anomalies?
    # Define "anomaly" as merchant-day with tx_count > merchant's 90th percentile
    daily_merchant = df.groupby([COLUMN_MERCHANT, "date"]).agg(
        tx_count=(COLUMN_AMOUNT, "count"),
        fraud_count=(COLUMN_IS_FRAUD, "sum"),
    ).reset_index()

    merchant_p90 = daily_merchant.groupby(COLUMN_MERCHANT)["tx_count"].quantile(0.90)
    daily_merchant = daily_merchant.merge(
        merchant_p90.rename("p90_threshold"),
        on=COLUMN_MERCHANT,
    )
    daily_merchant["is_high_activity"] = daily_merchant["tx_count"] > daily_merchant["p90_threshold"]

    high_activity_days = daily_merchant[daily_merchant["is_high_activity"]]
    normal_days = daily_merchant[~daily_merchant["is_high_activity"]]

    high_fraud_rate = float(high_activity_days["fraud_count"].sum() / high_activity_days["tx_count"].sum() * 100)
    normal_fraud_rate = float(normal_days["fraud_count"].sum() / normal_days["tx_count"].sum() * 100)

    findings["fraud_during_anomalies"] = {
        "high_activity_days": len(high_activity_days),
        "normal_days": len(normal_days),
        "fraud_rate_during_high_activity": round(high_fraud_rate, 4),
        "fraud_rate_during_normal": round(normal_fraud_rate, 4),
        "ratio": round(high_fraud_rate / normal_fraud_rate, 2) if normal_fraud_rate > 0 else 0,
    }

    print(f"\n  CRITICAL QUESTION: Is fraud rate higher during high-activity days?")
    print(f"    High-activity days (>p90 for merchant): {len(high_activity_days):,}")
    print(f"    Normal days: {len(normal_days):,}")
    print(f"    Fraud rate during high activity: {high_fraud_rate:.4f}%")
    print(f"    Fraud rate during normal:        {normal_fraud_rate:.4f}%")
    if normal_fraud_rate > 0:
        print(f"    Ratio: {high_fraud_rate/normal_fraud_rate:.2f}x")

    # Evaluation strategy feasibility
    # Can we create burst-level labels from tx-level labels?
    hourly_merchant = df.set_index(COLUMN_TIMESTAMP).groupby(
        [COLUMN_MERCHANT, pd.Grouper(freq="1h")]
    ).agg(
        tx_count=(COLUMN_AMOUNT, "count"),
        fraud_count=(COLUMN_IS_FRAUD, "sum"),
    ).reset_index()

    active_windows = hourly_merchant[hourly_merchant["tx_count"] > 0]
    windows_with_fraud = active_windows[active_windows["fraud_count"] > 0]

    # A "suspicious window" could be defined as fraud_count > 0 AND fraud_rate above some threshold
    windows_with_high_fraud = active_windows[
        (active_windows["fraud_count"] > 0) &
        (active_windows["fraud_count"] / active_windows["tx_count"] > 0.1)
    ]

    findings["evaluation_feasibility"] = {
        "total_hourly_windows": len(active_windows),
        "windows_with_any_fraud": len(windows_with_fraud),
        "windows_with_high_fraud_rate": len(windows_with_high_fraud),
        "pct_with_any_fraud": round(float(len(windows_with_fraud) / len(active_windows) * 100), 2),
        "pct_with_high_fraud": round(float(len(windows_with_high_fraud) / len(active_windows) * 100), 3),
    }

    print(f"\n  Evaluation feasibility:")
    print(f"    Total hourly windows: {len(active_windows):,}")
    print(f"    Windows with any fraud: {len(windows_with_fraud):,} ({len(windows_with_fraud)/len(active_windows)*100:.2f}%)")
    print(f"    Windows with >10% fraud rate: {len(windows_with_high_fraud):,} ({len(windows_with_high_fraud)/len(active_windows)*100:.3f}%)")

    # CONCLUSION
    findings["conclusion"] = {
        "labels_usable": len(windows_with_fraud) > 100,
        "strategy": (
            "Window-level evaluation possible: define suspicious windows as those "
            "with fraud concentration above merchant baseline fraud rate. "
            "Sufficient fraud-containing windows exist for held-out evaluation."
            if len(windows_with_fraud) > 100
            else "Insufficient fraud windows for reliable burst-level evaluation."
        ),
        "honest_limitation": (
            "Transaction-level fraud labels do not directly equal burst labels. "
            "A window containing fraud transactions is not necessarily a 'burst'. "
            "Our evaluation measures whether behavioral anomalies correlate with "
            "fraud-containing periods, not whether every flagged burst is an attack."
        ),
    }

    print(f"\n  CONCLUSION:")
    print(f"    {findings['conclusion']['strategy']}")
    print(f"    LIMITATION: {findings['conclusion']['honest_limitation']}")

    save_finding("area6_fraud_context", findings)
    return findings


# =====================================================================
# ANALYSIS AREA 7: BEHAVIORAL SIGNAL SELECTION
# =====================================================================

def analyze_signal_selection(
    df: pd.DataFrame,
    rhythm_findings: dict,
    window_findings: dict,
    amount_findings: dict,
    concentration_findings: dict,
    fraud_findings: dict,
) -> dict:
    """
    Evaluate every candidate signal based on prior analyses.
    """
    print_section("AREA 7: BEHAVIORAL SIGNAL SELECTION")

    signals = {}

    # 1. Transaction velocity
    signals["transaction_velocity"] = {
        "decision": "CORE",
        "reason": "Directly represents burst intensity. Hourly tx count deviation from baseline is the primary burst indicator.",
        "evidence": f"Median hourly tx/window = {window_findings.get('1h', {}).get('tx_per_window', {}).get('median', 'N/A')}",
    }

    # 2. Total amount per window
    amt_useful = amount_findings.get("conclusion", {}).get("amount_is_useful_signal", False)
    amt_ratio = amount_findings.get("fraud_vs_legit_amount", {}).get("mean_ratio", 1.0)
    signals["total_amount"] = {
        "decision": "CORE" if amt_useful else "SUPPORTING",
        "reason": f"Fraud amounts differ by {amt_ratio}x from legitimate. Adds value context to velocity.",
        "evidence": f"KS test significant: {amount_findings.get('ks_test_fraud_vs_legit', {}).get('distributions_differ', 'N/A')}",
    }

    # 3. Average amount per window
    signals["avg_amount"] = {
        "decision": "SUPPORTING",
        "reason": "Derived from total_amount and tx_count. Useful for detecting unusual per-transaction values but redundant with total_amount as a standalone signal.",
    }

    # 4. Amount deviation (std within window)
    signals["amount_std"] = {
        "decision": "SUPPORTING",
        "reason": "High uniformity of amounts within a burst (low std) may indicate automated activity. Useful but secondary.",
    }

    # 5. Hour-of-day context
    peak_ratio = rhythm_findings.get("hourly_activity", {}).get("peak_trough_ratio", 1.0)
    signals["hour_of_day"] = {
        "decision": "CORE" if peak_ratio > 3 else "SUPPORTING",
        "reason": f"Peak/trough ratio is {peak_ratio}x. Activity at unusual hours for a merchant is a meaningful deviation signal." if peak_ratio > 3
        else f"Peak/trough ratio is {peak_ratio}x. Modest hourly variation; use as context only.",
    }

    # 6. Day-of-week
    dow_cv = rhythm_findings.get("day_of_week", {}).get("coefficient_of_variation", 0)
    signals["day_of_week"] = {
        "decision": "EXCLUDE" if dow_cv < 0.05 else "SUPPORTING",
        "reason": f"Day-of-week CV is {dow_cv}. {'Minimal variation; not worth the complexity.' if dow_cv < 0.05 else 'Some weekday/weekend difference; include as baseline context.'}",
    }

    # 7. Unique cardholder count
    conc = concentration_findings.get("cardholder_concentration", {})
    fraud_cpt = conc.get("fraud_unique_cards_per_tx", 0)
    clean_cpt = conc.get("clean_unique_cards_per_tx", 0)
    signals["unique_cardholders"] = {
        "decision": "SUPPORTING",
        "reason": f"Fraud windows: {fraud_cpt} unique cards/tx vs clean: {clean_cpt}. {'Different' if abs(fraud_cpt - clean_cpt) > 0.05 else 'Similar'} cardholder density.",
    }

    # 8. Category diversity
    # Quick analysis: does category distribution shift during fraud?
    fraud_cats = df[df[COLUMN_IS_FRAUD] == 1][COLUMN_CATEGORY].value_counts(normalize=True)
    legit_cats = df[df[COLUMN_IS_FRAUD] == 0][COLUMN_CATEGORY].value_counts(normalize=True)
    # Align indices
    all_cats = set(fraud_cats.index) | set(legit_cats.index)
    cat_diff = sum(abs(fraud_cats.get(c, 0) - legit_cats.get(c, 0)) for c in all_cats) / 2

    signals["category_diversity"] = {
        "decision": "EXCLUDE" if cat_diff < 0.15 else "SUPPORTING",
        "reason": f"Category distribution shift between fraud/legit: {cat_diff:.3f}. {'Minimal shift; not useful for burst detection.' if cat_diff < 0.15 else 'Some category shift; may add value.'}",
    }

    # 9. Transaction concentration (inter-arrival time)
    signals["temporal_concentration"] = {
        "decision": "SUPPORTING",
        "reason": "Within a burst window, compressed inter-arrival times may indicate automated activity. Worth tracking as secondary signal.",
    }

    # Print signal table
    print(f"\n  {'Signal':<25s} | {'Decision':<12s} | Reason")
    print(f"  {'-'*25}-+-{'-'*12}-+-{'-'*50}")
    for name, info in signals.items():
        print(f"  {name:<25s} | {info['decision']:<12s} | {info['reason'][:80]}")

    # Summary counts
    core = [s for s, i in signals.items() if i["decision"] == "CORE"]
    supporting = [s for s, i in signals.items() if i["decision"] == "SUPPORTING"]
    excluded = [s for s, i in signals.items() if i["decision"] == "EXCLUDE"]

    findings = {
        "signals": signals,
        "summary": {
            "core_signals": core,
            "supporting_signals": supporting,
            "excluded_signals": excluded,
        }
    }

    print(f"\n  CORE ({len(core)}): {', '.join(core)}")
    print(f"  SUPPORTING ({len(supporting)}): {', '.join(supporting)}")
    print(f"  EXCLUDED ({len(excluded)}): {', '.join(excluded)}")

    save_finding("area7_signal_selection", findings)
    return findings


# =====================================================================
# MAIN EXECUTION
# =====================================================================

def run_phase_2():
    """Execute the complete Phase 2 analysis pipeline."""
    print_section("PAYMENT BURST SENTINEL - PHASE 2: EXPLORATORY ANALYSIS")
    print("\n  Purpose: Discover what 'normal payment rhythm' looks like")
    print("  and how a meaningful burst should be defined.")
    print("\n  NO detection logic. NO baselines. NO UI.")
    print("  Analysis only. Evidence-driven decisions.")

    # Load data
    print("\n  Loading processed training data...")
    df = load_train_data()
    print(f"  Loaded {len(df):,} transactions")

    # Run all 7 analysis areas
    rhythm = analyze_merchant_rhythms(df)
    windows = analyze_observation_windows(df)
    stability = analyze_baseline_stability(df)
    amounts = analyze_amount_behavior(df)
    concentration = analyze_activity_concentration(df)
    fraud = analyze_fraud_context(df)
    signals = analyze_signal_selection(df, rhythm, windows, amounts, concentration, fraud)

    # Phase 3 Input Contract
    print_section("PHASE 3 INPUT CONTRACT")

    rec_window = windows.get("recommendation", {}).get("window", "1h")

    contract = {
        "input": "Processed parquet files from Phase 1",
        "grouping": "Per-merchant",
        "temporal_context": "Hour-of-day awareness" if rhythm.get("hourly_activity", {}).get("peak_trough_ratio", 1) > 3 else "Daily aggregation",
        "observation_window": rec_window,
        "baseline_approach": stability.get("baseline_recommendation", "To be determined"),
        "core_signals": signals.get("summary", {}).get("core_signals", []),
        "supporting_signals": signals.get("summary", {}).get("supporting_signals", []),
        "excluded_signals": signals.get("summary", {}).get("excluded_signals", []),
        "output": "Per-merchant expected behavioral ranges for each signal",
        "evaluation_strategy": fraud.get("conclusion", {}).get("strategy", "To be determined"),
        "limitations": fraud.get("conclusion", {}).get("honest_limitation", ""),
    }

    save_finding("phase3_input_contract", contract)

    print(f"  INPUT:              {contract['input']}")
    print(f"  GROUPING:           {contract['grouping']}")
    print(f"  TEMPORAL CONTEXT:   {contract['temporal_context']}")
    print(f"  OBSERVATION WINDOW: {contract['observation_window']}")
    print(f"  BASELINE APPROACH:  {contract['baseline_approach']}")
    print(f"  CORE SIGNALS:       {', '.join(contract['core_signals'])}")
    print(f"  SUPPORTING SIGNALS: {', '.join(contract['supporting_signals'])}")
    print(f"  EXCLUDED:           {', '.join(contract['excluded_signals'])}")
    print(f"  OUTPUT:             {contract['output']}")

    print(f"\n{'='*70}")
    print(f"  Phase 2 - Exploratory Analysis - COMPLETE")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    run_phase_2()
