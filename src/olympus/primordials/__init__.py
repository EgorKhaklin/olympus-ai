"""Primordials — the first things that existed.

Before the Titans, before the Olympians, before order itself: Chaos
yawned. From Chaos came Gaia (Earth), Tartarus (the abyss), Nyx (Night),
Erebus (Darkness), and Eros (Generation).

These modules implement the lowest-level substrate primitives. Nothing
in Olympus runs without them. They are the ground beneath the ground.
"""

from olympus.primordials.chaos import Chaos, void
from olympus.primordials.gaia import Gaia, root
from olympus.primordials.nyx import Nyx, after_dark
from olympus.primordials.tartarus import Tartarus, quarantine
from olympus.primordials.eros import Eros, generate

__all__ = [
    "Chaos", "void",
    "Gaia", "root",
    "Nyx", "after_dark",
    "Tartarus", "quarantine",
    "Eros", "generate",
]
