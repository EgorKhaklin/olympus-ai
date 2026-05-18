"""Iapetus — titan of mortality, father of Prometheus and Epimetheus.

Iapetus fathered the line that included Prometheus (forethought),
Epimetheus (afterthought), Atlas (the bearer), and Menoetius (the
violent). His descendants brought mortality into the human story.
In Olympus, Iapetus governs the lifecycle of components — when they
end, and how their endings are handled.

Atropos (one of the Fates) cuts the thread; Iapetus is the wider
philosophy: every component will end. Plan for it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class LifecyclePhase(Enum):
    UNBORN = "unborn"        # not yet instantiated
    NASCENT = "nascent"      # bootstrap in progress
    ACTIVE = "active"        # in service
    QUIESCING = "quiescing"  # winding down (still serving)
    DORMANT = "dormant"      # not serving, recoverable
    ENDED = "ended"          # final state


@dataclass
class Lifecycle:
    """A component's lifecycle state machine."""
    component: str
    phase: LifecyclePhase = LifecyclePhase.UNBORN
    on_end: Callable[[], None] | None = None

    def advance_to(self, phase: LifecyclePhase) -> None:
        """Move forward in the lifecycle. Refuses regressions."""
        order = [
            LifecyclePhase.UNBORN, LifecyclePhase.NASCENT, LifecyclePhase.ACTIVE,
            LifecyclePhase.QUIESCING, LifecyclePhase.DORMANT, LifecyclePhase.ENDED,
        ]
        if order.index(phase) < order.index(self.phase):
            raise ValueError(
                f"{self.component}: cannot move backward "
                f"({self.phase.value} → {phase.value})"
            )
        self.phase = phase
        if phase == LifecyclePhase.ENDED and self.on_end:
            self.on_end()


class Iapetus:
    """Lifecycle registry."""

    def __init__(self) -> None:
        self._lifecycles: dict[str, Lifecycle] = {}

    def register(self, component: str, on_end: Callable[[], None] | None = None) -> Lifecycle:
        lc = Lifecycle(component=component, on_end=on_end)
        self._lifecycles[component] = lc
        return lc

    def of(self, component: str) -> Lifecycle | None:
        return self._lifecycles.get(component)

    def by_phase(self, phase: LifecyclePhase) -> list[Lifecycle]:
        return [lc for lc in self._lifecycles.values() if lc.phase == phase]


iapetus = Iapetus()
