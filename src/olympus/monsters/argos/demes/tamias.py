"""Tamias — the treasurer.

The tamias was the financial officer of the Greek polis. In Olympus,
Tamias reads Plutus's ledger and reports on resource accounting via
Lachesis (quotas)."""
from __future__ import annotations

from olympus.monsters.argos.demes.base import Deme, DemeFinding


class Tamias(Deme):
    NAME = "tamias"
    ROLE = "the treasurer"

    def observe(self) -> DemeFinding:
        from olympus.fates.lachesis import lachesis
        consumed = {name: lachesis.consumed(name) for name in lachesis._quotas}
        ceilings = {name: q.ceiling for name, q in lachesis._quotas.items()}
        if not lachesis._quotas:
            return DemeFinding(deme=self.NAME, role=self.ROLE,
                summary="no quotas registered with Lachesis")
        utilization = {
            name: f"{consumed[name]:.1f} / {ceilings[name]:.1f}"
            for name in lachesis._quotas
        }
        return DemeFinding(
            deme=self.NAME, role=self.ROLE,
            summary=f"{len(lachesis._quotas)} quota(s) under accounting",
            detail={"utilization": utilization},
        )


tamias = Tamias()
