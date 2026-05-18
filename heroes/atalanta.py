"""Atalanta — huntress who outran every suitor.

Atalanta was the fastest mortal of her age. She lost only because she
stopped to pick up golden apples. In Olympus, Atalanta is the
performance persona — she runs benchmarks against substrate operations
and reports timing percentiles via Artemis.
"""
from __future__ import annotations

import time
from typing import Callable

from olympians.artemis import artemis


class Atalanta:
    """Benchmark runner."""

    def race(self, name: str, fn: Callable[[], None], iterations: int = 100) -> dict[str, float]:
        """Run `fn` `iterations` times; record per-call duration in Artemis;
        return the percentile summary."""
        for _ in range(iterations):
            start = time.perf_counter()
            fn()
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            artemis.mark(f"atalanta.{name}", elapsed_ms)
        quiver = artemis.quiver(f"atalanta.{name}")
        return quiver.summary() if quiver else {}


atalanta = Atalanta()
