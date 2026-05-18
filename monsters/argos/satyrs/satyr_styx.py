"""satyr_styx — quick check on the oath chain."""
from __future__ import annotations

from monsters.argos.satyrs.base import Satyr, Sighting
from underworld.styx import styx


class SatyrStyx(Satyr):
    NAME = "satyr_styx"

    def look(self) -> Sighting:
        intact, bad_seq = styx.verify()
        if not intact:
            return Sighting(self.NAME, False,
                f"styx tampered at seq={bad_seq}")
        return Sighting(self.NAME, True,
            f"styx intact ({len(styx._read_all())} oath(s))")


satyr_styx = SatyrStyx()
