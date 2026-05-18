"""Demos — the people, the assembly.

The demos was the citizen assembly of the Greek polis. In Olympus,
Demos watches public-facing surfaces: codex/ documents, README,
the public face of the substrate."""
from __future__ import annotations

from olympus.monsters.argos.demes.base import Deme, DemeFinding
from olympus.primordials.gaia import root


PUBLIC_FACING = (
    "README.md", "codex/COSMOGONY.md", "codex/PANTHEON.md",
    "codex/RITES.md", "codex/CHRONICLE.md",
    "codex/PROPHECIES.md", "codex/BESTIARY.md",
)


class Demos(Deme):
    NAME = "demos"
    ROLE = "the people / public-facing watch"

    def observe(self) -> DemeFinding:
        present = [rel for rel in PUBLIC_FACING if root.child(rel).exists()]
        missing = [rel for rel in PUBLIC_FACING if not root.child(rel).exists()]
        if missing:
            return DemeFinding(
                deme=self.NAME, role=self.ROLE,
                summary=f"{len(missing)} public document(s) missing",
                detail={"missing": missing, "present": present},
            )
        return DemeFinding(
            deme=self.NAME, role=self.ROLE,
            summary=f"all {len(PUBLIC_FACING)} public documents present",
            detail={"present": present},
        )


demos = Demos()
