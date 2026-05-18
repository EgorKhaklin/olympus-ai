"""Artemis — huntress, twin sister of Apollo, goddess of the moon.

Artemis hunts what others cannot see, with arrows that never miss her
mark. In Olympus, Artemis is the precision-metrics primitive: she
tracks specific, named numbers over time and emits a percentile breakdown
on demand.

Where Apollo deals in falsifiable predictions, Artemis deals in
measured reality.
"""
from __future__ import annotations

import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Sequence


@dataclass
class Quiver:
    """A single named metric's recent arrows (samples)."""
    name: str
    samples: deque  # bounded
    capacity: int

    def loose(self, value: float) -> None:
        self.samples.append(value)

    @property
    def count(self) -> int:
        return len(self.samples)

    def percentile(self, p: float) -> float:
        """p in [0, 100]."""
        if not self.samples:
            return float("nan")
        sorted_samples = sorted(self.samples)
        if p <= 0:
            return sorted_samples[0]
        if p >= 100:
            return sorted_samples[-1]
        idx = (p / 100) * (len(sorted_samples) - 1)
        lo, hi = math.floor(idx), math.ceil(idx)
        if lo == hi:
            return sorted_samples[lo]
        frac = idx - lo
        return sorted_samples[lo] * (1 - frac) + sorted_samples[hi] * frac

    def summary(self) -> dict[str, float]:
        return {
            "count": self.count,
            "p50": self.percentile(50),
            "p95": self.percentile(95),
            "p99": self.percentile(99),
            "max": self.percentile(100),
        }


class Artemis:
    """Precision-metrics tracker. One quiver per named metric."""

    def __init__(self, capacity: int = 1024) -> None:
        self._quivers: dict[str, Quiver] = {}
        self._lock = threading.Lock()
        self.capacity = capacity

    def mark(self, name: str, value: float) -> None:
        """Record `value` against the named metric."""
        with self._lock:
            q = self._quivers.get(name)
            if q is None:
                q = Quiver(name, deque(maxlen=self.capacity), self.capacity)
                self._quivers[name] = q
            q.loose(value)

    def quiver(self, name: str) -> Quiver | None:
        with self._lock:
            return self._quivers.get(name)

    def all_summaries(self) -> dict[str, dict[str, float]]:
        with self._lock:
            return {name: q.summary() for name, q in self._quivers.items()}


artemis = Artemis()
