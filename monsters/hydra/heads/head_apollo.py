"""head_apollo — watches Apollo's predicate coverage.

Apollo predicts via falsifiable predicates. If the count drops, or
the acceptance rate falls below the empirical threshold, this head
surfaces it. The S5 substrate invariant says every Apollo prediction
must carry a verify() callable.
"""
from __future__ import annotations

from monsters.hydra.head import Head, HeadFinding, Severity
from olympians.apollo import apollo


class HeadApollo(Head):
    NAME = "apollo"
    SLICE = "olympians/apollo (predicate coverage)"
    IMMORTAL = False

    def observe(self) -> list[HeadFinding]:
        predicates = apollo.predictions()
        if not predicates:
            return [self._finding(
                self.SLICE, Severity.INFO,
                "no Apollo predicates registered yet",
            )]
        unverifiable = [p for p in predicates if p.verify is None]
        if unverifiable:
            return [self._finding(
                self.SLICE, Severity.ALERT,
                f"{len(unverifiable)} predicate(s) lack verify() — S5 violation",
                names=[p.name for p in unverifiable],
            )]
        return [self._finding(
            self.SLICE, Severity.INFO,
            f"{len(predicates)} falsifiable predicate(s) registered",
        )]
