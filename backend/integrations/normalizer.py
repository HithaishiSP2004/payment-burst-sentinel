"""
Payment Burst Sentinel — Normalizer (Phase 16)
================================================
Currency and timestamp normalization utilities.

Rules:
- Decimal for all monetary values (never float)
- UTC for all canonical timestamps
- No FX conversion
- Preserve original currency
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any


def normalize_timestamp(value: Any) -> datetime:
    """
    Parse and normalize a timestamp to UTC.

    Accepts:
    - ISO 8601 strings with timezone info
    - datetime objects with timezone info

    Rejects:
    - Naive timestamps (no timezone)
    - Invalid formats
    """
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid timestamp format: '{value}'. Use ISO 8601. Error: {e}")
    elif isinstance(value, datetime):
        dt = value
    else:
        raise ValueError(f"Timestamp must be string or datetime, got {type(value).__name__}")

    if dt.tzinfo is None:
        raise ValueError(
            "Naive timestamp rejected. Provide timezone info "
            "(e.g., '+05:30', 'Z', or '+00:00')."
        )

    return dt.astimezone(timezone.utc)


def normalize_amount(value: Any) -> Decimal:
    """
    Normalize an amount to Decimal.

    Accepts int, float, str, Decimal.
    Float is converted via string representation to avoid binary precision issues.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, (int, str)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            raise ValueError(f"Invalid decimal amount: '{value}'")
    raise ValueError(f"Amount must be numeric, got {type(value).__name__}")


def normalize_currency(value: str | None) -> str:
    """Normalize currency code to uppercase 3-letter ISO."""
    if value is None:
        return "INR"
    return str(value).upper().strip()
