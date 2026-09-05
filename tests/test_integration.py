"""
Payment Burst Sentinel — Integration Tests (Phase 16)
=======================================================
Comprehensive tests for the integration readiness layer.

Tests verify:
- Canonical schema integrity
- Validation boundaries
- Normalization (Decimal, UTC)
- Idempotency behavior
- Provider contracts
- Signature verification
- Source honesty
- Pipeline isolation
"""

import hashlib
import hmac
import os
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest

from backend.integrations.schemas import (
    CanonicalPaymentEvent,
    PaymentSource,
    NormalizedStatus,
    EventType,
    IntegrationMode,
    IngestionResult,
    IngestionStatus,
    PipelineStatus,
)
from backend.integrations.validator import (
    validate_payload,
    validate_payload_size,
    extract_identity,
)
from backend.integrations.normalizer import (
    normalize_timestamp,
    normalize_amount,
    normalize_currency,
)
from backend.integrations.demo_provider import DemoProvider
from backend.integrations.razorpay_adapter import RazorpayAdapter
from backend.integrations.idempotency import IdempotencyStore
from backend.integrations.service import (
    process_demo_ingestion,
    get_integration_status,
)


# ── Fixtures ───────────────────────────────────────────────────

def make_valid_demo_payload(**overrides):
    """Create a valid demo payload for testing."""
    payload = {
        "source": "demo",
        "source_event_id": f"test_{uuid.uuid4().hex[:8]}",
        "merchant_id": "test_merchant_001",
        "merchant_name": "Test Merchant (Demo)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "amount": "1500.00",
        "currency": "INR",
        "status": "captured",
        "payment_method": "card",
        "event_type": "payment",
    }
    payload.update(overrides)
    return payload


# ═══════════════════════════════════════════════════════════════
# CANONICAL SCHEMA TESTS
# ═══════════════════════════════════════════════════════════════

class TestCanonicalSchema:
    """Tests for CanonicalPaymentEvent model."""

    def test_valid_event_creation(self):
        """Valid event creates successfully."""
        event = CanonicalPaymentEvent(
            source=PaymentSource.DEMO,
            source_event_id="test_001",
            merchant_id="m001",
            timestamp=datetime.now(timezone.utc),
            amount=Decimal("1500.00"),
            normalized_status=NormalizedStatus.CAPTURED,
        )
        assert event.event_id  # UUID auto-generated
        assert event.schema_version == "1.0"
        assert event.source == PaymentSource.DEMO

    def test_decimal_amount_preserved(self):
        """Amount stays as Decimal, never float."""
        event = CanonicalPaymentEvent(
            source=PaymentSource.DEMO,
            source_event_id="test_002",
            merchant_id="m001",
            timestamp=datetime.now(timezone.utc),
            amount=Decimal("1234.56"),
            normalized_status=NormalizedStatus.CAPTURED,
        )
        assert isinstance(event.amount, Decimal)
        assert event.amount == Decimal("1234.56")

    def test_float_converted_to_decimal_via_string(self):
        """Float input is converted via string to avoid precision loss."""
        event = CanonicalPaymentEvent(
            source=PaymentSource.DEMO,
            source_event_id="test_003",
            merchant_id="m001",
            timestamp=datetime.now(timezone.utc),
            amount=99.99,  # float input
            normalized_status=NormalizedStatus.CAPTURED,
        )
        assert isinstance(event.amount, Decimal)
        assert event.amount == Decimal("99.99")

    def test_naive_timestamp_rejected(self):
        """Naive timestamps must be rejected."""
        with pytest.raises(Exception):
            CanonicalPaymentEvent(
                source=PaymentSource.DEMO,
                source_event_id="test_004",
                merchant_id="m001",
                timestamp=datetime(2024, 1, 15, 10, 30, 0),  # naive
                amount=Decimal("100"),
                normalized_status=NormalizedStatus.CAPTURED,
            )

    def test_utc_normalization(self):
        """Timezone-aware timestamps normalize to UTC."""
        ist = timezone(timedelta(hours=5, minutes=30))
        ts = datetime(2024, 1, 15, 16, 0, 0, tzinfo=ist)  # 4 PM IST
        event = CanonicalPaymentEvent(
            source=PaymentSource.DEMO,
            source_event_id="test_005",
            merchant_id="m001",
            timestamp=ts,
            amount=Decimal("100"),
            normalized_status=NormalizedStatus.CAPTURED,
        )
        assert event.timestamp.tzinfo == timezone.utc
        assert event.timestamp.hour == 10  # 4 PM IST = 10:30 AM UTC

    def test_no_fraud_label_required(self):
        """Schema does not require is_fraud_tagged."""
        event = CanonicalPaymentEvent(
            source=PaymentSource.DEMO,
            source_event_id="test_006",
            merchant_id="m001",
            timestamp=datetime.now(timezone.utc),
            amount=Decimal("100"),
            normalized_status=NormalizedStatus.CAPTURED,
        )
        assert not hasattr(event, "is_fraud_tagged")

    def test_idempotency_key(self):
        """Idempotency key uses source + source_event_id."""
        event = CanonicalPaymentEvent(
            source=PaymentSource.DEMO,
            source_event_id="test_idem",
            merchant_id="m001",
            timestamp=datetime.now(timezone.utc),
            amount=Decimal("100"),
            normalized_status=NormalizedStatus.CAPTURED,
        )
        assert event.idempotency_key == "demo:test_idem"

    def test_metadata_rejects_secrets(self):
        """Metadata containing secret-like keys is rejected."""
        with pytest.raises(Exception):
            CanonicalPaymentEvent(
                source=PaymentSource.DEMO,
                source_event_id="test_secret",
                merchant_id="m001",
                timestamp=datetime.now(timezone.utc),
                amount=Decimal("100"),
                normalized_status=NormalizedStatus.CAPTURED,
                source_metadata={"api_key": "sk_live_xxx"},
            )


# ═══════════════════════════════════════════════════════════════
# VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════

class TestValidation:
    """Tests for payload validation."""

    def test_valid_payload(self):
        errors = validate_payload(make_valid_demo_payload())
        assert errors == []

    def test_missing_merchant_id(self):
        errors = validate_payload(make_valid_demo_payload(merchant_id=""))
        assert any("merchant_id" in e for e in errors)

    def test_invalid_source(self):
        errors = validate_payload(make_valid_demo_payload(source="stripe"))
        assert any("Unsupported source" in e for e in errors)

    def test_invalid_amount_negative(self):
        errors = validate_payload(make_valid_demo_payload(amount="-50"))
        assert any("positive" in e.lower() for e in errors)

    def test_invalid_timestamp_naive(self):
        errors = validate_payload(make_valid_demo_payload(timestamp="2024-01-15T10:30:00"))
        assert any("timezone" in e.lower() for e in errors)

    def test_oversized_payload(self):
        errors = validate_payload_size("x" * 20_000)
        assert any("maximum size" in e for e in errors)

    def test_metadata_too_many_keys(self):
        metadata = {f"key_{i}": f"val_{i}" for i in range(25)}
        errors = validate_payload(make_valid_demo_payload(source_metadata=metadata))
        assert any("key count" in e for e in errors)

    def test_malformed_amount(self):
        errors = validate_payload(make_valid_demo_payload(amount="not_a_number"))
        assert any("Invalid amount" in e for e in errors)


# ═══════════════════════════════════════════════════════════════
# NORMALIZER TESTS
# ═══════════════════════════════════════════════════════════════

class TestNormalizer:

    def test_timestamp_utc_normalization(self):
        result = normalize_timestamp("2024-06-15T10:30:00+05:30")
        assert result.tzinfo == timezone.utc
        assert result.hour == 5  # 10:30 IST = 5:00 UTC

    def test_timestamp_naive_rejected(self):
        with pytest.raises(ValueError, match="Naive"):
            normalize_timestamp("2024-06-15T10:30:00")

    def test_amount_decimal(self):
        result = normalize_amount("1234.56")
        assert isinstance(result, Decimal)
        assert result == Decimal("1234.56")

    def test_amount_float_via_string(self):
        result = normalize_amount(99.99)
        assert isinstance(result, Decimal)
        assert result == Decimal("99.99")

    def test_currency_uppercase(self):
        assert normalize_currency("inr") == "INR"
        assert normalize_currency(None) == "INR"


# ═══════════════════════════════════════════════════════════════
# IDEMPOTENCY TESTS
# ═══════════════════════════════════════════════════════════════

class TestIdempotency:

    def setup_method(self):
        self.store = IdempotencyStore(max_entries=100, ttl_seconds=60)

    def test_first_event_accepted(self):
        result = self.store.check_duplicate("demo", "evt_001")
        assert result is None

    def test_duplicate_detected(self):
        self.store.record("demo", "evt_001", "canonical_001")
        result = self.store.check_duplicate("demo", "evt_001")
        assert result == "canonical_001"

    def test_different_sources_not_duplicate(self):
        """Different providers with same source_event_id are NOT duplicates."""
        self.store.record("demo", "evt_001", "canonical_001")
        result = self.store.check_duplicate("razorpay", "evt_001")
        assert result is None

    def test_canonical_uuid_not_used_as_key(self):
        """Idempotency key is source:source_event_id, not UUID."""
        key = IdempotencyStore.make_key("demo", "evt_001")
        assert key == "demo:evt_001"

    def test_max_entries_eviction(self):
        store = IdempotencyStore(max_entries=5, ttl_seconds=60)
        for i in range(10):
            store.record("demo", f"evt_{i}", f"can_{i}")
        assert store.size <= 5


# ═══════════════════════════════════════════════════════════════
# PROVIDER TESTS
# ═══════════════════════════════════════════════════════════════

class TestDemoProvider:

    def setup_method(self):
        self.provider = DemoProvider()

    def test_provider_name(self):
        assert self.provider.provider_name == "demo"

    def test_provider_mode(self):
        assert self.provider.provider_mode == IntegrationMode.DEMO

    def test_validate_valid_payload(self):
        payload = make_valid_demo_payload()
        errors = self.provider.validate(payload)
        assert errors == []

    def test_validate_wrong_source(self):
        payload = make_valid_demo_payload(source="razorpay")
        errors = self.provider.validate(payload)
        assert len(errors) > 0

    def test_normalize_creates_canonical(self):
        payload = make_valid_demo_payload()
        event = self.provider.normalize(payload)
        assert isinstance(event, CanonicalPaymentEvent)
        assert event.source == PaymentSource.DEMO
        assert isinstance(event.amount, Decimal)

    def test_generate_demo_payload(self):
        payload = self.provider.generate_demo_payload()
        assert payload["source"] == "demo"
        assert "source_event_id" in payload
        assert payload["source_metadata"]["label"] == "SIMULATED PROVIDER PAYLOAD"


# ═══════════════════════════════════════════════════════════════
# RAZORPAY ADAPTER TESTS
# ═══════════════════════════════════════════════════════════════

class TestRazorpayAdapter:

    def setup_method(self):
        self.adapter = RazorpayAdapter()

    def test_not_configured_by_default(self):
        assert not self.adapter.is_configured

    def test_missing_secret_verification_fails(self):
        """Missing webhook secret → verification ALWAYS fails."""
        result = self.adapter.verify_signature(b"payload", "fake_sig")
        assert result is False

    def test_invalid_signature_rejected(self):
        """Invalid signature is rejected."""
        os.environ["RAZORPAY_WEBHOOK_SECRET"] = "test_secret_123"
        os.environ["RAZORPAY_INTEGRATION_ENABLED"] = "true"
        try:
            result = self.adapter.verify_signature(b"payload", "wrong_signature")
            assert result is False
        finally:
            del os.environ["RAZORPAY_WEBHOOK_SECRET"]
            del os.environ["RAZORPAY_INTEGRATION_ENABLED"]

    def test_valid_signature_accepted(self):
        """Valid HMAC signature passes verification."""
        secret = "test_secret_456"
        payload = b'{"event":"payment.captured"}'
        expected_sig = hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()

        os.environ["RAZORPAY_WEBHOOK_SECRET"] = secret
        os.environ["RAZORPAY_INTEGRATION_ENABLED"] = "true"
        try:
            result = self.adapter.verify_signature(payload, expected_sig)
            assert result is True
        finally:
            del os.environ["RAZORPAY_WEBHOOK_SECRET"]
            del os.environ["RAZORPAY_INTEGRATION_ENABLED"]

    def test_hmac_compare_digest_used(self):
        """Verify constant-time comparison is used (via hmac module)."""
        import inspect
        source = inspect.getsource(self.adapter.verify_signature)
        assert "compare_digest" in source


# ═══════════════════════════════════════════════════════════════
# HONESTY TESTS
# ═══════════════════════════════════════════════════════════════

class TestSourceHonesty:
    """Verify the system never claims to be live."""

    def test_demo_not_live(self):
        provider = DemoProvider()
        assert provider.provider_mode != IntegrationMode.DATASET
        assert provider.provider_mode == IntegrationMode.DEMO

    def test_no_live_mode(self):
        """'live' is not a valid IntegrationMode."""
        valid_modes = [m.value for m in IntegrationMode]
        assert "live" not in valid_modes

    def test_adapter_ready_not_connected(self):
        """Integration status distinguishes adapter_ready from connected."""
        status = get_integration_status()
        rzp = status.providers["razorpay"]
        assert rzp.adapter_ready is True
        assert rzp.connected is False


# ═══════════════════════════════════════════════════════════════
# ISOLATION TESTS
# ═══════════════════════════════════════════════════════════════

class TestPipelineIsolation:
    """Verify demo ingestion does not affect the analytical pipeline."""

    def test_no_data_processed_mutation(self):
        """Demo ingestion does not modify data/processed/."""
        from pathlib import Path
        processed = Path(__file__).parent.parent / "data" / "processed"
        # Record file modification times
        before = {}
        if processed.exists():
            for f in processed.rglob("*"):
                if f.is_file():
                    before[str(f)] = f.stat().st_mtime

        # Run demo ingestion
        process_demo_ingestion()

        # Verify nothing changed
        if processed.exists():
            for f in processed.rglob("*"):
                if f.is_file() and str(f) in before:
                    assert f.stat().st_mtime == before[str(f)], \
                        f"data/processed file was modified: {f.name}"

    def test_pipeline_status_shows_not_triggered(self):
        """Pipeline status explicitly shows detection/AI not triggered."""
        result = process_demo_ingestion()
        assert result.pipeline_status.detection_execution == "not_triggered"
        assert result.pipeline_status.ai_analysis == "not_triggered"
        assert result.pipeline_status.historical_aggregation == "future_phase"

    def test_demo_ingestion_returns_accepted(self):
        """Demo ingestion succeeds and returns canonical event."""
        result = process_demo_ingestion()
        assert result.status == IngestionStatus.ACCEPTED
        assert result.canonical_event is not None
        assert result.pipeline_status.payload_validated is True
        assert result.pipeline_status.canonical_event_created is True


# ═══════════════════════════════════════════════════════════════
# INTEGRATION SERVICE TESTS
# ═══════════════════════════════════════════════════════════════

class TestIntegrationService:

    def test_status_reports_dataset_mode(self):
        status = get_integration_status()
        assert status.current_data_mode == "dataset"

    def test_demo_available(self):
        status = get_integration_status()
        assert status.providers["demo"].available is True

    def test_razorpay_not_configured(self):
        status = get_integration_status()
        assert status.providers["razorpay"].configured is False
        assert status.providers["razorpay"].connected is False

    def test_demo_ingestion_with_custom_payload(self):
        payload = make_valid_demo_payload()
        result = process_demo_ingestion(payload=payload)
        assert result.status == IngestionStatus.ACCEPTED

    def test_demo_ingestion_auto_generate(self):
        result = process_demo_ingestion(payload=None)
        assert result.status == IngestionStatus.ACCEPTED
        assert result.canonical_event is not None

    def test_invalid_payload_rejected(self):
        result = process_demo_ingestion(payload={"source": "demo"})
        assert result.status == IngestionStatus.REJECTED
        assert len(result.validation_errors) > 0
