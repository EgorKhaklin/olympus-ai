"""satyr_hearth — verifies Hestia's hearth is lit."""
from __future__ import annotations

from olympus.monsters.argos.satyrs.base import Satyr, Sighting
from olympus.olympians.hestia import hestia


class SatyrHearth(Satyr):
    NAME = "satyr_hearth"

    def look(self) -> Sighting:
        if hestia.is_lit():
            h = hestia.hearth()
            return Sighting(self.NAME, True, f"hearth lit as '{h.name}'")
        return Sighting(self.NAME, False, "hearth is dark")


satyr_hearth = SatyrHearth()
