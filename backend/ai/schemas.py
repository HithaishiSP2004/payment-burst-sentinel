"""
Payment Burst Sentinel — AI Schemas
====================================
Pydantic models for the AI Investigation Intelligence layer.
Defines the evidence contract, structured AI output, and API response.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
# EVIDENCE CONTRACT — Input to Gemini
# ═══════════════════════════════════════════════════════════

class EvidenceItem(BaseModel):
    """A single piece of deterministic evidence with a stable ID."""
    evidence_id: str = Field(..., description="Stable ID like E1, E2, E3")
    category: str = Field(..., description="amount | velocity | baseline | anomaly_type")
    label: str = Field(..., description="Human-readable label")
    observed_value: str = Field(..., description="Observed value as string")
    baseline_value: Optional[str] = Field(None, description="Expected baseline value")
    deviation: Optional[str] = Field(None, description="Deviation in MADs")
    context: Optional[str] = Field(None, description="Additional context")


class EvidenceSignal(BaseModel):
    """Structured signal from the detection system."""
    signal: str
    role: str
    observed: float
    expected: float
    variability: float
    deviation_mads: float


class BaselineInfo(BaseModel):
    """Baseline computation metadata."""
    historical_days_used: int
    baseline_window_days: int
    baseline_status: str
    day_of_week: int


class InvestigationEvidence(BaseModel):
    """Complete evidence contract sent to Gemini. Read-only from detection."""
    event_id: str = Field(..., description="merchant::date identifier")
    merchant: str
    date: str
    risk_level: str
    anomaly_type: str
    composite_deviation: float

    primary_evidence: EvidenceSignal
    behavioral_context: EvidenceSignal
    baseline_info: BaselineInfo
    evidence_statements: list[str]

    evidence_items: list[EvidenceItem] = Field(
        ..., description="Structured evidence with stable IDs for AI referencing"
    )

    thresholds: dict = Field(
        default_factory=lambda: {"elevated_mad": 4.0, "high_mad": 5.0}
    )

    limitations: list[str] = Field(
        default_factory=lambda: [
            "Behavioral anomaly does not establish fraud.",
            "The system detects merchant-day deviations, not individual fraudulent transactions.",
            "The available evidence should be reviewed by a human investigator.",
        ]
    )


# ═══════════════════════════════════════════════════════════
# AI OUTPUT — Structured response from Gemini
# ═══════════════════════════════════════════════════════════

class EvidenceClaim(BaseModel):
    """A claim about what changed, with mandatory evidence references."""
    statement: str = Field(..., description="Concise observation")
    evidence_ids: list[str] = Field(
        ..., min_length=1,
        description="References to evidence IDs (e.g. ['E1', 'E2'])"
    )


class KeyEvidenceExplanation(BaseModel):
    """AI explanation of a specific evidence item."""
    evidence_id: str = Field(..., description="Reference to a deterministic evidence ID")
    observation: str = Field(..., description="What was observed")
    why_it_matters: str = Field(..., description="Why this is significant for investigation")


class InvestigationBrief(BaseModel):
    """
    Structured AI investigation brief — used as Gemini response_schema.
    Every evidence-based claim must reference deterministic evidence IDs.
    """
    headline: str = Field(
        ..., description="One-sentence evidence-grounded finding (max ~100 chars)"
    )
    summary: str = Field(
        ..., description="2-4 concise sentences summarizing the behavioral deviation"
    )
    what_changed: list[EvidenceClaim] = Field(
        ..., description="Structured observations with evidence references"
    )
    key_evidence: list[KeyEvidenceExplanation] = Field(
        ..., description="Explanation of the most important evidence items"
    )
    investigate_next: list[str] = Field(
        ..., description="Defensive investigation questions for human analysts"
    )
    what_remains_unknown: list[str] = Field(
        ..., min_length=1,
        description="What cannot be concluded from the available evidence"
    )
    safety_note: str = Field(
        ...,
        description="Mandatory disclaimer about deterministic evidence boundaries"
    )


# ═══════════════════════════════════════════════════════════
# API RESPONSE — Returned to frontend
# ═══════════════════════════════════════════════════════════

class AIBriefResponse(BaseModel):
    """API response for the AI investigation brief endpoint."""
    status: str = Field(..., description="available | unavailable | error")
    cached: bool = False
    generated_at: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    reason: Optional[str] = None
    brief: Optional[InvestigationBrief] = None

    @classmethod
    def available(cls, brief: InvestigationBrief, provider: str, model: str,
                  cached: bool = False) -> AIBriefResponse:
        return cls(
            status="available",
            cached=cached,
            generated_at=datetime.utcnow().isoformat() + "Z",
            provider=provider,
            model=model,
            brief=brief,
        )

    @classmethod
    def unavailable(cls, reason: str) -> AIBriefResponse:
        return cls(
            status="unavailable",
            reason=reason,
        )
