"""Rhea — titaness of motherhood, mother of Zeus.

Rhea bore Zeus and hid him from Cronus, who would have devoured him.
She is generative, protective, the one who *makes the next thing exist*
under hostile conditions. In Olympus, Rhea is the bootstrap primitive:
she lights the hearth, registers the core gods, and prepares the
substrate for the first session.
"""
from __future__ import annotations

import pathlib

from primordials.gaia import root
from titans.mnemosyne import mnemosyne


class Rhea:
    """Bootstrap orchestrator. Ensures a fresh Olympus deployment has
    its directories in place and its hearth lit."""

    REQUIRED_DIRS = (
        "primordials", "titans", "olympians",
        "monsters/hydra", "monsters/argos",
        "underworld", "oracles/delphi",
        "fates", "furies", "graces", "muses",
        "heroes", "chronicle/journal",
        "codex", "rites", "bestiary",
    )

    def __init__(self) -> None:
        self.root = root.root

    def bring_forth(self) -> dict[str, str]:
        """Ensure required directories exist. Idempotent.
        Returns a status dict."""
        statuses: dict[str, str] = {}
        for rel in self.REQUIRED_DIRS:
            path = self.root / rel
            if path.exists():
                statuses[rel] = "extant"
            else:
                path.mkdir(parents=True, exist_ok=True)
                statuses[rel] = "born"
        mnemosyne.remember(
            kind="bootstrap",
            actor="rhea",
            summary="ensured all required directories",
            statuses=statuses,
        )
        return statuses


rhea = Rhea()
