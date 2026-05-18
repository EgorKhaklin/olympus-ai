"""Lethe — the river of forgetting.

The dead drank from Lethe to forget their mortal lives before passing
into the afterlife. Olympus's Lethe is the ephemeral cache: data that
is intentionally short-lived, never persisted to disk, never archived.

Anything written to Lethe is forgotten on process exit. Use it for
caches, in-memory state, anything you'd be embarrassed to find later.
"""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Any


@dataclass
class _Memory:
    value: Any
    expires_at: float


class Lethe:
    """In-memory cache with TTL. Thread-safe. Forgotten on exit."""

    def __init__(self, default_ttl_seconds: float = 300.0) -> None:
        self._memories: dict[str, _Memory] = {}
        self._lock = threading.Lock()
        self.default_ttl = default_ttl_seconds

    def forget(self, key: str, value: Any, ttl: float | None = None) -> None:
        """Store `value` under `key`, to be forgotten after `ttl` seconds."""
        ttl = ttl if ttl is not None else self.default_ttl
        with self._lock:
            self._memories[key] = _Memory(value, time.time() + ttl)

    def remembered(self, key: str, default: Any = None) -> Any:
        """Retrieve `value` if still in memory, else `default`."""
        with self._lock:
            mem = self._memories.get(key)
            if mem is None:
                return default
            if time.time() >= mem.expires_at:
                del self._memories[key]
                return default
            return mem.value

    def drink(self, key: str) -> Any:
        """Retrieve AND forget — true Lethe behavior."""
        with self._lock:
            mem = self._memories.pop(key, None)
            if mem is None or time.time() >= mem.expires_at:
                return None
            return mem.value

    def __len__(self) -> int:
        with self._lock:
            self._sweep()
            return len(self._memories)

    def _sweep(self) -> None:
        now = time.time()
        dead = [k for k, m in self._memories.items() if now >= m.expires_at]
        for k in dead:
            del self._memories[k]


lethe = Lethe()
forget = lethe.forget
remembered = lethe.remembered
