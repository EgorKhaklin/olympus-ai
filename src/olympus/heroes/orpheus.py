"""Orpheus — poet who descended into Hades to recover Eurydice.

Orpheus charmed the underworld with his lyre. He was permitted to
lead Eurydice back — provided he did not look. He looked. In Olympus,
Orpheus is the log-retrieval persona: he descends into Hades's
archive and brings back specific shades. He may look (no curse
applies in code).
"""
from __future__ import annotations

from typing import Any

from olympus.underworld.hades import hades


class Orpheus:
    """Archive retrieval."""

    def descend_for(self, name: str) -> list[dict[str, Any]]:
        """Retrieve every shade archived under `name`."""
        return hades.ascend(name)

    def how_many(self) -> int:
        """Total shades in Hades."""
        return hades.population()


orpheus = Orpheus()
