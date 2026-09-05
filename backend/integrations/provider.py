"""
Payment Burst Sentinel — Provider Abstraction (Phase 16)
=========================================================
Abstract base for payment data providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.integrations.schemas import CanonicalPaymentEvent, IntegrationMode


class PaymentDataProvider(ABC):
    """
    Abstract payment data provider.

    Each provider maps external payloads into CanonicalPaymentEvent.
    The existing historical dataset is NOT a provider — it remains
    a separate read-only pipeline.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier (e.g., 'demo', 'razorpay')."""
        ...

    @property
    @abstractmethod
    def provider_mode(self) -> IntegrationMode:
        """Operational mode (demo, sandbox). Never 'live' in Phase 16."""
        ...

    @abstractmethod
    def validate(self, payload: dict[str, Any]) -> list[str]:
        """
        Validate a raw provider payload.

        Returns a list of validation error strings.
        Empty list means valid.
        """
        ...

    @abstractmethod
    def normalize(self, payload: dict[str, Any]) -> CanonicalPaymentEvent:
        """
        Normalize a validated provider payload into a CanonicalPaymentEvent.

        Must only be called after validate() returns no errors.
        """
        ...
