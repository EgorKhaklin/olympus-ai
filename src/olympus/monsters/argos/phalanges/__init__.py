"""Phalanges — battle formations grouping Eyes by concern.

In Greek warfare, the phalanx was a tight infantry formation in which
hoplites locked shields and advanced as one. Each phalanx in Olympus
groups Eyes that scan the same concern, advancing as one.

Four phalanges by default:

  Constitutional   — eyes that watch the substrate's own laws
  Substrate        — eyes that watch the filesystem layout
  Cadence          — eyes that watch rhythms of operation
  Oracular         — eyes that watch Apollo + Delphi surfaces
"""

from olympus.monsters.argos.phalanges.base import Phalanx
from olympus.monsters.argos.phalanges.phalanx_constitutional import phalanx_constitutional
from olympus.monsters.argos.phalanges.phalanx_substrate import phalanx_substrate
from olympus.monsters.argos.phalanges.phalanx_cadence import phalanx_cadence
from olympus.monsters.argos.phalanges.phalanx_oracular import phalanx_oracular

ALL_PHALANGES = (phalanx_constitutional, phalanx_substrate,
                 phalanx_cadence, phalanx_oracular)

__all__ = ["Phalanx", "ALL_PHALANGES",
           "phalanx_constitutional", "phalanx_substrate",
           "phalanx_cadence", "phalanx_oracular"]
