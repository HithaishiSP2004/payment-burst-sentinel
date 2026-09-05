"""
Payment Burst Sentinel — FastAPI Backend
==========================================
Serves the locked Phase 4 detection outputs to the frontend.
Uses real processed data only. No fake metrics.
"""

import json
import os
from pathlib import Path
from typing import Optional, List

import pandas as pd
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Paths & Environment ───────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Auto-load .env from PROJECT_ROOT if present
_env_path = PROJECT_ROOT / ".env"
if _env_path.exists():
    try:
        with open(_env_path, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    _k, _v = _k.strip(), _v.strip().strip("'\"")
                    if _k and _k not in os.environ:
                        os.environ[_k] = _v
    except Exception:
        pass

DATA_DIR = PROJECT_ROOT / "data" / "processed"
ANOMALIES_DIR = DATA_DIR / "anomalies"
EVALUATION_DIR = DATA_DIR / "evaluation"
BASELINES_DIR = DATA_DIR / "baselines"

# ── CORS configuration ────────────────────────────────────────
# Production: set ALLOWED_ORIGINS=https://your-frontend.com,https://www.your-frontend.com
# Development: if unset, allows all origins for local development
_allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
_allowed_origins = [o.strip() for o in _allowed_origins_env.split(",") if o.strip()] if _allowed_origins_env else ["*"]

# ── Load data once at startup ──────────────────────────────────
app = FastAPI(
    title="Payment Burst Sentinel",
    description="Behavioral anomaly detection API — real data, honest results",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global data holders
_anomalies_df: Optional[pd.DataFrame] = None
_flagged_df: Optional[pd.DataFrame] = None
_baselines_df: Optional[pd.DataFrame] = None
_test_anomalies_df: Optional[pd.DataFrame] = None
_eval_report: Optional[dict] = None
_detection_policy: Optional[dict] = None


def get_anomalies():
    global _anomalies_df
    if _anomalies_df is None:
        path = ANOMALIES_DIR / "merchant_daily_anomalies.parquet"
        _anomalies_df = pd.read_parquet(path)
        _anomalies_df["date"] = pd.to_datetime(_anomalies_df["date"]).dt.strftime("%Y-%m-%d")
    return _anomalies_df


def get_flagged():
    global _flagged_df
    if _flagged_df is None:
        path = ANOMALIES_DIR / "flagged_events.parquet"
        _flagged_df = pd.read_parquet(path)
        _flagged_df["date"] = pd.to_datetime(_flagged_df["date"]).dt.strftime("%Y-%m-%d")
    return _flagged_df


def get_test_anomalies():
    global _test_anomalies_df
    if _test_anomalies_df is None:
        path = EVALUATION_DIR / "test_anomalies.parquet"
        _test_anomalies_df = pd.read_parquet(path)
        _test_anomalies_df["date"] = pd.to_datetime(_test_anomalies_df["date"]).dt.strftime("%Y-%m-%d")
    return _test_anomalies_df


def get_eval_report():
    global _eval_report
    if _eval_report is None:
        path = EVALUATION_DIR / "evaluation_report.json"
        with open(path) as f:
            _eval_report = json.load(f)
    return _eval_report


def get_detection_policy():
    global _detection_policy
    if _detection_policy is None:
        path = ANOMALIES_DIR / "detection_policy.json"
        with open(path) as f:
            _detection_policy = json.load(f)
    return _detection_policy


# ── API Routes ─────────────────────────────────────────────────

@app.get("/api/overview")
def get_overview():
    """System overview with real metrics from actual processed data."""
    df = get_anomalies()
    sufficient = df[df["baseline_status"] == "sufficient_history"]

    flagged = sufficient[sufficient["anomaly_type"] != "normal"]
    elevated = sufficient[sufficient["risk_level"] == "elevated"]
    high = sufficient[sufficient["risk_level"] == "high"]

    # Use test data for "current" metrics
    test_df = get_test_anomalies()
    test_suf = test_df[test_df["baseline_status"] == "sufficient_history"]
    test_flagged = test_suf[test_suf["anomaly_type"] != "normal"]

    eval_report = get_eval_report()

    return {
        "merchants_monitored": int(df["merchant"].nunique()),
        "total_merchant_days_analyzed": len(sufficient),
        "total_flagged_events": len(flagged),
        "elevated_events": len(elevated),
        "high_events": len(high),
        "test_period": {
            "merchant_days": len(test_suf),
            "flagged": len(test_flagged),
            "flagged_pct": round(len(test_flagged) / len(test_suf) * 100, 2) if len(test_suf) > 0 else 0,
        },
        "enrichment": {
            "vs_overall": eval_report["primary_results"]["flagged_vs_normal"]["enrichment_vs_overall"],
            "vs_normal": eval_report["primary_results"]["flagged_vs_normal"]["enrichment_vs_normal"],
        },
        "anomaly_types": {
            "velocity": int((flagged["anomaly_type"] == "velocity_anomaly").sum()),
            "amount": int((flagged["anomaly_type"] == "amount_anomaly").sum()),
            "combined": int((flagged["anomaly_type"] == "combined_anomaly").sum()),
        },
        "risk_distribution": {
            "normal": int((sufficient["risk_level"] == "normal").sum()),
            "elevated": int((sufficient["risk_level"] == "elevated").sum()),
            "high": int((sufficient["risk_level"] == "high").sum()),
        },
    }


@app.get("/api/investigations")
def get_investigations(
    risk_level: Optional[str] = Query(None, description="Filter: normal, elevated, high"),
    anomaly_type: Optional[str] = Query(None, description="Filter: velocity_anomaly, amount_anomaly, combined_anomaly"),
    merchant: Optional[str] = Query(None, description="Search by merchant name"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("composite_deviation", description="Sort field"),
    dataset: str = Query("test", description="Dataset: train or test"),
):
    """Retrieve flagged behavioral events for investigation."""
    if dataset == "test":
        df = get_test_anomalies()
    else:
        df = get_anomalies()

    sufficient = df[df["baseline_status"] == "sufficient_history"]
    flagged = sufficient[sufficient["anomaly_type"] != "normal"].copy()

    # Apply filters
    if risk_level:
        flagged = flagged[flagged["risk_level"] == risk_level]
    if anomaly_type:
        flagged = flagged[flagged["anomaly_type"] == anomaly_type]
    if merchant:
        flagged = flagged[flagged["merchant"].str.contains(merchant, case=False, na=False)]

    total = len(flagged)

    # Sort
    if sort_by in flagged.columns:
        flagged = flagged.sort_values(sort_by, ascending=False)

    # Paginate
    page = flagged.iloc[offset:offset + limit]

    events = []
    for _, row in page.iterrows():
        evidence_parts = []
        if row["amount_deviation"] >= 3.0:
            evidence_parts.append(
                f"Payment value (${row['total_amount']:.0f}) was significantly above "
                f"expected (~${row['expected_total_amount']:.0f})"
            )
        elif row["amount_deviation"] >= 1.0:
            evidence_parts.append(
                f"Payment value (${row['total_amount']:.0f}) was above expected (~${row['expected_total_amount']:.0f})"
            )

        if row["velocity_deviation"] >= 3.0:
            evidence_parts.append(
                f"Transaction count ({int(row['transaction_count'])}) was substantially above "
                f"expected (~{row['expected_tx_count']:.0f})"
            )
        elif row["velocity_deviation"] >= 1.0:
            evidence_parts.append(
                f"Transaction count ({int(row['transaction_count'])}) was above expected (~{row['expected_tx_count']:.0f})"
            )

        events.append({
            "merchant": row["merchant"],
            "date": row["date"],
            "risk_level": row["risk_level"],
            "anomaly_type": row["anomaly_type"],
            "transaction_count": int(row["transaction_count"]),
            "expected_tx_count": round(float(row["expected_tx_count"]), 1),
            "total_amount": round(float(row["total_amount"]), 2),
            "expected_total_amount": round(float(row["expected_total_amount"]), 2),
            "velocity_deviation": round(float(row["velocity_deviation"]), 2),
            "amount_deviation": round(float(row["amount_deviation"]), 2),
            "composite_deviation": round(float(row["composite_deviation"]), 2),
            "fraud_count": int(row.get("fraud_count", 0)),
            "evidence": evidence_parts,
        })

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "events": events,
    }


@app.get("/api/investigation/{merchant}/{date}")
def get_investigation_detail(merchant: str, date: str):
    """Detailed investigation view for one merchant-day event."""
    # Try test data first, then training
    for df_getter in [get_test_anomalies, get_anomalies]:
        df = df_getter()
        match = df[(df["merchant"] == merchant) & (df["date"] == date)]
        if len(match) > 0:
            break

    if len(match) == 0:
        raise HTTPException(404, f"No event found for {merchant} on {date}")

    row = match.iloc[0]

    # Primary evidence (amount)
    primary_evidence = {
        "signal": "Payment Value Deviation",
        "role": "PRIMARY",
        "observed": round(float(row["total_amount"]), 2),
        "expected": round(float(row["expected_total_amount"]), 2),
        "variability": round(float(row["total_amount_variability"]), 2),
        "deviation_mads": round(float(row["amount_deviation"]), 2),
    }

    # Behavioral context (velocity)
    behavioral_context = {
        "signal": "Transaction Volume Shift",
        "role": "CONTEXT",
        "observed": int(row["transaction_count"]),
        "expected": round(float(row["expected_tx_count"]), 1),
        "variability": round(float(row["tx_count_variability"]), 1),
        "deviation_mads": round(float(row["velocity_deviation"]), 2),
    }

    # Evidence statements
    statements = []
    if row["amount_deviation"] >= 3.0:
        statements.append(
            f"Total payment value (${row['total_amount']:.2f}) was significantly above "
            f"the expected range (expected ~${row['expected_total_amount']:.2f}, "
            f"variability ±${row['total_amount_variability']:.2f})."
        )
    elif row["amount_deviation"] >= 1.0:
        statements.append(
            f"Total payment value (${row['total_amount']:.2f}) was above this merchant's "
            f"expected level of ~${row['expected_total_amount']:.2f}."
        )

    if row["velocity_deviation"] >= 3.0:
        statements.append(
            f"Daily transaction count ({int(row['transaction_count'])}) was substantially above "
            f"this merchant's recent historical range (expected ~{row['expected_tx_count']:.0f})."
        )
    elif row["velocity_deviation"] >= 1.0:
        statements.append(
            f"Daily transaction count ({int(row['transaction_count'])}) was above expected "
            f"(~{row['expected_tx_count']:.0f})."
        )

    if row["anomaly_type"] == "combined_anomaly":
        statements.append(
            "Both payment value and transaction volume shifted together."
        )

    if row["anomaly_type"] == "normal":
        statements.append("Activity was within the expected behavioral range.")

    statements.append(
        "This system identifies unusual behavior. Investigation is required "
        "to determine the cause."
    )

    return {
        "merchant": row["merchant"],
        "date": row["date"],
        "risk_level": row["risk_level"],
        "anomaly_type": row["anomaly_type"],
        "composite_deviation": round(float(row["composite_deviation"]), 2),
        "primary_evidence": primary_evidence,
        "behavioral_context": behavioral_context,
        "evidence_statements": statements,
        "baseline_info": {
            "historical_days_used": int(row["historical_days_used"]),
            "baseline_window_days": int(row["baseline_window_days"]),
            "baseline_status": row["baseline_status"],
            "day_of_week": int(row["day_of_week"]),
        },
        "metadata": {
            "fraud_count": int(row.get("fraud_count", 0)),
        },
    }


@app.get("/api/merchant/{merchant_name}/rhythm")
def get_merchant_rhythm(
    merchant_name: str,
    days: int = Query(60, ge=7, le=365),
):
    """Merchant behavioral rhythm — recent daily pattern."""
    # Combine train + test for full history
    train_df = get_anomalies()
    test_df = get_test_anomalies()

    combined = pd.concat([train_df, test_df], ignore_index=True)

    # Case-insensitive merchant lookup
    merchant_lower = merchant_name.lower()
    all_merchants = combined["merchant"].unique()
    matched = [m for m in all_merchants if m.lower() == merchant_lower]

    if not matched:
        # Try partial match as fallback
        matched = [m for m in all_merchants if merchant_lower in m.lower()]

    if not matched:
        raise HTTPException(404, f"Merchant '{merchant_name}' not found")

    # Use the actual canonical name from data
    canonical_name = matched[0]
    merchant_data = combined[combined["merchant"] == canonical_name].copy()

    merchant_data = merchant_data.sort_values("date")

    # Take last N days
    if len(merchant_data) > days:
        merchant_data = merchant_data.tail(days)

    timeline = []
    for _, row in merchant_data.iterrows():
        entry = {
            "date": row["date"],
            "transaction_count": int(row["transaction_count"]),
            "total_amount": round(float(row["total_amount"]), 2),
            "risk_level": row.get("risk_level", "not_scored"),
            "anomaly_type": row.get("anomaly_type", "not_scored"),
        }

        if row.get("baseline_status") == "sufficient_history":
            entry["expected_tx_count"] = round(float(row["expected_tx_count"]), 1)
            entry["expected_total_amount"] = round(float(row["expected_total_amount"]), 2)
            entry["velocity_deviation"] = round(float(row.get("velocity_deviation", 0)), 2)
            entry["amount_deviation"] = round(float(row.get("amount_deviation", 0)), 2)

        timeline.append(entry)

    # Summary
    suf = merchant_data[merchant_data["baseline_status"] == "sufficient_history"]
    anomaly_days = suf[suf["anomaly_type"] != "normal"] if "anomaly_type" in suf.columns else pd.DataFrame()

    return {
        "merchant": canonical_name,
        "total_days": len(merchant_data),
        "anomaly_days": len(anomaly_days),
        "avg_daily_tx": round(float(merchant_data["transaction_count"].mean()), 1),
        "avg_daily_amount": round(float(merchant_data["total_amount"].mean()), 2),
        "timeline": timeline,
    }


@app.get("/api/merchants/suggest")
def suggest_merchants(
    q: str = Query("", description="Search query for merchant name"),
    limit: int = Query(8, ge=1, le=20),
):
    """Lightweight merchant name suggestions for autocomplete."""
    df = get_anomalies()
    all_merchants = sorted(df["merchant"].unique())

    if not q.strip():
        return {"suggestions": all_merchants[:limit]}

    query_lower = q.strip().lower()
    # Exact prefix matches first, then contains matches
    prefix = [m for m in all_merchants if m.lower().startswith(query_lower)]
    contains = [m for m in all_merchants if query_lower in m.lower() and m not in prefix]
    results = (prefix + contains)[:limit]

    return {"suggestions": results}


@app.get("/api/merchants")
def list_merchants(
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    """List all merchants with summary stats."""
    df = get_anomalies()
    sufficient = df[df["baseline_status"] == "sufficient_history"]

    merchants = sufficient.groupby("merchant").agg(
        total_days=("date", "count"),
        avg_tx=("transaction_count", "mean"),
        avg_amount=("total_amount", "mean"),
        anomaly_count=("anomaly_type", lambda x: (x != "normal").sum()),
        high_count=("risk_level", lambda x: (x == "high").sum()),
    ).reset_index()

    if search:
        merchants = merchants[merchants["merchant"].str.contains(search, case=False, na=False)]

    merchants = merchants.sort_values("anomaly_count", ascending=False).head(limit)

    return {
        "total": len(merchants),
        "merchants": [
            {
                "name": row["merchant"],
                "total_days": int(row["total_days"]),
                "avg_daily_tx": round(float(row["avg_tx"]), 1),
                "avg_daily_amount": round(float(row["avg_amount"]), 2),
                "anomaly_days": int(row["anomaly_count"]),
                "high_risk_days": int(row["high_count"]),
            }
            for _, row in merchants.iterrows()
        ],
    }


@app.get("/api/evaluation")
def get_evaluation():
    """Honest Phase 5 evaluation results — no vanity metrics."""
    report = get_eval_report()
    policy = get_detection_policy()
    pc = report["proxy_classification"]
    pr = report["primary_results"]

    # Alert efficiency — derived from locked evaluation data
    total_eligible = report["dataset_coverage"]["eligible_merchant_days"]
    total_alerts = pr["alert_volume"]["total_flagged"]
    proxy_positives = pr["overall_fraud_prevalence"]["fraud_containing_days"]
    alerts_per_proxy_positive = round(total_alerts / max(pc["tp"], 1), 2)

    return {
        "methodology": {
            "description": "Behavioral anomaly detection evaluated on held-out test data",
            "detection_unit": "merchant-day",
            "proxy_ground_truth": "Merchant-day containing at least one fraud-tagged transaction",
            "frozen_policy": True,
            "test_data_used_for_tuning": False,
            "baseline_method": "30-day rolling median + MAD per merchant",
            "core_signals": ["Transaction velocity deviation", "Total amount deviation"],
            "composite_method": policy.get("composite_method", "max(velocity, amount)"),
            "thresholds": {
                "elevated": policy.get("elevated_threshold", 4.0),
                "high": policy.get("high_threshold", 5.0),
            },
        },
        "dataset": report["evaluation_setup"],
        "coverage": report["dataset_coverage"],
        "primary_results": pr,
        "confusion_matrix": {
            "tp": pc["tp"],
            "fp": pc["fp"],
            "fn": pc["fn"],
            "tn": pc["tn"],
            "unit": "merchant-day",
            "positive_definition": "Merchant-day with fraud_count > 0",
        },
        "proxy_metrics": {
            "proxy_precision_pct": pc["proxy_precision_pct"],
            "proxy_recall_pct": pc["proxy_recall_pct"],
            "proxy_f1_pct": pc["proxy_f1_pct"],
            "methodology_note": (
                "These metrics use fraud-containing merchant-days as proxy ground truth. "
                "Payment Burst Sentinel detects behavioral deviations, not individual "
                "fraudulent transactions."
            ),
        },
        "alert_efficiency": {
            "total_eligible_merchant_days": total_eligible,
            "total_alerts": total_alerts,
            "alert_rate_pct": pr["alert_volume"]["pct_flagged"],
            "proxy_fraud_days_captured": pc["tp"],
            "total_proxy_fraud_days": proxy_positives,
            "proxy_capture_rate_pct": pc["proxy_recall_pct"],
            "alerts_per_proxy_positive": alerts_per_proxy_positive,
        },
        "signal_analysis": {
            "amount_dominance_pct": report["amount_dominance"]["amount_only_pct_of_flags"],
            "velocity_only_pct": report["amount_dominance"]["velocity_only_pct_of_flags"],
            "combined_pct": report["amount_dominance"]["combined_pct_of_flags"],
        },
        "baseline_comparison": report["baseline_comparison"],
        "verdict": report["verdict"],
        "limitations": [
            "Behavioral anomaly ≠ fraud — the system detects behavioral deviation, not fraud",
            "Merchant-day is the detection unit; proxy ground truth is fraud-containing merchant-day",
            "Daily resolution only — sub-daily patterns not detected",
            "Evaluated on synthetic dataset derived from IEEE-CIS data",
            "Velocity alone provides weak fraud enrichment (0.65×)",
            "49% of fraud-containing days are behaviorally normal and undetectable by this method",
            "Thresholds were frozen before test evaluation — no test-set tuning occurred",
        ],
    }


@app.get("/api/evaluation/cost-model")
def get_cost_model(
    review_minutes: int = Query(15, ge=1, le=120, description="Minutes per alert review"),
    analyst_hourly_cost: int = Query(500, ge=100, le=5000, description="Analyst cost per hour (INR)"),
    policy: str = Query("all_flagged", description="Policy: all_flagged or high_only"),
):
    """
    Scenario-based investigation workload model.

    Source: locked evaluation outputs (evaluation_report.json).
    All calculations are derived read-only — no analytical files are modified.
    Assumptions are scenario-based, NOT measured Razorpay operational costs.
    """
    report = get_eval_report()
    pr = report["primary_results"]
    pc = report["proxy_classification"]

    if policy not in ("all_flagged", "high_only"):
        raise HTTPException(400, f"Invalid policy: '{policy}'. Use 'all_flagged' or 'high_only'.")

    # ── Compute per-policy metrics from locked data ──────────────
    def compute_policy_metrics(alerts: int, proxy_tp: int, review_min: int, hourly_cost: int):
        estimated_fp = alerts - proxy_tp
        review_hours = round((estimated_fp * review_min) / 60, 2)
        review_cost = round(review_hours * hourly_cost, 2)
        alerts_per_pp = round(alerts / max(proxy_tp, 1), 2)
        proxy_precision = round((proxy_tp / max(alerts, 1)) * 100, 2)
        return {
            "total_alerts": alerts,
            "proxy_true_positives": proxy_tp,
            "estimated_false_positive_alerts": estimated_fp,
            "proxy_precision_pct": proxy_precision,
            "estimated_review_hours": review_hours,
            "scenario_based_review_cost": review_cost,
            "alerts_per_proxy_positive": alerts_per_pp,
        }

    # All flagged: elevated + high (≥4 MAD)
    all_flagged_alerts = pr["alert_volume"]["total_flagged"]
    all_flagged_tp = pc["tp"]

    # High only (≥5 MAD)
    high_alerts = pr["risk_levels"]["high"]["count"]
    high_tp = pr["risk_levels"]["high"]["fraud_days"]

    # Total proxy positives for recall calculation
    total_proxy_positives = pr["overall_fraud_prevalence"]["fraud_containing_days"]

    # Selected policy results
    if policy == "high_only":
        selected = compute_policy_metrics(high_alerts, high_tp, review_minutes, analyst_hourly_cost)
        selected["proxy_recall_pct"] = round((high_tp / max(total_proxy_positives, 1)) * 100, 2)
    else:
        selected = compute_policy_metrics(all_flagged_alerts, all_flagged_tp, review_minutes, analyst_hourly_cost)
        selected["proxy_recall_pct"] = round((all_flagged_tp / max(total_proxy_positives, 1)) * 100, 2)

    # ── Scenario presets ─────────────────────────────────────────
    scenarios = []
    presets = [
        {"name": "Lean", "review_minutes": 5, "analyst_hourly_cost": 300},
        {"name": "Standard", "review_minutes": 15, "analyst_hourly_cost": 500},
        {"name": "Intensive", "review_minutes": 30, "analyst_hourly_cost": 800},
    ]
    for preset in presets:
        if policy == "high_only":
            metrics = compute_policy_metrics(high_alerts, high_tp, preset["review_minutes"], preset["analyst_hourly_cost"])
        else:
            metrics = compute_policy_metrics(all_flagged_alerts, all_flagged_tp, preset["review_minutes"], preset["analyst_hourly_cost"])
        scenarios.append({**preset, **metrics})

    # ── Policy comparison ────────────────────────────────────────
    policy_comparison = {
        "all_flagged": {
            "label": "Elevated + High (≥4 MAD)",
            "enrichment_vs_normal": pr["flagged_vs_normal"]["enrichment_vs_normal"],
            **compute_policy_metrics(all_flagged_alerts, all_flagged_tp, review_minutes, analyst_hourly_cost),
            "proxy_recall_pct": round((all_flagged_tp / max(total_proxy_positives, 1)) * 100, 2),
        },
        "high_only": {
            "label": "High only (≥5 MAD)",
            "enrichment_vs_normal": pr["risk_levels"]["high"]["enrichment"],
            **compute_policy_metrics(high_alerts, high_tp, review_minutes, analyst_hourly_cost),
            "proxy_recall_pct": round((high_tp / max(total_proxy_positives, 1)) * 100, 2),
        },
    }

    return {
        "assumptions": {
            "review_minutes": review_minutes,
            "analyst_hourly_cost": analyst_hourly_cost,
            "currency": "INR",
            "policy": policy,
            "source": "Derived read-only from locked evaluation_report.json",
            "disclaimer": (
                "These figures model analyst review workload using illustrative "
                "assumptions. They are not Razorpay operational cost data."
            ),
        },
        "results": selected,
        "scenarios": scenarios,
        "policy_comparison": policy_comparison,
    }


# ═══════════════════════════════════════════════════════════════
# AI INVESTIGATION INTELLIGENCE — Phase 15
# Additive endpoint. No existing routes modified.
# ═══════════════════════════════════════════════════════════════

@app.post("/api/investigation/{merchant}/{date}/ai-brief")
async def generate_ai_brief(merchant: str, date: str):
    """
    Generate an AI investigation brief for a specific merchant-day event.

    POST because this triggers an external AI service call and populates cache.
    The AI explains deterministic evidence — it does not detect anomalies.
    """
    # Step 1: Resolve the investigation event using existing logic
    try:
        investigation_detail = get_investigation_detail(merchant, date)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(404, f"No event found for {merchant} on {date}")

    # Step 2: Delegate to AI service layer
    try:
        from backend.ai.service import generate_investigation_brief
        response = await generate_investigation_brief(investigation_detail)
        return response.model_dump()
    except Exception as e:
        # AI failure must never break the application
        return {
            "status": "unavailable",
            "cached": False,
            "reason": "AI service encountered an unexpected error. The deterministic investigation evidence remains available.",
            "brief": None,
        }


# ═══════════════════════════════════════════════════════════════
# INTEGRATION READINESS — Phase 16
# Additive endpoints only. No existing routes modified.
# This does NOT connect to Razorpay. This does NOT modify
# analytical data, trigger detection, or call Gemini.
# ═══════════════════════════════════════════════════════════════

@app.get("/api/integration/status")
def get_integration_status_endpoint():
    """
    Return honest integration readiness status.

    adapter_ready ≠ connected.
    This endpoint reports architecture readiness, not live connectivity.
    """
    try:
        from backend.integrations.service import get_integration_status
        status = get_integration_status()
        return status.model_dump()
    except Exception:
        # Integration status failure must never break the application
        return {
            "current_data_mode": "dataset",
            "integration_readiness": {
                "provider_abstraction": True,
                "canonical_normalization": True,
                "payload_validation": True,
                "idempotency_boundary": True,
            },
            "providers": {},
        }


@app.post("/api/integration/demo/ingest")
async def demo_ingest_endpoint(payload: Optional[dict] = None):
    """
    Demo integration endpoint — demonstrates the integration pipeline.

    Accepts a demo payload or auto-generates a synthetic one.
    Returns the canonical normalized event with pipeline status.

    This endpoint:
    - ONLY accepts source='demo'
    - Does NOT write to data/processed/
    - Does NOT trigger anomaly detection
    - Does NOT modify baselines or evaluation
    - Does NOT call Gemini

    All output is labeled: SIMULATED PROVIDER PAYLOAD
    """
    try:
        from backend.integrations.service import process_demo_ingestion

        result = process_demo_ingestion(payload=payload)

        # Serialize with Decimal/datetime handling
        result_dict = result.model_dump()

        # Convert Decimal to string for JSON
        if result_dict.get("canonical_event"):
            ce = result_dict["canonical_event"]
            if ce.get("amount") is not None:
                ce["amount"] = str(ce["amount"])

        return result_dict
    except Exception as e:
        return {
            "status": "rejected",
            "validation_errors": [f"Integration service error: {str(e)}"],
            "pipeline_status": {
                "payload_validated": False,
                "canonical_event_created": False,
                "historical_aggregation": "future_phase",
                "detection_execution": "not_triggered",
                "ai_analysis": "not_triggered",
            },
        }

