"""Mantis — the seer.

The mantis (μάντις) was the Greek prophet who read patterns in signs.
In Olympus, Mantis surveys recent pheromone deposits and surfaces the
strongest pattern."""
from __future__ import annotations

from collections import Counter

from olympus.monsters.argos.demes.base import Deme, DemeFinding


class Mantis(Deme):
    NAME = "mantis"
    ROLE = "the seer"

    def observe(self) -> DemeFinding:
        from olympus.monsters.argos.colony import colony
        phers = colony.read_log()
        if not phers:
            return DemeFinding(deme=self.NAME, role=self.ROLE,
                summary="no pheromones yet to read")
        kinds = Counter(p.kind for p in phers)
        eyes = Counter(p.eye for p in phers)
        dominant_kind = kinds.most_common(1)[0]
        most_active = eyes.most_common(1)[0]
        return DemeFinding(
            deme=self.NAME, role=self.ROLE,
            summary=(f"of {len(phers)} pheromone(s), {dominant_kind[0]} "
                     f"dominates ({dominant_kind[1]}); most active eye is "
                     f"{most_active[0]} ({most_active[1]})"),
            detail={"by_kind": dict(kinds), "by_eye": dict(eyes)},
        )


mantis = Mantis()
