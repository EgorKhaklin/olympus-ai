"""Urania — Muse of astronomy, the celestial chart.

Urania reads the stars. In Olympus she renders the brain-map — the
celestial chart of the pantheon, showing every named component and
its relationships. The brain-map is the system's own astronomy:
where each god / monster / hero lives, and what they touch.
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass

from olympus.primordials.gaia import root


@dataclass
class Constellation:
    """A grouping of related modules."""
    tier: str               # primordials / titans / olympians / etc.
    members: list[str]


class Urania:
    """Brain-map generator. Returns a structural summary of the
    project as constellations."""

    TIERS = (
        "primordials", "titans", "olympians", "underworld",
        "monsters", "heroes", "fates", "furies", "graces", "muses",
    )

    def chart(self) -> list[Constellation]:
        """Read the filesystem; group .py modules by mythological tier."""
        out: list[Constellation] = []
        for tier in self.TIERS:
            tier_path = root.child("src", "olympus", tier)
            if not tier_path.exists():
                continue
            members: list[str] = []
            for f in sorted(tier_path.rglob("*.py")):
                if f.name.startswith("_") or f.name == "base.py":
                    continue
                rel = f.relative_to(tier_path).as_posix()[:-3]  # strip .py
                members.append(rel)
            if members:
                out.append(Constellation(tier=tier, members=members))
        return out

    def as_text(self) -> str:
        lines: list[str] = []
        for c in self.chart():
            lines.append(f"## {c.tier}  ({len(c.members)})")
            for m in c.members:
                lines.append(f"  · {m}")
            lines.append("")
        return "\n".join(lines)


urania = Urania()
