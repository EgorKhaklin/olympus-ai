"""HYDRA — the many-headed beast of Lerna.

Eight mortal heads, one immortal. The immortal head can be crushed
beneath a rock but cannot be killed. The mortal heads, cut, do not
regrow — they are replaced by new heads with new shapes covering
the same slice.

In Olympus, HYDRA is the watcher tier: read-only observers, one per
slice of the substrate. The heads are deliberate, named, and limited.
"""

from monsters.hydra.host import Hydra, hydra
from monsters.hydra.head import Head, HeadFinding, Severity

__all__ = ["Hydra", "hydra", "Head", "HeadFinding", "Severity"]
