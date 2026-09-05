"""
Payment Burst Sentinel — Idempotency Store (Phase 16)
=======================================================
Bounded in-memory idempotency store.

Key: source + source_event_id (NOT the auto-generated canonical UUID).

Limitations (documented):
- In-memory only — application restart clears the store
- NOT production-durable
- Bounded to ~10,000 entries with TTL eviction
- Failure isolated — does not affect detection, evaluation, or Gemini
"""

from __future__ import annotations

import time
import threading
from collections import OrderedDict
from typing import Optional


# ── Configuration ──────────────────────────────────────────────

MAX_ENTRIES = 10_000
DEFAULT_TTL_SECONDS = 3600  # 1 hour


class IdempotencyEntry:
    """A single idempotency record."""

    __slots__ = ("canonical_event_id", "created_at")

    def __init__(self, canonical_event_id: str):
        self.canonical_event_id = canonical_event_id
        self.created_at = time.monotonic()


class IdempotencyStore:
    """
    Bounded in-memory idempotency store.

    Thread-safe. Uses source + source_event_id as the deduplication key.
    Different providers using the same source_event_id are NOT duplicates.

    Critical rules:
    - Invalid payloads must NEVER be recorded
    - Only successfully normalized events are recorded
    - Duplicate lookups return the previously known canonical event_id
    """

    def __init__(
        self,
        max_entries: int = MAX_ENTRIES,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
    ):
        self._store: OrderedDict[str, IdempotencyEntry] = OrderedDict()
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._lock = threading.Lock()

    @staticmethod
    def make_key(source: str, source_event_id: str) -> str:
        """
        Create the idempotency key.

        Uses source + source_event_id to ensure different providers
        with the same source_event_id are NOT treated as duplicates.
        """
        return f"{source}:{source_event_id}"

    def check_duplicate(self, source: str, source_event_id: str) -> Optional[str]:
        """
        Check if an event is a duplicate.

        Returns the canonical_event_id if duplicate, None if new.
        Does NOT record anything — recording happens only after
        successful normalization.
        """
        key = self.make_key(source, source_event_id)

        with self._lock:
            self._evict_expired()

            entry = self._store.get(key)
            if entry is not None:
                # Move to end (most recently accessed)
                self._store.move_to_end(key)
                return entry.canonical_event_id

        return None

    def record(self, source: str, source_event_id: str, canonical_event_id: str) -> None:
        """
        Record a successfully processed event.

        ONLY call this after full validation and successful normalization.
        Invalid payloads must NEVER reach this method.
        """
        key = self.make_key(source, source_event_id)

        with self._lock:
            self._evict_expired()

            # Evict oldest if at capacity
            while len(self._store) >= self._max_entries:
                self._store.popitem(last=False)

            self._store[key] = IdempotencyEntry(canonical_event_id)

    def _evict_expired(self) -> None:
        """Remove entries that have exceeded TTL."""
        now = time.monotonic()
        expired_keys = [
            k for k, v in self._store.items()
            if (now - v.created_at) > self._ttl_seconds
        ]
        for k in expired_keys:
            del self._store[k]

    @property
    def size(self) -> int:
        """Current number of entries (for monitoring)."""
        with self._lock:
            return len(self._store)

    def clear(self) -> None:
        """Clear all entries (for testing)."""
        with self._lock:
            self._store.clear()
