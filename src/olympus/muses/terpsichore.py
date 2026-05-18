"""Terpsichore — Muse of dance.

Terpsichore choreographs movement: which step follows which, what
falls on the beat. In Olympus she manages cron-like choreography:
the schedule of which Olympian or Titan should run at which Cadence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from olympus.titans.cronus import cronus, Cadence


@dataclass
class Step:
    """A choreographed step — what to do, on which beat."""
    name: str
    cadence: Cadence
    fn: Callable[[], None]


class Terpsichore:
    """Choreography registry."""

    def __init__(self) -> None:
        self._steps: dict[str, Step] = {}

    def choreograph(self, name: str, cadence_name: str,
                    fn: Callable[[], None]) -> Step:
        """Register `fn` to run on the `cadence_name` beat."""
        cad = cronus.cadence(cadence_name)
        if cad is None:
            raise ValueError(f"unknown cadence: {cadence_name!r}")
        step = Step(name=name, cadence=cad, fn=fn)
        self._steps[name] = step
        return step

    def dance(self) -> list[Step]:
        """Return all registered steps. The caller is responsible for
        actually invoking them on the beat (e.g., via cron or Nyx)."""
        return list(self._steps.values())


terpsichore = Terpsichore()
