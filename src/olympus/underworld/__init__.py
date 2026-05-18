"""The Underworld — Hades's realm, beneath the earth.

Below Gaia, beneath the roots of mountains, Hades rules the dead.
Persephone is his queen, six months above and six below. Hecate
keeps the crossroads. The rivers Styx and Lethe encircle the realm:
the first carries unbreakable oaths, the second carries forgetting.

In Olympus, the underworld holds what is no longer active but is not
forgotten. Archive, deletion ceremonies, error recovery, and the
oath ledger all live here.
"""

from olympus.underworld.hades import Hades, descend, ascend
from olympus.underworld.persephone import Persephone, cycle
from olympus.underworld.hecate import Hecate, at_crossroads
from olympus.underworld.styx import Styx, swear, oath_of
from olympus.underworld.lethe import Lethe, forget, remembered

__all__ = [
    "Hades", "descend", "ascend",
    "Persephone", "cycle",
    "Hecate", "at_crossroads",
    "Styx", "swear", "oath_of",
    "Lethe", "forget", "remembered",
]
