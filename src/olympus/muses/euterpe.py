"""Euterpe — Muse of music, the rhythm of recurrent things.

Euterpe governs musical rhythm. In Olympus she registers and reads
*pheromone rhythms*: how often each Argos Eye / HYDRA Head /
Phalanx deposits findings into the substrate.

Where Cronus tracks calendar cadences, Euterpe tracks *observed*
rhythms — measured, not declared.
"""
from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass

from olympus.primordials.nyx import Nyx


@dataclass
class Rhythm:
    source: str
    intervals: list[float]   # seconds between successive emissions

    @property
    def beats(self) -> int:
        return len(self.intervals) + 1  # n intervals → n+1 beats

    @property
    def median_interval(self) -> float:
        return statistics.median(self.intervals) if self.intervals else float("nan")

    @property
    def jitter(self) -> float:
        """stdev of intervals — high jitter means irregular rhythm."""
        return statistics.stdev(self.intervals) if len(self.intervals) > 1 else 0.0


class Euterpe:
    """Per-source rhythm recorder."""

    def __init__(self) -> None:
        self._last: dict[str, float] = {}
        self._rhythms: dict[str, Rhythm] = {}

    def beat(self, source: str) -> None:
        """Note a beat from `source` (one emission)."""
        now_s = Nyx.now().timestamp()
        last = self._last.get(source)
        if last is not None:
            rhythm = self._rhythms.get(source) or Rhythm(source=source, intervals=[])
            rhythm.intervals.append(now_s - last)
            self._rhythms[source] = rhythm
        self._last[source] = now_s

    def rhythm(self, source: str) -> Rhythm | None:
        return self._rhythms.get(source)

    def all_rhythms(self) -> list[Rhythm]:
        return list(self._rhythms.values())

    # ─────────────────────────────────────────────────────────
    # Musical consonance (aegis arc) — Pythagoras discovered that
    # consonant intervals correspond to simple integer ratios.
    # Where Pythagoras's harmony() scores against φ, 1/φ, 1, 2,
    # Euterpe scores against the musical intervals.
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def intervals() -> list[tuple[str, float]]:
        """The canonical consonant intervals (name, ratio)."""
        return [
            ("unison",         1.0),
            ("octave",         2.0),
            ("perfect_fifth",  3.0 / 2.0),
            ("perfect_fourth", 4.0 / 3.0),
            ("major_third",    5.0 / 4.0),
            ("minor_third",    6.0 / 5.0),
            ("major_sixth",    5.0 / 3.0),
            ("minor_sixth",    8.0 / 5.0),
            ("major_second",   9.0 / 8.0),
        ]

    def consonance(self, ratio: float) -> "Consonance":
        """Score a ratio against the consonant musical intervals.
        Octave-invariant — folds the ratio into [1, 2) before
        comparing, since musical consonance is perceptually
        octave-equivalent."""
        import math as _math
        if not isinstance(ratio, (int, float)) or \
           _math.isnan(ratio) or _math.isinf(ratio):
            return Consonance(ratio=float("nan"),
                              nearest_interval="undefined",
                              nearest_ratio=float("nan"),
                              distance=float("inf"),
                              score=0.0,
                              consonance_class="dissonant")
        r = abs(float(ratio))
        if r <= 0:
            return Consonance(ratio=ratio,
                              nearest_interval="undefined",
                              nearest_ratio=float("nan"),
                              distance=float("inf"),
                              score=0.0,
                              consonance_class="dissonant")
        # Fold into [1, 2) — octave-equivalence
        while r >= 2.0:
            r /= 2.0
        while r < 1.0:
            r *= 2.0
        best_name = ""
        best_value = 0.0
        best_distance = float("inf")
        for name, value in self.intervals():
            normed = value
            while normed >= 2.0:
                normed /= 2.0
            while normed < 1.0:
                normed *= 2.0
            d = abs(r - normed)
            if d < best_distance:
                best_name = name
                best_value = normed
                best_distance = d
        score = _math.exp(-12.0 * best_distance)
        cls = ("perfect" if score > 0.9 else
               "consonant" if score > 0.5 else
               "dissonant")
        return Consonance(
            ratio=float(ratio),
            nearest_interval=best_name,
            nearest_ratio=best_value,
            distance=best_distance,
            score=score,
            consonance_class=cls,
        )


@dataclass
class Consonance:
    """One musical-interval evaluation."""
    ratio: float
    nearest_interval: str
    nearest_ratio: float
    distance: float
    score: float                  # 0..1; 1.0 = on the interval exactly
    consonance_class: str         # 'perfect' | 'consonant' | 'dissonant'


euterpe = Euterpe()
