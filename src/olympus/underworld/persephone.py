"""Persephone — queen of the underworld, half the year above and half below.

Demeter's daughter, abducted by Hades, ate six pomegranate seeds and
was bound to spend six months each year beneath the earth. Her ascent
brings spring; her descent, winter. Olympus's Persephone models
cyclical state: things that alternate between active (Olympus) and
quiescent (underworld) on a schedule.

Use Persephone for token-rotation, session cycles, anything that
periodically descends and ascends.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Callable


@dataclass
class Cycle:
    """A Persephone cycle. `above_months` time above; `below_months`
    time below. Total period must be ≤ 12."""
    name: str
    above_months: int = 6
    below_months: int = 6
    anchor: datetime.date = datetime.date(2026, 3, 21)  # vernal equinox

    def __post_init__(self) -> None:
        if self.above_months + self.below_months > 12:
            raise ValueError(
                f"Cycle {self.name!r}: above+below must be ≤12 months"
            )

    def state_at(self, when: datetime.date | None = None) -> str:
        """Returns 'above' or 'below' depending on when (defaults to today)."""
        if when is None:
            when = datetime.date.today()
        days_since = (when - self.anchor).days
        period_days = (self.above_months + self.below_months) * 30
        if period_days == 0:
            return "above"
        phase = days_since % period_days
        above_days = self.above_months * 30
        return "above" if phase < above_days else "below"

    def is_above(self, when: datetime.date | None = None) -> bool:
        return self.state_at(when) == "above"


class Persephone:
    """Registry of cyclical-state things."""

    def __init__(self) -> None:
        self._cycles: dict[str, Cycle] = {}
        self._callbacks: dict[str, list[Callable[[str], None]]] = {}

    def cycle(self, c: Cycle) -> Cycle:
        """Register a cycle; returns the registered cycle."""
        self._cycles[c.name] = c
        return c

    def get(self, name: str) -> Cycle | None:
        return self._cycles.get(name)

    def all_cycles(self) -> list[Cycle]:
        return list(self._cycles.values())


persephone = Persephone()
cycle = persephone.cycle
