"""
Payment Burst Sentinel — AI Cache
===================================
Bounded in-memory LRU cache for AI investigation briefs.
Cache key includes evidence fingerprint + prompt version + model.
"""

import hashlib
import json
import time
from collections import OrderedDict
from typing import Optional

from .schemas import AIBriefResponse, InvestigationEvidence
from .prompt_builder import AI_PROMPT_VERSION

MAX_CACHE_ENTRIES = 100
CACHE_TTL_SECONDS = 3600  # 1 hour


class AIBriefCache:
    """Bounded LRU cache for AI investigation briefs."""

    def __init__(
        self,
        max_entries: int = MAX_CACHE_ENTRIES,
        ttl_seconds: int = CACHE_TTL_SECONDS,
    ):
        self._cache: OrderedDict[str, tuple[float, AIBriefResponse]] = OrderedDict()
        self._max_entries = max_entries
        self._ttl = ttl_seconds

    def make_key(
        self,
        evidence: InvestigationEvidence,
        model: str,
    ) -> str:
        """
        Create a cache key from evidence fingerprint + prompt version + model.
        Changes to any of these invalidate the cache entry.
        """
        # Evidence fingerprint — hash of the full evidence payload
        evidence_json = json.dumps(
            evidence.model_dump(), sort_keys=True, default=str
        )
        evidence_hash = hashlib.sha256(evidence_json.encode()).hexdigest()[:16]

        key_parts = f"{evidence.event_id}|{evidence_hash}|{AI_PROMPT_VERSION}|{model}"
        return hashlib.sha256(key_parts.encode()).hexdigest()[:32]

    def get(self, key: str) -> Optional[AIBriefResponse]:
        """Get cached response if exists and not expired."""
        if key not in self._cache:
            return None

        timestamp, response = self._cache[key]

        # Check TTL
        if time.time() - timestamp > self._ttl:
            del self._cache[key]
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)

        # Return with cached flag
        cached_response = response.model_copy()
        cached_response.cached = True
        return cached_response

    def put(self, key: str, response: AIBriefResponse) -> None:
        """Store response in cache. Evicts LRU entries if at capacity."""
        # Remove if already exists
        if key in self._cache:
            del self._cache[key]

        # Evict LRU if at capacity
        while len(self._cache) >= self._max_entries:
            self._cache.popitem(last=False)

        self._cache[key] = (time.time(), response)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    @property
    def size(self) -> int:
        """Current number of cached entries."""
        return len(self._cache)
