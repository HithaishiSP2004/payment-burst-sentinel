"""
Payment Burst Sentinel — Integration Service (Phase 16)
=========================================================
Orchestration layer for the integration boundary.

Flow:
1. Payload size check
2. Minimal source + source_event_id extraction
3. Duplicate lookup
4. Full validation
5. Provider normalization
6. Canonical event creation
7. Record idempotency (ONLY after success)
8. Return IngestionResult

CRITICAL BOUNDARIES — this service NEVER:
- writes to data/processed/
- modifies parquet files
- calls anomaly detection
- updates baselines
- modifies evaluation
- calls Gemini
- triggers Phase 15 AI automatically
"""

from __future__ import annotations

import os
from typing import Any

from backend.integrations.schemas import (
    CanonicalPaymentEvent,
    IngestionResult,
    IngestionStatus,
    IntegrationStatusResponse,
    IntegrationReadiness,
    ProviderStatus,
    PipelineStatus,
    PaymentSource,
)
from backend.integrations.validator import (
    validate_payload,
    validate_payload_size,
    extract_identity,
)
from backend.integrations.demo_provider import DemoProvider
from backend.integrations.razorpay_adapter import RazorpayAdapter
from backend.integrations.idempotency import IdempotencyStore


# ── Singleton instances ────────────────────────────────────────

_demo_provider = DemoProvider()
_razorpay_adapter = RazorpayAdapter()
_idempotency_store = IdempotencyStore()


def get_demo_provider() -> DemoProvider:
    return _demo_provider


def get_razorpay_adapter() -> RazorpayAdapter:
    return _razorpay_adapter


def get_idempotency_store() -> IdempotencyStore:
    return _idempotency_store


# ── Integration Status ────────────────────────────────────────

def get_integration_status() -> IntegrationStatusResponse:
    """
    Return honest integration readiness status.

    adapter_ready ≠ connected.
    """
    rzp = _razorpay_adapter
    mode = os.environ.get("INTEGRATION_MODE", "dataset")

    return IntegrationStatusResponse(
        current_data_mode=mode,
        integration_readiness=IntegrationReadiness(
            provider_abstraction=True,
            canonical_normalization=True,
            payload_validation=True,
            idempotency_boundary=True,
        ),
        providers={
            "demo": ProviderStatus(available=True),
            "razorpay": ProviderStatus(
                adapter_ready=True,
                configured=rzp.is_configured,
                connected=False,  # Phase 16: NEVER connected
            ),
        },
    )


# ── Ingestion Orchestration ───────────────────────────────────

def process_demo_ingestion(
    payload: dict[str, Any] | None = None,
    raw_body: str | bytes | None = None,
) -> IngestionResult:
    """
    Process a demo integration payload.

    If no payload is provided, generates a synthetic demo event.

    Flow:
    1. Payload size validation
    2. Identity extraction
    3. Duplicate check
    4. Full validation
    5. Normalization
    6. Idempotency recording (only on success)
    7. Return result with pipeline status
    """
    pipeline = PipelineStatus()

    # Auto-generate if no payload provided
    if payload is None:
        payload = _demo_provider.generate_demo_payload()

    # Force source to demo
    payload["source"] = "demo"

    # Step 1: Payload size validation
    if raw_body is not None:
        size_errors = validate_payload_size(raw_body)
        if size_errors:
            return IngestionResult(
                status=IngestionStatus.REJECTED,
                validation_errors=size_errors,
                pipeline_status=pipeline,
            )

    # Step 2: Extract identity for idempotency
    source, source_event_id = extract_identity(payload)

    # Step 3: Duplicate check (only if identity is extractable)
    if source and source_event_id:
        existing_id = _idempotency_store.check_duplicate(source, source_event_id)
        if existing_id is not None:
            pipeline.payload_validated = True
            return IngestionResult(
                event_id=existing_id,
                status=IngestionStatus.DUPLICATE,
                duplicate_of=existing_id,
                pipeline_status=pipeline,
            )

    # Step 4: Full validation
    errors = _demo_provider.validate(payload)
    if errors:
        return IngestionResult(
            status=IngestionStatus.REJECTED,
            validation_errors=errors,
            pipeline_status=pipeline,
        )

    pipeline.payload_validated = True

    # Step 5: Normalization
    try:
        canonical = _demo_provider.normalize(payload)
    except Exception as e:
        return IngestionResult(
            status=IngestionStatus.REJECTED,
            validation_errors=[f"Normalization failed: {str(e)}"],
            pipeline_status=pipeline,
        )

    pipeline.canonical_event_created = True

    # Step 6: Record idempotency (ONLY after successful normalization)
    _idempotency_store.record(
        canonical.source.value,
        canonical.source_event_id,
        canonical.event_id,
    )

    # Step 7: Return result
    # Pipeline explicitly stops here — future phases handle aggregation/detection
    return IngestionResult(
        event_id=canonical.event_id,
        status=IngestionStatus.ACCEPTED,
        canonical_event=canonical,
        pipeline_status=pipeline,
    )
