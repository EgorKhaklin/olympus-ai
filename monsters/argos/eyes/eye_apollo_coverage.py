"""eye_apollo_coverage — how many Apollo predicates are registered, and
how many carry verify() callables (S5 invariant)."""
from __future__ import annotations

from monsters.argos.base import Eye, EyeFinding, KIND_INFO, KIND_ALERT
from olympians.apollo import apollo


class EyeApolloCoverage(Eye):
    NAME = "eye_apollo_coverage"
    SLICE = "olympians/apollo (predicates)"

    def scan(self) -> list[EyeFinding]:
        preds = apollo.predictions()
        if not preds:
            return [self._finding(KIND_INFO, "no Apollo predicates yet")]
        unverifiable = [p.name for p in preds if p.verify is None]
        if unverifiable:
            return [self._finding(KIND_ALERT,
                f"S5 violation — {len(unverifiable)} predicate(s) lack verify()",
                intensity=10.0, names=unverifiable)]
        return [self._finding(KIND_INFO,
            f"{len(preds)} predicate(s); all carry verify()")]
