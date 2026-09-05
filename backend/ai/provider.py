"""
Payment Burst Sentinel — AI Provider Abstraction
==================================================
Abstract base class for investigation AI providers.
"""

from abc import ABC, abstractmethod
from .schemas import InvestigationEvidence, AIBriefResponse


class InvestigationAIProvider(ABC):
    """Abstract provider for AI investigation intelligence."""

    @abstractmethod
    async def generate_brief(
        self, evidence: InvestigationEvidence
    ) -> AIBriefResponse:
        """
        Generate an investigation brief from deterministic evidence.

        Args:
            evidence: Structured deterministic evidence

        Returns:
            AIBriefResponse with structured brief or unavailable status
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier."""
        ...
