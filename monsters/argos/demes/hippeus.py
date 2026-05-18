"""Hippeus — the cavalry knight.

The hippeus was the cavalry-class citizen of the Greek polis, the
fast-moving observer. In Olympus, Hippeus correlates recent
findings across multiple Eyes — looking for the same slice surfacing
in many places at once."""
from __future__ import annotations

from collections import Counter

from monsters.argos.demes.base import Deme, DemeFinding


class Hippeus(Deme):
    NAME = "hippeus"
    ROLE = "the cavalry — fast correlator"

    def observe(self) -> DemeFinding:
        from monsters.argos.colony import colony
        phers = colony.read_log()
        if not phers:
            return DemeFinding(deme=self.NAME, role=self.ROLE,
                summary="no recent activity to correlate")
        slice_count = Counter(p.slice for p in phers)
        correlated = [(s, n) for s, n in slice_count.items() if n >= 2]
        if not correlated:
            return DemeFinding(deme=self.NAME, role=self.ROLE,
                summary="no cross-eye correlations yet")
        top = sorted(correlated, key=lambda x: -x[1])[:3]
        return DemeFinding(
            deme=self.NAME, role=self.ROLE,
            summary=f"{len(correlated)} slice(s) seen by multiple eyes; top: {top}",
            detail={"correlations": top},
        )


hippeus = Hippeus()
