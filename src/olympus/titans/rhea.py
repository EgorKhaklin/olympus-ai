"""Rhea — titaness of motherhood, mother of Zeus.

Rhea bore Zeus and hid him from Cronus, who would have devoured him.
She is generative, protective, the one who *makes the next thing exist*
under hostile conditions. In Olympus, Rhea is the bootstrap primitive:
she lights the hearth, registers the core gods, and prepares the
substrate for the first session.
"""
from __future__ import annotations

import pathlib

from olympus.primordials.gaia import root
from olympus.titans.mnemosyne import mnemosyne


class Rhea:
    """Bootstrap orchestrator. Ensures a fresh Olympus deployment has
    its directories in place and its hearth lit."""

    # Runtime directories Rhea ensures exist. Source-code tiers live under
    # src/olympus/ and are present by virtue of being in the package; Rhea
    # need not create those. What Rhea does create is the runtime-state
    # tree (state/) and the operator-authored prose directories under
    # codex/ that get written to by Clio, Melpomene, and the Delphi protocol.
    REQUIRED_DIRS = (
        "state",
        "state/argos",
        "state/mnemosyne",
        "state/hades",
        "state/athena",
        "state/hephaestus",
        "codex",
        "codex/journal",
        "codex/postmortems",
        "codex/oracles/delphi",
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
