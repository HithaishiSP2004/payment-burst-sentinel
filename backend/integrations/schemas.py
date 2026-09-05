"""
Payment Burst Sentinel — Integration Schemas (Phase 16)
========================================================
Provider-neutral canonical payment event model.

Schema version: 1.0
Breaking schema changes require a new major version.

Design principles:
- Decimal for all monetary values (never float)
- UTC-normalized timestamps (naive timestamps rejected)
- No is_fraud_tagged — fraud labels are evaluation-only metadata
- Idempotency uses source + source_event_id, NOT the canonical event_id
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Enums ──────────────────────────────────────────────────────

class PaymentSource(str, Enum):
    """Supported integration sources."""
    DEMO = "demo"
    RAZORPAY = "razorpay"


class IntegrationMode(str, Enum):
    """
    Supported operational modes in Phase 16.
    'live' is intentionally excluded — it belongs to a future production phase.
    """
    DATASET = "dataset"
    DEMO = "demo"
    SANDBOX = "sandbox"


class NormalizedStatus(str, Enum):
    """Provider-neutral payment lifecycle states."""
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class EventType(str, Enum):
    """Canonical event types."""
    PAYMENT = "payment"
    REFUND = "refund"
    DISPUTE = "dispute"


class IngestionStatus(str, Enum):
    """Result of ingestion processing."""
    ACCEPTED = "accepted"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"


# ── Canonical Payment Event ───────────────────────────────────

# Metadata safety limits
MAX_METADATA_KEYS = 20
MAX_METADATA_DEPTH = 2
MAX_METADATA_STRING_LENGTH = 500
MAX_METADATA_TOTAL_SIZE = 4096  # bytes (approximate)


def _validate_metadata_depth(obj: Any, current_depth: int = 0) -> bool:
    """Validate metadata nesting depth does not exceed limit."""
    if current_depth > MAX_METADATA_DEPTH:
        return False
    if isinstance(obj, dict):
        for v in obj.values():
            if not _validate_metadata_depth(v, current_depth + 1):
                return False
    elif isinstance(obj, list):
        for item in obj:
            if not _validate_metadata_depth(item, current_depth + 1):
                return False
    return True


# Secrets that must never appear in metadata
_FORBIDDEN_METADATA_KEYS = frozenset({
    "api_key", "apikey", "api_secret", "apisecret",
    "secret", "key_secret", "key_id",
    "token", "authorization", "auth_token",
    "password", "credential", "webhook_secret",
    "signature", "x-razorpay-signature",
})


class CanonicalPaymentEvent(BaseModel):
    """
    Provider-neutral canonical payment event.

    This is the normalized representation that all external provider
    payloads are mapped into. The existing historical dataset is NOT
    routed through this model — it remains a separate read-only pipeline.

    Idempotency key: source + source_event_id (NOT event_id).
    """

    # Internal canonical ID — NOT used for idempotency
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Provider origin
    source: PaymentSource
    source_event_id: str = Field(..., min_length=1, max_length=256)

    # Merchant
    merchant_id: str = Field(..., min_length=1, max_length=256)
    merchant_name: Optional[str] = Field(None, max_length=256)

    # Timestamp — must be timezone-aware, stored as UTC
    timestamp: datetime

    # Amount — Decimal only, never float
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)

    # Status — dual representation preserves provider-specific info
    normalized_status: NormalizedStatus
    provider_status: Optional[str] = Field(None, max_length=128)

    # Payment details
    payment_method: Optional[str] = Field(None, max_length=64)
    event_type: EventType = EventType.PAYMENT

    # Non-sensitive provider metadata (bounded)
    source_metadata: dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    received_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Schema version
    schema_version: str = Field(default="1.0")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_timezone(cls, v: datetime) -> datetime:
        """Reject naive timestamps; normalize to UTC."""
        if v.tzinfo is None:
            raise ValueError(
                "Timestamp must be timezone-aware. Naive timestamps are rejected. "
                "Provide a UTC or timezone-offset timestamp."
            )
        return v.astimezone(timezone.utc)

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount_decimal(cls, v: Any) -> Decimal:
        """Ensure amount is Decimal, never float."""
        if isinstance(v, float):
            # Accept floats from JSON but convert to Decimal via string
            # to avoid binary floating-point precision issues
            v = Decimal(str(v))
        elif isinstance(v, (int, str)):
            try:
                v = Decimal(str(v))
            except InvalidOperation:
                raise ValueError(f"Invalid decimal amount: {v}")
        if not isinstance(v, Decimal):
            raise ValueError(f"Amount must be Decimal, got {type(v).__name__}")
        return v

    @field_validator("source_metadata")
    @classmethod
    def validate_metadata(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Enforce metadata safety boundaries."""
        if len(v) > MAX_METADATA_KEYS:
            raise ValueError(
                f"Metadata exceeds maximum key count ({MAX_METADATA_KEYS})"
            )

        # Check for forbidden keys (secrets/credentials)
        for key in v:
            if key.lower().replace("-", "_") in _FORBIDDEN_METADATA_KEYS:
                raise ValueError(
                    f"Metadata key '{key}' appears to be a secret/credential "
                    "and must not be included"
                )

        # Check nesting depth
        if not _validate_metadata_depth(v):
            raise ValueError(
                f"Metadata nesting exceeds maximum depth ({MAX_METADATA_DEPTH})"
            )

        # Check approximate total size
        import json
        try:
            serialized = json.dumps(v, default=str)
            if len(serialized) > MAX_METADATA_TOTAL_SIZE:
                raise ValueError(
                    f"Metadata exceeds maximum size ({MAX_METADATA_TOTAL_SIZE} bytes)"
                )
        except (TypeError, ValueError) as e:
            if "maximum size" in str(e):
                raise
            raise ValueError(f"Metadata is not JSON-serializable: {e}")

        return v

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }

    @property
    def idempotency_key(self) -> str:
        """The true idempotency identity: source + source_event_id."""
        return f"{self.source.value}:{self.source_event_id}"


# ── Pipeline Status ───────────────────────────────────────────

class PipelineStatus(BaseModel):
    """Shows exactly what happened and what did NOT happen."""
    payload_validated: bool = False
    canonical_event_created: bool = False
    historical_aggregation: str = "future_phase"
    detection_execution: str = "not_triggered"
    ai_analysis: str = "not_triggered"


# ── Ingestion Result ──────────────────────────────────────────

class IngestionResult(BaseModel):
    """Response after integration processing."""
    event_id: Optional[str] = None
    status: IngestionStatus
    canonical_event: Optional[CanonicalPaymentEvent] = None
    validation_errors: list[str] = Field(default_factory=list)
    pipeline_status: PipelineStatus = Field(default_factory=PipelineStatus)
    duplicate_of: Optional[str] = None  # canonical event_id if duplicate

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }


# ── Integration Status ────────────────────────────────────────

class ProviderStatus(BaseModel):
    """Status of a single provider."""
    available: Optional[bool] = None
    adapter_ready: Optional[bool] = None
    configured: Optional[bool] = None
    connected: Optional[bool] = None


class IntegrationReadiness(BaseModel):
    """Architecture-level readiness flags."""
    provider_abstraction: bool = True
    canonical_normalization: bool = True
    payload_validation: bool = True
    idempotency_boundary: bool = True


class IntegrationStatusResponse(BaseModel):
    """
    Honest integration readiness report.
    adapter_ready ≠ connected.
    """
    current_data_mode: str = "dataset"
    integration_readiness: IntegrationReadiness = Field(
        default_factory=IntegrationReadiness
    )
    providers: dict[str, ProviderStatus] = Field(default_factory=dict)
