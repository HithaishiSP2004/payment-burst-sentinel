"""
Payment Burst Sentinel — Payload Validator (Phase 16)
======================================================
Input validation for integration payloads.
Enforces size limits, type checks, and boundary hardening.
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from backend.integrations.schemas import (
    PaymentSource, NormalizedStatus, EventType,
    MAX_METADATA_TOTAL_SIZE, MAX_METADATA_KEYS,
)

# ── Payload limits ─────────────────────────────────────────────

MAX_PAYLOAD_SIZE_BYTES = 16_384  # 16 KB
MAX_STRING_LENGTH = 256
REQUIRED_FIELDS = {"source", "source_event_id", "merchant_id", "timestamp", "amount"}
VALID_SOURCES = {s.value for s in PaymentSource}
VALID_STATUSES = {s.value for s in NormalizedStatus}
VALID_EVENT_TYPES = {e.value for e in EventType}


def validate_payload_size(raw_body: str | bytes) -> list[str]:
    """Check raw request body size."""
    size = len(raw_body) if isinstance(raw_body, bytes) else len(raw_body.encode("utf-8"))
    if size > MAX_PAYLOAD_SIZE_BYTES:
        return [f"Payload exceeds maximum size ({MAX_PAYLOAD_SIZE_BYTES} bytes, got {size})"]
    return []


def validate_payload(payload: dict[str, Any]) -> list[str]:
    """
    Full validation of an integration payload.

    Returns list of error strings. Empty = valid.
    """
    errors: list[str] = []

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in payload or payload[field] is None:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors  # Can't continue without required fields

    # Source validation
    source = payload.get("source", "")
    if source not in VALID_SOURCES:
        errors.append(
            f"Unsupported source: '{source}'. "
            f"Supported: {', '.join(sorted(VALID_SOURCES))}"
        )

    # source_event_id
    seid = payload.get("source_event_id", "")
    if not isinstance(seid, str) or len(seid) == 0:
        errors.append("source_event_id must be a non-empty string")
    elif len(seid) > MAX_STRING_LENGTH:
        errors.append(f"source_event_id exceeds maximum length ({MAX_STRING_LENGTH})")

    # merchant_id
    mid = payload.get("merchant_id", "")
    if not isinstance(mid, str) or len(mid) == 0:
        errors.append("merchant_id must be a non-empty string")
    elif len(mid) > MAX_STRING_LENGTH:
        errors.append(f"merchant_id exceeds maximum length ({MAX_STRING_LENGTH})")

    # merchant_name (optional)
    mname = payload.get("merchant_name")
    if mname is not None:
        if not isinstance(mname, str):
            errors.append("merchant_name must be a string")
        elif len(mname) > MAX_STRING_LENGTH:
            errors.append(f"merchant_name exceeds maximum length ({MAX_STRING_LENGTH})")

    # Timestamp
    ts = payload.get("timestamp")
    if ts is not None:
        if isinstance(ts, str):
            try:
                parsed = datetime.fromisoformat(ts)
                if parsed.tzinfo is None:
                    errors.append(
                        "Timestamp must be timezone-aware (e.g., '2024-01-15T10:30:00+05:30' "
                        "or '2024-01-15T05:00:00Z'). Naive timestamps are rejected."
                    )
            except (ValueError, TypeError):
                errors.append(f"Invalid timestamp format: '{ts}'. Use ISO 8601.")
        elif isinstance(ts, datetime):
            if ts.tzinfo is None:
                errors.append("Timestamp must be timezone-aware. Naive timestamps are rejected.")
        else:
            errors.append(f"Timestamp must be a string or datetime, got {type(ts).__name__}")

    # Amount
    amt = payload.get("amount")
    if amt is not None:
        try:
            decimal_amt = Decimal(str(amt))
            if decimal_amt <= 0:
                errors.append(f"Amount must be positive, got {amt}")
        except (InvalidOperation, TypeError, ValueError):
            errors.append(f"Invalid amount: '{amt}'. Must be a valid number.")

    # Currency (optional, defaults to INR)
    currency = payload.get("currency", "INR")
    if not isinstance(currency, str) or len(currency) != 3:
        errors.append("Currency must be a 3-letter ISO code (e.g., 'INR', 'USD')")

    # Status (optional, defaults to captured)
    status = payload.get("normalized_status") or payload.get("status")
    if status is not None and status not in VALID_STATUSES:
        errors.append(
            f"Invalid status: '{status}'. "
            f"Supported: {', '.join(sorted(VALID_STATUSES))}"
        )

    # Event type (optional)
    etype = payload.get("event_type")
    if etype is not None and etype not in VALID_EVENT_TYPES:
        errors.append(
            f"Invalid event_type: '{etype}'. "
            f"Supported: {', '.join(sorted(VALID_EVENT_TYPES))}"
        )

    # Metadata bounds
    metadata = payload.get("source_metadata", {})
    if isinstance(metadata, dict):
        if len(metadata) > MAX_METADATA_KEYS:
            errors.append(f"source_metadata exceeds maximum key count ({MAX_METADATA_KEYS})")
        try:
            serialized = json.dumps(metadata, default=str)
            if len(serialized) > MAX_METADATA_TOTAL_SIZE:
                errors.append(
                    f"source_metadata exceeds maximum size ({MAX_METADATA_TOTAL_SIZE} bytes)"
                )
        except (TypeError, ValueError):
            errors.append("source_metadata is not JSON-serializable")
    elif metadata is not None:
        errors.append("source_metadata must be a dict or omitted")

    return errors


def extract_identity(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    """
    Extract minimal identity fields for idempotency lookup.

    Returns (source, source_event_id) or (None, None) if missing.
    """
    source = payload.get("source")
    source_event_id = payload.get("source_event_id")

    if not isinstance(source, str) or not isinstance(source_event_id, str):
        return None, None

    return source, source_event_id
