"""
Payment Burst Sentinel — AI Provider & Guardrail Tests (Phase 15/FW1.1)
========================================================================
Deterministic unit tests for Gemini provider configuration, model fallback,
fallback provider behavior, and post-generation safety guardrails.
"""

import os
import pytest
from unittest.mock import patch

from backend.ai.schemas import (
    InvestigationEvidence,
    EvidenceItem,
    EvidenceSignal,
    BaselineInfo,
    InvestigationBrief,
    EvidenceClaim,
    KeyEvidenceExplanation,
    AIBriefResponse,
)
from backend.ai.fallback_provider import FallbackProvider
from backend.ai.guardrails import validate_brief
from backend.ai.gemini_provider import GeminiProvider, DEFAULT_MODELS


@pytest.fixture
def sample_evidence():
    return InvestigationEvidence(
        event_id="Kovacek Ltd_2020-11-27",
        merchant="Kovacek Ltd",
        date="2020-11-27",
        risk_level="high",
        anomaly_type="amount_anomaly",
        composite_deviation=1935.42,
        primary_evidence=EvidenceSignal(
            signal="Payment Value Deviation",
            role="PRIMARY",
            observed=19364.91,
            expected=10.75,
            variability=10.0,
            deviation_mads=1935.42,
        ),
        behavioral_context=EvidenceSignal(
            signal="Transaction Volume Shift",
            role="CONTEXT",
            observed=1,
            expected=2.0,
            variability=1.0,
            deviation_mads=0.0,
        ),
        baseline_info=BaselineInfo(
            historical_days_used=25,
            baseline_window_days=30,
            baseline_status="sufficient_history",
            day_of_week=4,
        ),
        evidence_items=[
            EvidenceItem(
                evidence_id="E1",
                category="amount_deviation",
                label="Payment Value Deviation",
                observed_value="₹19,364.91",
                baseline_value="~₹10.75",
                deviation="+1935.42 MADs",
                context="Primary signal",
            ),
            EvidenceItem(
                evidence_id="E2",
                category="velocity_deviation",
                label="Transaction Volume",
                observed_value="1 tx",
                baseline_value="~2 tx",
                deviation="+0.00 MADs",
                context="Contextual signal",
            ),
        ],
        evidence_statements=["Payment value was significantly above expected."],
        limitations=["Anomaly is not fraud."],
    )


@pytest.fixture
def sample_valid_brief():
    return InvestigationBrief(
        headline="Significant Payment Value Deviation for Kovacek Ltd",
        summary="A major statistical spike in daily payment value was observed while transaction volume remained typical.",
        what_changed=[
            EvidenceClaim(
                statement="Payment value reached ₹19,364.91 compared to baseline expected of ~₹10.75.",
                evidence_ids=["E1"],
            )
        ],
        key_evidence=[
            KeyEvidenceExplanation(
                evidence_id="E1",
                observation="Daily amount exceeded median baseline by 1935.42 MADs.",
                why_it_matters="Indicates an extreme single-day transaction value shift.",
            )
        ],
        investigate_next=[
            "Verify whether single high-value order or bulk payment caused the shift.",
            "Check merchant category and historical seasonality.",
        ],
        what_remains_unknown=[
            "Underlying commercial justification for the high-value transaction.",
            "Customer authorization and settlement status.",
        ],
        safety_note="This brief explains deterministic evidence and does not confirm fraud. Human review required.",
    )


class TestGeminiProviderConfig:
    """Verify provider initialization, model selection, and fallback lists."""

    def test_requires_api_key(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable is not set"):
                GeminiProvider()

    def test_default_model_cascade(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key"}, clear=True):
            with patch("google.genai.Client"):
                provider = GeminiProvider()
                assert provider.model_name == "gemini-3.8-flash"
                assert provider.models == DEFAULT_MODELS
                assert "gemini-3.7-flash" in provider.models
                assert "gemini-3.5-flash" in provider.models
                assert "gemini-3.5-flash-lite" in provider.models

    def test_comma_separated_models_override(self):
        custom_models = "gemini-3.5-flash-lite,gemini-2.5-flash"
        with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_key", "GEMINI_MODEL": custom_models}, clear=True):
            with patch("google.genai.Client"):
                provider = GeminiProvider()
                assert provider.model_name == "gemini-3.5-flash-lite"
                assert provider.models == ["gemini-3.5-flash-lite", "gemini-2.5-flash"]


class TestFallbackProvider:
    """Verify FallbackProvider behavior when AI is offline or unconfigured."""

    def test_fallback_returns_unavailable(self, sample_evidence):
        import asyncio
        provider = FallbackProvider("Custom unconfigured message.")
        response = asyncio.run(provider.generate_brief(sample_evidence))
        assert response.status == "unavailable"
        assert response.brief is None
        assert response.reason == "Custom unconfigured message."


class TestGuardrails:
    """Verify 7 deterministic safety guardrails."""

    def test_valid_brief_passes(self, sample_valid_brief):
        valid_ids = {"E1", "E2"}
        error = validate_brief(sample_valid_brief, valid_ids)
        assert error is None

    def test_invalid_evidence_id_rejected(self, sample_valid_brief):
        valid_ids = {"E2"}  # E1 missing
        error = validate_brief(sample_valid_brief, valid_ids)
        assert error is not None
        assert "Invalid evidence reference 'E1'" in error

    def test_prohibited_fraud_certainty_rejected(self, sample_valid_brief):
        sample_valid_brief.headline = "Confirmed fraud detected at merchant"
        error = validate_brief(sample_valid_brief, {"E1", "E2"})
        assert error is not None
        assert "Prohibited fraud-certainty phrase" in error

    def test_prohibited_autonomous_action_rejected(self, sample_valid_brief):
        sample_valid_brief.summary = "Risk engine should block payment immediately"
        error = validate_brief(sample_valid_brief, {"E1", "E2"})
        assert error is not None
        assert "Prohibited autonomous action" in error

    def test_empty_unknowns_rejected(self, sample_valid_brief):
        sample_valid_brief.what_remains_unknown = []
        error = validate_brief(sample_valid_brief, {"E1", "E2"})
        assert error is not None
        assert "what_remains_unknown must not be empty" in error
