"""Demes — the civic tier of Argos's swarm.

Where Eyes watch slices and Satyrs handle concrete checks, Demes
represent the Greek polis as a sociological model: each Deme is a
named civic role with its own observation domain.

  Mantis        the seer                — pattern surfacing
  Demarchos     the deme-leader         — registry roll-keeper
  Hippeus       the cavalry knight      — fast-correlation
  Demos         the people              — public-forum activity
  Tamias        the treasurer           — Plutus's ledger
  Ephoros       the overseer            — protocol-compliance checker
"""

from monsters.argos.demes.base import Deme, DemeFinding
from monsters.argos.demes.mantis import mantis
from monsters.argos.demes.demarchos import demarchos
from monsters.argos.demes.hippeus import hippeus
from monsters.argos.demes.demos import demos
from monsters.argos.demes.tamias import tamias
from monsters.argos.demes.ephoros import ephoros

ALL_DEMES = (mantis, demarchos, hippeus, demos, tamias, ephoros)

__all__ = [
    "Deme", "DemeFinding", "ALL_DEMES",
    "mantis", "demarchos", "hippeus", "demos", "tamias", "ephoros",
]
