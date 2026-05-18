"""Demeter — goddess of grain, harvest, and the cycle of seasons.

Demeter taught humans to farm. Her grief for Persephone brings winter.
In Olympus, Demeter is the ingestion primitive — collecting raw
observations from many sources, batching them into harvests for
downstream processing.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Harvest:
    """A batch of observations gathered together."""
    label: str
    started_at: float
    items: list[Any] = field(default_factory=list)

    def add(self, item: Any) -> None:
        self.items.append(item)

    @property
    def size(self) -> int:
        return len(self.items)

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self.started_at


class Demeter:
    """Batch-collecting ingestion. Each call to `gather()` accumulates
    items until the batch is yielded via `reap()`."""

    def __init__(self) -> None:
        self._current: dict[str, Harvest] = {}

    def gather(self, label: str, item: Any) -> Harvest:
        """Add an item to the current harvest under `label`."""
        h = self._current.get(label)
        if h is None:
            h = Harvest(label=label, started_at=time.monotonic())
            self._current[label] = h
        h.add(item)
        return h

    def reap(self, label: str) -> Harvest:
        """Take the current harvest under `label`; start a fresh one."""
        h = self._current.pop(label, Harvest(label=label, started_at=time.monotonic()))
        return h

    def harvests(self) -> dict[str, Harvest]:
        return dict(self._current)


demeter = Demeter()
