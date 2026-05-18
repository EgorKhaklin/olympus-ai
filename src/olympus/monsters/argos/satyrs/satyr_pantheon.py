"""satyr_pantheon — verifies the cosmogonic tier directories all
contain at least one module."""
from __future__ import annotations

from olympus.monsters.argos.satyrs.base import Satyr, Sighting
from olympus.primordials.gaia import root


TIERS = ("primordials", "titans", "olympians", "underworld",
         "fates", "furies", "graces", "muses", "heroes", "monsters")


class SatyrPantheon(Satyr):
    NAME = "satyr_pantheon"

    def look(self) -> Sighting:
        empty: list[str] = []
        for tier in TIERS:
            path = root.child("src", "olympus", tier)
            modules = [f for f in path.rglob("*.py")
                       if not f.name.startswith("_")]
            if not modules:
                empty.append(tier)
        if empty:
            return Sighting(self.NAME, False,
                f"empty tier(s): {', '.join(empty)}")
        return Sighting(self.NAME, True,
            f"all {len(TIERS)} cosmogonic tiers populated")


satyr_pantheon = SatyrPantheon()
