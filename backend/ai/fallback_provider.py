"""
Payment Burst Sentinel — Fallback Provider
============================================
Deterministic fallback when Gemini is unavailable.
Returns structured unavailable status without fabricating AI output.
"""

from .provider import InvestigationAIProvider
from .schemas import InvestigationEvidence, AIBriefResponse


class FallbackProvider(InvestigationAIProvider):
    """Fallback provider when AI is not configured or unavailable."""

    def __init__(self, reason: str = "AI investigation intelligence is not configured."):
        self._reason = reason

    @property
    def provider_name(self) -> str:
        return "fallback"

    @property
    def model_name(self) -> str:
        return "none"

    async def generate_brief(
        self, evidence: InvestigationEvidence
    ) -> AIBriefResponse:
        """Return unavailable status — never fabricate AI output."""
        return AIBriefResponse.unavailable(self._reason)
