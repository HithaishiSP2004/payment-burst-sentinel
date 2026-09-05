"""
Payment Burst Sentinel — Razorpay Adapter (Phase 16)
======================================================
READINESS ONLY — This is NOT a live Razorpay integration.

This adapter:
- Defines mapping logic for Razorpay-style webhook payloads
- Implements signature verification using hmac.compare_digest()
- Does NOT connect to Razorpay
- Does NOT call Razorpay APIs
- Does NOT use the Razorpay SDK
- Does NOT expose a public webhook endpoint

Missing RAZORPAY_WEBHOOK_SECRET means verification is UNAVAILABLE.
Missing secret NEVER bypasses verification.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any

from backend.integrations.provider import PaymentDataProvider
from backend.integrations.schemas import (
    CanonicalPaymentEvent,
    IntegrationMode,
    NormalizedStatus,
    EventType,
    PaymentSource,
)
from backend.integrations.normalizer import normalize_timestamp, normalize_amount


# ── Razorpay status mapping ───────────────────────────────────

_RAZORPAY_STATUS_MAP: dict[str, NormalizedStatus] = {
    "authorized": NormalizedStatus.AUTHORIZED,
    "captured": NormalizedStatus.CAPTURED,
    "failed": NormalizedStatus.FAILED,
    "refunded": NormalizedStatus.REFUNDED,
}

# Event type mapping from Razorpay webhook event names
_RAZORPAY_EVENT_TYPE_MAP: dict[str, EventType] = {
    "payment.authorized": EventType.PAYMENT,
    "payment.captured": EventType.PAYMENT,
    "payment.failed": EventType.PAYMENT,
    "refund.created": EventType.REFUND,
    "refund.processed": EventType.REFUND,
    "payment.dispute.created": EventType.DISPUTE,
}


class RazorpayAdapter(PaymentDataProvider):
    """
    Razorpay integration readiness boundary.

    This adapter demonstrates how future Razorpay webhook payloads
    would be validated, verified, and normalized into canonical events.

    Phase 16 status: ADAPTER READY — NOT CONNECTED.
    """

    @property
    def provider_name(self) -> str:
        return "razorpay"

    @property
    def provider_mode(self) -> IntegrationMode:
        return IntegrationMode.SANDBOX

    @property
    def is_configured(self) -> bool:
        """Check if Razorpay integration credentials are configured."""
        enabled = os.environ.get("RAZORPAY_INTEGRATION_ENABLED", "false").lower()
        secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
        return enabled == "true" and bool(secret)

    @property
    def webhook_secret(self) -> str | None:
        """Get the webhook secret, if configured."""
        secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
        return secret if secret else None

    def verify_signature(self, payload_body: str | bytes, signature: str) -> bool:
        """
        Verify a Razorpay webhook signature.

        Uses hmac.compare_digest() for constant-time comparison.
        Returns False if secret is not configured (NEVER bypasses).

        Args:
            payload_body: Raw request body (string or bytes)
            signature: X-Razorpay-Signature header value
        """
        secret = self.webhook_secret
        if not secret:
            # NO SECRET → NO VERIFICATION → REJECT
            return False

        if isinstance(payload_body, str):
            payload_body = payload_body.encode("utf-8")

        expected = hmac.new(
            secret.encode("utf-8"),
            payload_body,
            hashlib.sha256,
        ).hexdigest()

        # Constant-time comparison prevents timing attacks
        return hmac.compare_digest(expected, signature)

    def validate(self, payload: dict[str, Any]) -> list[str]:
        """
        Validate a Razorpay-style webhook payload.

        Expected structure mirrors Razorpay webhook format:
        {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_xxx",
                        "amount": 50000,  # in paise
                        "currency": "INR",
                        "status": "captured",
                        "method": "card",
                        ...
                    }
                }
            }
        }
        """
        errors: list[str] = []

        if not self.is_configured:
            errors.append(
                "Razorpay integration is not configured. "
                "Set RAZORPAY_INTEGRATION_ENABLED=true and RAZORPAY_WEBHOOK_SECRET."
            )
            return errors

        event = payload.get("event")
        if not event or not isinstance(event, str):
            errors.append("Missing or invalid 'event' field")

        p = payload.get("payload", {})
        payment = p.get("payment", {}).get("entity", {})
        if not payment:
            errors.append("Missing payload.payment.entity structure")
            return errors

        if not payment.get("id"):
            errors.append("Missing payment ID (payload.payment.entity.id)")

        amount = payment.get("amount")
        if amount is None:
            errors.append("Missing amount")
        elif not isinstance(amount, (int, float)):
            errors.append(f"Invalid amount type: {type(amount).__name__}")
        elif amount <= 0:
            errors.append("Amount must be positive")

        return errors

    def normalize(self, payload: dict[str, Any]) -> CanonicalPaymentEvent:
        """
        Normalize a Razorpay-style webhook payload to canonical event.

        Note: Razorpay sends amounts in paise (1/100 INR).
        """
        event_name = payload.get("event", "payment.captured")
        payment = payload["payload"]["payment"]["entity"]

        # Razorpay amounts are in paise — convert to INR
        raw_amount = payment["amount"]
        amount_inr = normalize_amount(raw_amount) / 100

        # Map status
        rzp_status = payment.get("status", "captured")
        normalized_status = _RAZORPAY_STATUS_MAP.get(
            rzp_status, NormalizedStatus.CAPTURED
        )

        # Map event type
        event_type = _RAZORPAY_EVENT_TYPE_MAP.get(
            event_name, EventType.PAYMENT
        )

        # Timestamp
        created_at = payment.get("created_at")
        if created_at and isinstance(created_at, (int, float)):
            from datetime import datetime, timezone
            timestamp = datetime.fromtimestamp(created_at, tz=timezone.utc)
        else:
            from datetime import datetime, timezone
            timestamp = datetime.now(timezone.utc)

        return CanonicalPaymentEvent(
            source=PaymentSource.RAZORPAY,
            source_event_id=payment["id"],
            merchant_id=payment.get("merchant_id", "unknown"),
            merchant_name=payment.get("merchant_name"),
            timestamp=timestamp,
            amount=amount_inr,
            currency=payment.get("currency", "INR"),
            normalized_status=normalized_status,
            provider_status=rzp_status,
            payment_method=payment.get("method"),
            event_type=event_type,
            source_metadata={
                "provider": "razorpay",
                "mode": "sandbox",
                "razorpay_event": event_name,
                "razorpay_payment_id": payment.get("id"),
                "label": "RAZORPAY ADAPTER — READINESS ONLY",
            },
        )
