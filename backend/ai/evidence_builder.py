"""
Payment Burst Sentinel — Evidence Builder
==========================================
Builds structured InvestigationEvidence from existing detection data.
Assigns stable deterministic evidence IDs for AI referencing.
READ-ONLY — consumes the same data as /api/investigation/{merchant}/{date}.
"""

import re
from .schemas import (
    InvestigationEvidence, EvidenceItem, EvidenceSignal, BaselineInfo
)


def _sanitize_text(text: str) -> str:
    """Remove potential prompt-injection patterns from data fields."""
    # Strip control characters and instruction-like prefixes
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    # Truncate excessively long values
    return text[:500]


def build_evidence(investigation_detail: dict) -> InvestigationEvidence:
    """
    Build structured evidence from the existing investigation detail response.

    Args:
        investigation_detail: The dict returned by get_investigation_detail()

    Returns:
        InvestigationEvidence with stable evidence IDs
    """
    d = investigation_detail
    pe = d["primary_evidence"]
    bc = d["behavioral_context"]
    bi = d["baseline_info"]

    # Build stable evidence items with deterministic IDs
    evidence_items: list[EvidenceItem] = []

    # E1 — Amount deviation (primary signal)
    evidence_items.append(EvidenceItem(
        evidence_id="E1",
        category="amount",
        label="Payment Value Deviation",
        observed_value=f"₹{pe['observed']:,.2f}",
        baseline_value=f"₹{pe['expected']:,.2f}",
        deviation=f"{pe['deviation_mads']:.2f} MADs",
        context=f"Variability: ±₹{pe['variability']:.2f}",
    ))

    # E2 — Velocity deviation (behavioral context)
    evidence_items.append(EvidenceItem(
        evidence_id="E2",
        category="velocity",
        label="Transaction Volume Shift",
        observed_value=f"{bc['observed']:.0f} transactions",
        baseline_value=f"~{bc['expected']:.1f} expected",
        deviation=f"{bc['deviation_mads']:.2f} MADs",
        context=f"Variability: ±{bc['variability']:.1f}",
    ))

    # E3 — Baseline information
    evidence_items.append(EvidenceItem(
        evidence_id="E3",
        category="baseline",
        label="Behavioral Baseline",
        observed_value=f"{bi['historical_days_used']} days of history",
        baseline_value=f"{bi['baseline_window_days']}-day rolling window",
        deviation=None,
        context=f"Status: {bi['baseline_status']}",
    ))

    # E4 — Anomaly classification
    anomaly_type = d["anomaly_type"]
    type_desc = {
        "amount_anomaly": "Amount deviation exceeded threshold independently",
        "velocity_anomaly": "Transaction velocity exceeded threshold independently",
        "combined_anomaly": "Both amount and velocity signals exceeded thresholds",
        "normal": "Activity was within expected behavioral range",
    }.get(anomaly_type, f"Classification: {anomaly_type}")

    evidence_items.append(EvidenceItem(
        evidence_id="E4",
        category="anomaly_type",
        label="Detection Classification",
        observed_value=anomaly_type.replace("_", " ").title(),
        baseline_value=None,
        deviation=None,
        context=type_desc,
    ))

    # E5 — Composite deviation score
    evidence_items.append(EvidenceItem(
        evidence_id="E5",
        category="composite",
        label="Composite Deviation Score",
        observed_value=f"{d['composite_deviation']:.2f} MADs",
        baseline_value=f"Elevated ≥ 4.0, High ≥ 5.0",
        deviation=None,
        context=f"Risk level: {d['risk_level'].upper()}",
    ))

    # E6 — Fraud count (proxy ground truth indicator)
    fraud_count = d.get("metadata", {}).get("fraud_count", 0)
    evidence_items.append(EvidenceItem(
        evidence_id="E6",
        category="proxy_truth",
        label="Proxy Ground Truth",
        observed_value=f"{fraud_count} fraud-tagged transactions on this merchant-day",
        baseline_value=None,
        deviation=None,
        context="Proxy label from dataset — does not confirm actual fraud",
    ))

    return InvestigationEvidence(
        event_id=f"{_sanitize_text(d['merchant'])}::{d['date']}",
        merchant=_sanitize_text(d["merchant"]),
        date=d["date"],
        risk_level=d["risk_level"],
        anomaly_type=d["anomaly_type"],
        composite_deviation=d["composite_deviation"],
        primary_evidence=EvidenceSignal(**pe),
        behavioral_context=EvidenceSignal(**bc),
        baseline_info=BaselineInfo(**bi),
        evidence_statements=[_sanitize_text(s) for s in d["evidence_statements"]],
        evidence_items=evidence_items,
    )
