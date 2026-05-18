"""Pythagoras — mathematician of Samos, father of sacred numerics.

In history: 6th-century-BCE thinker whose school treated number as
the foundation of reality. He formalized the proportional
relationships that became the golden ratio (then called the "section
in extreme and mean ratio"). The Pythagorean theorem and the
Pythagorean triples bear his name.

In Olympus, Pythagoras is the **sacred-numerics module**. He exposes:

  - canonical mathematical constants (φ, π, √2, e, ...)
  - Fibonacci sequence + Fibonacci-scaled backoff timing
  - golden-section search (unimodal optimization in O(log n))
  - harmony scoring (proximity of a ratio to φ, 1/φ, or 1)
  - Pythagorean-triple generator

He records every `golden_section_search` invocation to Mnemosyne under
`pythagoras.search`, so the optimization history is reconstructable
(S8). Constants and pure-math helpers are read-only and recorded only
when used through the search/backoff entry points.

Per Delphi 2026-05-18-phi-arc.md.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Callable, Iterator

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


# ─────────────────────────────────────────────────────────
# Sacred constants — the canonical values other modules may import.
# These are evaluated once; modules use them via attribute reference,
# never recompute.
# ─────────────────────────────────────────────────────────


#: The golden ratio φ = (1 + √5) / 2 ≈ 1.6180339887...
PHI: float = (1.0 + math.sqrt(5.0)) / 2.0

#: 1/φ = φ − 1 ≈ 0.6180339887... (the smaller golden-ratio reciprocal)
PHI_INVERSE: float = 1.0 / PHI

#: π ≈ 3.14159...
PI: float = math.pi

#: e ≈ 2.71828...
E: float = math.e

#: √2 ≈ 1.41421...
SQRT2: float = math.sqrt(2.0)

#: √3 ≈ 1.73205...
SQRT3: float = math.sqrt(3.0)

#: √5 ≈ 2.23606...
SQRT5: float = math.sqrt(5.0)


# ─────────────────────────────────────────────────────────
# Fibonacci sequence + Fibonacci-scaled backoff
# ─────────────────────────────────────────────────────────


def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number (0-indexed; F(0)=0, F(1)=1)."""
    if n < 0:
        raise ValueError("fibonacci index must be non-negative")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def fib_sequence(k: int) -> list[int]:
    """Return the first k Fibonacci numbers, starting from F(0)=0."""
    if k <= 0:
        return []
    out: list[int] = []
    a, b = 0, 1
    for _ in range(k):
        out.append(a)
        a, b = b, a + b
    return out


def fib_backoff(attempt: int, *,
                base_seconds: float = 1.0,
                cap_seconds: float = 300.0,
                jitter: float = 0.0) -> float:
    """Fibonacci-scaled retry delay.

    The ratio between successive Fibonacci numbers approaches φ
    (≈ 1.618), giving a smoother growth curve than exponential
    backoff's 2.0 ratio. Same fairness properties under load.

    attempt 0 → base_seconds × F(1) = base
    attempt 1 → base × F(2) = base × 1
    attempt n → base × F(n+1), capped at cap_seconds.
    """
    if attempt < 0:
        raise ValueError("attempt must be non-negative")
    delay = base_seconds * fibonacci(attempt + 1)
    delay = min(delay, cap_seconds)
    if jitter > 0:
        # Deterministic-ish jitter via attempt index; no random module
        # to keep tests fully reproducible.
        delay += (attempt % 7) / 7.0 * jitter
    return delay


# ─────────────────────────────────────────────────────────
# Golden-section search — unimodal optimization
# ─────────────────────────────────────────────────────────


@dataclass
class SearchTrace:
    """One golden-section search invocation recorded."""
    name: str
    lo: float
    hi: float
    tol: float
    iterations: int = 0
    best_x: float = 0.0
    best_f: float = 0.0
    direction: str = "minimize"
    history: list[tuple[float, float]] = field(default_factory=list)


def golden_section_search(
    fn: Callable[[float], float],
    lo: float, hi: float, *,
    tol: float = 1e-5,
    max_iter: int = 200,
    minimize: bool = True,
    name: str = "anonymous",
    record: bool = True,
) -> tuple[float, float]:
    """Find the extremum of a unimodal `fn(x)` in [lo, hi].

    By default, minimizes. Set `minimize=False` to maximize (we
    internally negate). Returns (best_x, best_f).

    The algorithm narrows the bracket using the golden ratio at each
    step; convergence is geometric with ratio 1/φ ≈ 0.618 per call.

    Records the trace to Mnemosyne if `record=True` (S8: optimization
    decisions are reconstructable from substrate records alone).
    """
    if lo >= hi:
        raise ValueError(f"lo ({lo}) must be < hi ({hi})")
    if tol <= 0:
        raise ValueError("tol must be > 0")

    sign = 1.0 if minimize else -1.0
    a, b = float(lo), float(hi)

    # Interior points at golden-ratio offsets
    c = b - (b - a) / PHI
    d = a + (b - a) / PHI
    fc = sign * fn(c)
    fd = sign * fn(d)

    trace = SearchTrace(
        name=name, lo=lo, hi=hi, tol=tol,
        direction="minimize" if minimize else "maximize",
    )

    for i in range(max_iter):
        if abs(b - a) < tol:
            break
        if fc < fd:
            b = d
            d = c
            fd = fc
            c = b - (b - a) / PHI
            fc = sign * fn(c)
        else:
            a = c
            c = d
            fc = fd
            d = a + (b - a) / PHI
            fd = sign * fn(d)
        trace.iterations = i + 1
        if i < 20:
            # Cap history depth to keep records small.
            trace.history.append((float(c if fc < fd else d),
                                  float(sign * min(fc, fd))))

    best_x = (a + b) / 2.0
    best_f = fn(best_x)
    trace.best_x = best_x
    trace.best_f = best_f

    if record:
        mnemosyne.remember(
            kind="pythagoras.search",
            actor="pythagoras",
            summary=(f"golden-section {trace.direction} of {name!r} "
                     f"in [{lo:.4g}, {hi:.4g}] → "
                     f"x≈{best_x:.6g}, f≈{best_f:.6g} "
                     f"({trace.iterations} iter)"),
            **asdict(trace),
        )
    return best_x, best_f


# ─────────────────────────────────────────────────────────
# Harmony — score a ratio against φ, 1/φ, 1
# ─────────────────────────────────────────────────────────


_HARMONIC_ANCHORS: tuple[tuple[str, float], ...] = (
    ("phi", PHI),
    ("inverse_phi", PHI_INVERSE),
    ("unity", 1.0),
    ("two", 2.0),
)


@dataclass
class HarmonyScore:
    """One harmony evaluation."""
    ratio: float
    nearest_anchor: str
    nearest_value: float
    distance: float
    score: float          # 1.0 = exactly on anchor; 0.0 = far away


def harmony(ratio: float) -> HarmonyScore:
    """Score a ratio against the harmonic anchors (φ, 1/φ, 1, 2).

    Returns a HarmonyScore with the nearest anchor and a 0..1 score.
    The score is exp(-distance) so that "close to φ" gives near 1.0
    and "far from any anchor" tends toward 0.0.
    """
    if not isinstance(ratio, (int, float)) or math.isnan(ratio) \
       or math.isinf(ratio):
        return HarmonyScore(ratio=float("nan"), nearest_anchor="undefined",
                            nearest_value=float("nan"),
                            distance=float("inf"), score=0.0)
    best_name = ""
    best_value = 0.0
    best_distance = float("inf")
    for name, value in _HARMONIC_ANCHORS:
        d = abs(ratio - value)
        if d < best_distance:
            best_name = name
            best_value = value
            best_distance = d
    score = math.exp(-best_distance)
    return HarmonyScore(
        ratio=float(ratio),
        nearest_anchor=best_name,
        nearest_value=best_value,
        distance=best_distance,
        score=score,
    )


# ─────────────────────────────────────────────────────────
# Pythagorean triples — (a, b, c) with a² + b² = c²
# ─────────────────────────────────────────────────────────


def pythagorean_triples(below: int) -> Iterator[tuple[int, int, int]]:
    """Yield all primitive Pythagorean triples (a, b, c) with c < below.

    Generated via Euclid's formula:
        a = m² − n², b = 2mn, c = m² + n²
    for coprime m > n > 0 with m − n odd.

    Yields each triple in (smaller leg, larger leg, hypotenuse) order.
    """
    if below <= 0:
        return
    import math as _math
    m = 2
    while True:
        for n in range(1, m):
            if (m - n) % 2 == 0:
                continue
            if _math.gcd(m, n) != 1:
                continue
            a = m * m - n * n
            b = 2 * m * n
            c = m * m + n * n
            if c >= below:
                continue
            leg_small = min(a, b)
            leg_large = max(a, b)
            yield (leg_small, leg_large, c)
        # Stop when even the smallest possible c at this m exceeds below
        if m * m + 1 >= below:
            return
        m += 1


# ─────────────────────────────────────────────────────────
# Pythagoras as a small class — for callers that want a singleton
# ─────────────────────────────────────────────────────────


class Pythagoras:
    """The numerics-of-Olympus interface. Module functions are the
    primary surface; this class exposes them on a singleton named
    `pythagoras` for symmetry with the rest of the pantheon."""

    PHI = PHI
    PHI_INVERSE = PHI_INVERSE
    PI = PI
    E = E
    SQRT2 = SQRT2
    SQRT3 = SQRT3
    SQRT5 = SQRT5

    fibonacci = staticmethod(fibonacci)
    fib_sequence = staticmethod(fib_sequence)
    fib_backoff = staticmethod(fib_backoff)
    golden_section_search = staticmethod(golden_section_search)
    harmony = staticmethod(harmony)
    pythagorean_triples = staticmethod(pythagorean_triples)


pythagoras = Pythagoras()
