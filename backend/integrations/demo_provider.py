"""
Payment Burst Sentinel — Demo Provider (Phase 16)
===================================================
Fully working demo provider for integration demonstration.

All output is clearly labeled SIMULATED PROVIDER PAYLOAD.
This provider:
- operates without credentials
- generates synthetic integration payload examples
- NEVER claims to be live Razorpay data
- NEVER fabricates historical analytical metrics or fraud outcomes
- NEVER accepts provider credentials
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
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
from backend.integrations.validator import validate_payload


# ── Demo fixtures ──────────────────────────────────────────────

DEMO_MERCHANTS = [
    {"id": "demo_merchant_001", "name": "Acme Electronics (Demo)"},
    {"id": "demo_merchant_002", "name": "CloudBooks SaaS (Demo)"},
    {"id": "demo_merchant_003", "name": "FreshMart Delivery (Demo)"},
]

DEMO_PAYMENT_METHODS = ["card", "upi", "netbanking", "wallet"]

DEMO_SCENARIOS = [
    {
        "source_event_id": "demo_pay_001",
        "merchant_id": "demo_merchant_001",
        "merchant_name": "Acme Electronics (Demo)",
        "amount": "2499.00",
        "currency": "INR",
        "status": "captured",
        "payment_method": "card",
        "event_type": "payment",
    },
    {
        "source_event_id": "demo_pay_002",
        "merchant_id": "demo_merchant_002",
        "merchant_name": "CloudBooks SaaS (Demo)",
        "amount": "599.00",
        "currency": "INR",
        "status": "captured",
        "payment_method": "upi",
        "event_type": "payment",
    },
    {
        "source_event_id": "demo_pay_003",
        "merchant_id": "demo_merchant_003",
        "merchant_name": "FreshMart Delivery (Demo)",
        "amount": "1275.50",
        "currency": "INR",
        "status": "authorized",
        "payment_method": "wallet",
        "event_type": "payment",
    },
]

_demo_counter = 0


class DemoProvider(PaymentDataProvider):
    """
    Demo integration provider.

    Generates synthetic integration payloads for architecture demonstration.
    All output is explicitly simulated — never claims to represent real
    payment traffic or analytical data.
    """

    @property
    def provider_name(self) -> str:
        return "demo"

    @property
    def provider_mode(self) -> IntegrationMode:
        return IntegrationMode.DEMO

    def validate(self, payload: dict[str, Any]) -> list[str]:
        """Validate a demo payload using standard validation."""
        # Ensure source is demo
        if payload.get("source") != "demo":
            return ["Demo provider only accepts source='demo'"]
        return validate_payload(payload)

    def normalize(self, payload: dict[str, Any]) -> CanonicalPaymentEvent:
        """Normalize a demo payload into a canonical event."""
        timestamp = normalize_timestamp(payload["timestamp"])
        amount = normalize_amount(payload["amount"])

        return CanonicalPaymentEvent(
            source=PaymentSource.DEMO,
            source_event_id=payload["source_event_id"],
            merchant_id=payload["merchant_id"],
            merchant_name=payload.get("merchant_name"),
            timestamp=timestamp,
            amount=amount,
            currency=payload.get("currency", "INR").upper(),
            normalized_status=NormalizedStatus(
                payload.get("normalized_status")
                or payload.get("status", "captured")
            ),
            provider_status=payload.get("status"),
            payment_method=payload.get("payment_method"),
            event_type=EventType(payload.get("event_type", "payment")),
            source_metadata={
                "provider": "demo",
                "mode": "simulated",
                "label": "SIMULATED PROVIDER PAYLOAD",
            },
        )

    def generate_demo_payload(self) -> dict[str, Any]:
        """
        Generate a synthetic demo payload for demonstration.

        Each call produces a unique event with a deterministic structure.
        The output is clearly labeled as simulated.
        """
        global _demo_counter
        scenario = DEMO_SCENARIOS[_demo_counter % len(DEMO_SCENARIOS)]
        _demo_counter += 1

        return {
            "source": "demo",
            "source_event_id": f"demo_evt_{uuid.uuid4().hex[:12]}",
            "merchant_id": scenario["merchant_id"],
            "merchant_name": scenario["merchant_name"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "amount": scenario["amount"],
            "currency": scenario["currency"],
            "status": scenario["status"],
            "payment_method": scenario["payment_method"],
            "event_type": scenario["event_type"],
            "source_metadata": {
                "provider": "demo",
                "mode": "simulated",
                "label": "SIMULATED PROVIDER PAYLOAD",
            },
        }
