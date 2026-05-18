"""Hyperion — titan of light, father of the Sun, Moon, and Dawn.

Hyperion saw everything that happened under the sky. He fathered Helios
(Sun), Selene (Moon), and Eos (Dawn) — the three lights of the world.
In Olympus, Hyperion is the observability primitive: counters, gauges,
the things that make state visible.

Artemis (precision-metrics) handles latency-quality measurements;
Hyperion handles the simpler counters and gauges that flood the
operator's dashboard.
"""
from __future__ import annotations

import threading
from collections import defaultdict


class Hyperion:
    """Counter + gauge primitives. Lightweight; in-memory."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}
        self._lock = threading.Lock()

    def incr(self, name: str, by: int = 1) -> int:
        """Increment a counter; returns the new value."""
        with self._lock:
            self._counters[name] += by
            return self._counters[name]

    def gauge(self, name: str, value: float) -> None:
        """Set a gauge to `value`."""
        with self._lock:
            self._gauges[name] = value

    def snapshot(self) -> dict[str, dict[str, float | int]]:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
            }

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()


hyperion = Hyperion()
