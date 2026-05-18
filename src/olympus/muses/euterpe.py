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


euterpe = Euterpe()
