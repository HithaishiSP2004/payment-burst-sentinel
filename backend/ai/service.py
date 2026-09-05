"""
Payment Burst Sentinel — AI Service Layer
===========================================
Orchestrates the AI investigation intelligence pipeline.
Thin route handlers delegate here for all AI logic.
"""

import asyncio
import logging
import os
from typing import Optional

from .schemas import AIBriefResponse, InvestigationEvidence
from .evidence_builder import build_evidence
from .cache import AIBriefCache
from .provider import InvestigationAIProvider
from .gemini_provider import GeminiProvider
from .fallback_provider import FallbackProvider

logger = logging.getLogger(__name__)

# Singleton cache instance
_cache = AIBriefCache()

# Concurrency guard — prevent duplicate simultaneous generations
_in_progress: set[str] = set()


def _is_ai_enabled() -> bool:
    """Check if AI features are enabled via environment."""
    return os.environ.get("AI_ENABLED", "true").lower() in ("true", "1", "yes")


def _reload_env_if_needed() -> None:
    """Dynamically load .env if GEMINI_API_KEY is not yet in os.environ."""
    if not os.environ.get("GEMINI_API_KEY"):
        from pathlib import Path
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().strip("'\"")
                            if k:
                                os.environ[k] = v
            except Exception:
                pass


def _get_provider() -> InvestigationAIProvider:
    """Get the appropriate AI provider based on configuration."""
    _reload_env_if_needed()

    if not _is_ai_enabled():
        return FallbackProvider("AI investigation intelligence is disabled.")

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return FallbackProvider(
            "AI investigation intelligence is not configured. "
            "Set GEMINI_API_KEY to enable Gemini integration."
        )

    try:
        return GeminiProvider()
    except Exception as e:
        logger.error(f"Failed to initialize Gemini provider: {e}")
        return FallbackProvider(
            "AI provider initialization failed. "
            "The deterministic investigation evidence remains available."
        )


async def generate_investigation_brief(
    investigation_detail: dict,
) -> AIBriefResponse:
    """
    Main orchestration: build evidence → check cache → generate → validate → cache.

    Args:
        investigation_detail: Dict from get_investigation_detail()

    Returns:
        AIBriefResponse with structured brief or unavailable status
    """
    # Step 1: Build deterministic evidence
    try:
        evidence = build_evidence(investigation_detail)
    except Exception as e:
        logger.error(f"Evidence building failed: {e}")
        return AIBriefResponse.unavailable(
            "Failed to build investigation evidence."
        )

    # Step 2: Get provider
    provider = _get_provider()

    # Step 3: Create cache key
    cache_key = _cache.make_key(evidence, provider.model_name)

    # Step 4: Check cache
    cached = _cache.get(cache_key)
    if cached:
        logger.info(f"Cache hit for {evidence.event_id}")
        return cached

    # Step 5: Concurrency guard
    if cache_key in _in_progress:
        return AIBriefResponse.unavailable(
            "An AI brief is already being generated for this event. Please wait."
        )

    _in_progress.add(cache_key)
    try:
        # Step 6: Generate via provider
        logger.info(
            f"Generating AI brief for {evidence.event_id} "
            f"via {provider.provider_name}/{provider.model_name}"
        )
        response = await provider.generate_brief(evidence)

        # Step 7: Cache successful responses
        if response.status == "available":
            _cache.put(cache_key, response)
            logger.info(f"Cached AI brief for {evidence.event_id}")

        return response

    finally:
        _in_progress.discard(cache_key)


def get_cache_stats() -> dict:
    """Get cache statistics for diagnostics."""
    return {
        "cached_entries": _cache.size,
        "in_progress": len(_in_progress),
    }
