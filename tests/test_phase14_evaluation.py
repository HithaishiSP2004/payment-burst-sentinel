"""
Phase 14 — Evaluation & Cost Model Tests
==========================================
Tests for proxy metrics integrity, cost model calculations,
and API endpoint validation. All data comes from locked
evaluation_report.json — no analytical files are modified.
"""
import json
import math
from pathlib import Path
import pytest

# ── Load locked evaluation data ─────────────────────────────
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
EVAL_REPORT_PATH = DATA_DIR / "evaluation" / "evaluation_report.json"


@pytest.fixture
def eval_report():
    with open(EVAL_REPORT_PATH) as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════
# 1. METRIC INTEGRITY — Confusion Matrix Consistency
# ═══════════════════════════════════════════════════════════

class TestMetricIntegrity:
    """Verify confusion matrix is internally consistent."""

    def test_tp_plus_fp_equals_flagged(self, eval_report):
        pc = eval_report["proxy_classification"]
        flagged = eval_report["primary_results"]["alert_volume"]["total_flagged"]
        assert pc["tp"] + pc["fp"] == flagged, (
            f"TP ({pc['tp']}) + FP ({pc['fp']}) must equal total flagged ({flagged})"
        )

    def test_tp_plus_fn_equals_proxy_positives(self, eval_report):
        pc = eval_report["proxy_classification"]
        fraud_days = eval_report["primary_results"]["overall_fraud_prevalence"]["fraud_containing_days"]
        assert pc["tp"] + pc["fn"] == fraud_days, (
            f"TP ({pc['tp']}) + FN ({pc['fn']}) must equal fraud-containing days ({fraud_days})"
        )

    def test_tn_plus_fp_equals_proxy_negatives(self, eval_report):
        pc = eval_report["proxy_classification"]
        total = eval_report["dataset_coverage"]["eligible_merchant_days"]
        fraud_days = eval_report["primary_results"]["overall_fraud_prevalence"]["fraud_containing_days"]
        proxy_negatives = total - fraud_days
        assert pc["tn"] + pc["fp"] == proxy_negatives, (
            f"TN ({pc['tn']}) + FP ({pc['fp']}) must equal proxy negatives ({proxy_negatives})"
        )

    def test_total_observations(self, eval_report):
        pc = eval_report["proxy_classification"]
        total = eval_report["dataset_coverage"]["eligible_merchant_days"]
        computed = pc["tp"] + pc["fp"] + pc["fn"] + pc["tn"]
        assert computed == total, (
            f"TP+FP+FN+TN ({computed}) must equal total observations ({total})"
        )

    def test_precision_calculation(self, eval_report):
        pc = eval_report["proxy_classification"]
        expected = round((pc["tp"] / (pc["tp"] + pc["fp"])) * 100, 2)
        assert pc["proxy_precision_pct"] == expected

    def test_recall_calculation(self, eval_report):
        pc = eval_report["proxy_classification"]
        expected = round((pc["tp"] / (pc["tp"] + pc["fn"])) * 100, 2)
        assert pc["proxy_recall_pct"] == expected

    def test_f1_calculation(self, eval_report):
        pc = eval_report["proxy_classification"]
        p = pc["proxy_precision_pct"] / 100
        r = pc["proxy_recall_pct"] / 100
        expected_f1 = round(2 * p * r / (p + r) * 100, 2)
        assert pc["proxy_f1_pct"] == expected_f1


# ═══════════════════════════════════════════════════════════
# 2. COST MODEL — Calculation Correctness
# ═══════════════════════════════════════════════════════════

class TestCostModel:
    """Test cost model calculation logic."""

    def _compute(self, alerts, proxy_tp, review_min, hourly_cost):
        """Replicate the cost model formula."""
        fp = alerts - proxy_tp
        hours = round((fp * review_min) / 60, 2)
        cost = round(hours * hourly_cost, 2)
        return fp, hours, cost

    def test_standard_scenario(self, eval_report):
        pc = eval_report["proxy_classification"]
        alerts = eval_report["primary_results"]["alert_volume"]["total_flagged"]
        fp, hours, cost = self._compute(alerts, pc["tp"], 15, 500)
        assert fp == 15021
        assert hours == 3755.25
        assert cost == 1877625.0

    def test_lean_scenario(self, eval_report):
        pc = eval_report["proxy_classification"]
        alerts = eval_report["primary_results"]["alert_volume"]["total_flagged"]
        fp, hours, cost = self._compute(alerts, pc["tp"], 5, 300)
        assert fp == 15021
        assert hours == round((15021 * 5) / 60, 2)
        assert cost == round(hours * 300, 2)

    def test_zero_false_positives(self):
        """Edge case: all alerts are true positives."""
        fp, hours, cost = 0, 0.0, 0.0
        computed_fp = 100 - 100  # alerts == proxy_tp
        computed_hours = round((computed_fp * 15) / 60, 2)
        computed_cost = round(computed_hours * 500, 2)
        assert computed_fp == fp
        assert computed_hours == hours
        assert computed_cost == cost

    def test_zero_alerts(self):
        """Edge case: no alerts generated."""
        fp = 0 - 0
        hours = round((fp * 15) / 60, 2)
        cost = round(hours * 500, 2)
        assert fp == 0
        assert hours == 0.0
        assert cost == 0.0

    def test_high_only_policy(self, eval_report):
        """High-only policy should have fewer alerts."""
        pr = eval_report["primary_results"]
        all_alerts = pr["alert_volume"]["total_flagged"]
        high_alerts = pr["risk_levels"]["high"]["count"]
        assert high_alerts < all_alerts, "High-only must have fewer alerts than all_flagged"


# ═══════════════════════════════════════════════════════════
# 3. DATA INTEGRITY — Locked Files Unchanged
# ═══════════════════════════════════════════════════════════

class TestDataIntegrity:
    """Verify locked evaluation data has expected values."""

    def test_merchants_monitored(self, eval_report):
        assert eval_report["dataset_coverage"]["merchants_covered"] == 693

    def test_total_flagged(self, eval_report):
        assert eval_report["primary_results"]["alert_volume"]["total_flagged"] == 16090

    def test_enrichment_vs_normal(self, eval_report):
        assert eval_report["primary_results"]["flagged_vs_normal"]["enrichment_vs_normal"] == 7.13

    def test_enrichment_vs_overall(self, eval_report):
        assert eval_report["primary_results"]["flagged_vs_normal"]["enrichment_vs_overall"] == 4.01

    def test_elevated_count(self, eval_report):
        assert eval_report["primary_results"]["risk_levels"]["elevated"]["count"] == 4977

    def test_high_count(self, eval_report):
        assert eval_report["primary_results"]["risk_levels"]["high"]["count"] == 11113

    def test_thresholds_unchanged(self, eval_report):
        setup = eval_report["evaluation_setup"]
        assert setup["frozen_elevated_threshold"] == 4.0
        assert setup["frozen_high_threshold"] == 5.0

    def test_parquet_files_exist(self):
        """Verify locked analytical outputs exist."""
        assert (DATA_DIR / "anomalies" / "merchant_daily_anomalies.parquet").exists()
        assert (DATA_DIR / "anomalies" / "flagged_events.parquet").exists()
        assert (DATA_DIR / "evaluation" / "test_anomalies.parquet").exists()
        assert (DATA_DIR / "evaluation" / "evaluation_report.json").exists()
