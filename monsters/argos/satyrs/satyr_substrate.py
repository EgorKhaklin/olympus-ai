"""satyr_substrate — verifies Rhea's required directories exist."""
from __future__ import annotations

from monsters.argos.satyrs.base import Satyr, Sighting
from titans.rhea import rhea
from primordials.gaia import root


class SatyrSubstrate(Satyr):
    NAME = "satyr_substrate"

    def look(self) -> Sighting:
        missing = [d for d in rhea.REQUIRED_DIRS if not root.child(d).is_dir()]
        if missing:
            return Sighting(self.NAME, False,
                f"{len(missing)} required dir(s) missing")
        return Sighting(self.NAME, True,
            f"all {len(rhea.REQUIRED_DIRS)} required dirs present")


satyr_substrate = SatyrSubstrate()
