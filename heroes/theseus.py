"""Theseus — hero who navigated the labyrinth with Ariadne's thread.

Theseus entered the Cretan labyrinth to slay the Minotaur. Ariadne
gave him a thread to retrace his steps. In Olympus, Theseus is the
navigation persona — he can enter the brain-map (a structural
labyrinth) and report back what's there, never losing his way.
"""
from __future__ import annotations

import pathlib

from primordials.gaia import root
from muses.urania import urania


class Theseus:
    """Navigator. Reads Urania's chart; follows ariadne-thread back
    to summarize any subgraph."""

    def explore(self, tier: str) -> list[str]:
        """List every module in `tier`, with full relative path."""
        path = root.child(tier)
        if not path.exists():
            return []
        return [
            f.relative_to(root.root).as_posix()
            for f in sorted(path.rglob("*.py"))
            if not f.name.startswith("_")
        ]

    def labyrinth_size(self) -> int:
        """Total number of modules across all mythological tiers."""
        return sum(len(c.members) for c in urania.chart())


theseus = Theseus()
