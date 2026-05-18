"""Lachesis — the Allotter, second of the three Fates.

Lachesis measures the thread Clotho spins, determining how long it will
be. In Olympus she is the resource-accounting primitive: she records
how much of a quota each component has been allotted, and refuses
overdraws.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class Quota:
    """A named allotment with a ceiling."""
    name: str
    ceiling: float
    units: str = "units"


class Lachesis:
    """Per-quota accounting."""

    def __init__(self) -> None:
        self._quotas: dict[str, Quota] = {}
        self._consumed: dict[str, float] = defaultdict(float)

    def allot(self, q: Quota) -> Quota:
        """Register a quota."""
        self._quotas[q.name] = q
        return q

    def measure(self, name: str, amount: float) -> bool:
        """Charge `amount` against the quota named `name`.
        Returns True iff the charge fits under the ceiling.
        Returns False if it would exceed — and does NOT charge."""
        q = self._quotas.get(name)
        if q is None:
            raise KeyError(f"lachesis: no quota named {name!r}")
        if self._consumed[name] + amount > q.ceiling:
            return False
        self._consumed[name] += amount
        return True

    def consumed(self, name: str) -> float:
        return self._consumed[name]

    def remaining(self, name: str) -> float:
        q = self._quotas[name]
        return max(0.0, q.ceiling - self._consumed[name])

    def reset(self, name: str) -> None:
        self._consumed[name] = 0.0


lachesis = Lachesis()
measure = lachesis.measure
