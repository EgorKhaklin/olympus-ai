"""The Moirai — the three Fates, weavers of every life.

Clotho spins the thread, Lachesis measures it, Atropos cuts it.
The Fates were older than the Olympians; not even Zeus could overrule
them. In Olympus they are the lifecycle primitives:

  Clotho     creates    — spin a new component / id / record
  Lachesis   measures   — quota, allocation, resource accounting
  Atropos    cuts       — graceful termination, hard deletion

Every component's life passes through their hands.
"""

from olympus.fates.clotho import clotho, spin
from olympus.fates.lachesis import lachesis, measure
from olympus.fates.atropos import atropos, cut

__all__ = ["clotho", "spin", "lachesis", "measure", "atropos", "cut"]
