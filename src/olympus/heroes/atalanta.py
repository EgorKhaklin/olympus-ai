"""Atalanta — huntress who outran every suitor.

Atalanta was the fastest mortal of her age. She lost only because she
stopped to pick up golden apples. In Olympus, Atalanta is the
performance persona — she runs benchmarks against substrate
operations and reports timing percentiles via Artemis.

Akropolis arc: Atalanta gains a **scalability harness** —
`atalanta.scale(operation_name, build_state, run_op, sizes=...)`
runs `run_op` against synthetic state of each size, returns a
ScaleReport with p50/p95/p99 latency + memory delta. Each point is
persisted under `atalanta.scale-point` for trending.
"""
from __future__ import annotations

import gc
import time
from dataclasses import dataclass, field, asdict
from typing import Callable

from olympus.olympians.artemis import artemis


@dataclass
class ScalePoint:
    """One (size, runner) data point."""
    size: int
    iterations: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float
    max_ms: float
    memory_delta_kb: float = 0.0      # 0 if psutil unavailable
    error: str = ""


@dataclass
class ScaleReport:
    operation: str
    started_at: str
    ended_at: str = ""
    points: list[ScalePoint] = field(default_factory=list)


def _measure_memory_kb() -> float | None:
    """Current process RSS in KB, or None if psutil isn't installed."""
    try:
        import psutil  # type: ignore
        return psutil.Process().memory_info().rss / 1024.0
    except Exception:  # noqa: BLE001
        return None


def _percentile(samples: list[float], p: float) -> float:
    """p in [0,100]. Linear interpolation between sorted points."""
    if not samples:
        return 0.0
    sorted_s = sorted(samples)
    if p <= 0: return sorted_s[0]
    if p >= 100: return sorted_s[-1]
    k = (len(sorted_s) - 1) * (p / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(sorted_s) - 1)
    frac = k - lo
    return sorted_s[lo] * (1.0 - frac) + sorted_s[hi] * frac


class Atalanta:
    """Benchmark runner + scalability harness (akropolis arc)."""

    def race(self, name: str, fn: Callable[[], None],
              iterations: int = 100) -> dict[str, float]:
        """Run `fn` `iterations` times; record per-call duration in
        Artemis; return the percentile summary."""
        for _ in range(iterations):
            start = time.perf_counter()
            fn()
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            artemis.mark(f"atalanta.{name}", elapsed_ms)
        quiver = artemis.quiver(f"atalanta.{name}")
        return quiver.summary() if quiver else {}

    # ─────────────────────────────────────────────────────
    # Scalability harness
    # ─────────────────────────────────────────────────────

    def scale(self, operation_name: str,
               build_state: Callable[[int], object],
               run_op: Callable[[object], None],
               *,
               sizes: list[int] | None = None,
               iterations_per_size: int = 20,
               teardown: Callable[[object], None] | None = None,
               ) -> ScaleReport:
        """Measure how `run_op` scales as state size grows.

        `build_state(n)` builds a synthetic state of size n.
        `run_op(state)` runs the operation against that state.
        `teardown(state)` (optional) cleans up between sizes.

        For each size, runs `iterations_per_size` trials, records
        latency percentiles + memory delta. Each point persists to
        `atalanta.scale-point` for trending."""
        from olympus.primordials.nyx import Nyx
        from olympus.titans.mnemosyne import mnemosyne

        sizes = sizes if sizes is not None else [10, 100, 1000, 10000]
        report = ScaleReport(
            operation=operation_name,
            started_at=Nyx.now().isoformat(),
        )
        for n in sizes:
            point = ScalePoint(
                size=n, iterations=iterations_per_size,
                p50_ms=0.0, p95_ms=0.0, p99_ms=0.0,
                mean_ms=0.0, max_ms=0.0,
            )
            try:
                state = build_state(n)
                gc.collect()
                mem_before = _measure_memory_kb()
                samples: list[float] = []
                for _ in range(iterations_per_size):
                    s = time.perf_counter()
                    run_op(state)
                    samples.append((time.perf_counter() - s) * 1000.0)
                mem_after = _measure_memory_kb()
                if teardown is not None:
                    teardown(state)
                if mem_before is not None and mem_after is not None:
                    point.memory_delta_kb = mem_after - mem_before
                point.p50_ms = _percentile(samples, 50)
                point.p95_ms = _percentile(samples, 95)
                point.p99_ms = _percentile(samples, 99)
                point.mean_ms = (sum(samples) / len(samples)) \
                                if samples else 0.0
                point.max_ms = max(samples) if samples else 0.0
            except Exception as exc:  # noqa: BLE001
                point.error = f"{type(exc).__name__}: {exc}"
            report.points.append(point)

            mnemosyne.remember(
                kind="atalanta.scale-point",
                actor=f"atalanta:{operation_name}",
                summary=(f"scale-point {operation_name}@n={n}: "
                         f"p50={point.p50_ms:.2f}ms "
                         f"p95={point.p95_ms:.2f}ms "
                         f"p99={point.p99_ms:.2f}ms"
                         + (f" ERROR={point.error[:40]}"
                            if point.error else "")),
                operation=operation_name,
                **asdict(point),
            )

        report.ended_at = Nyx.now().isoformat()
        mnemosyne.remember(
            kind="atalanta.scale-report",
            actor=f"atalanta:{operation_name}",
            summary=(f"scale report for {operation_name}: "
                     f"{len(report.points)} sizes"),
            operation=operation_name,
            points=[asdict(p) for p in report.points],
        )
        return report


atalanta = Atalanta()
