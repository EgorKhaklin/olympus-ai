"""Tartarus — the abyss beneath the underworld.

Tartarus is the deepest pit in the cosmos: a prison for the Titans
defeated by Zeus, sealed by bronze gates. Olympus's Tartarus is where
quarantined data goes — irretrievable to normal flows, preserved
only for forensic inspection.

Things thrown into Tartarus are never returned by normal queries.
Only Hecate (crossroads / error-recovery) can summon them, and only
with cause.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

from olympus.primordials.gaia import root


class Tartarus:
    """Quarantine for corrupted / suspicious / forbidden artifacts.

    Tartarus appends each consigned artifact to a JSONL file with
    metadata. It does NOT delete; deletion is Atropos's domain. It does
    NOT archive; that is Hades's. Tartarus is the explicit refusal —
    "this is wrong, do not let it back."
    """

    PIT_FILE = "state/tartarus.jsonl"

    def __init__(self, pit_path: pathlib.Path | None = None) -> None:
        self.pit_path = pit_path or root.child(self.PIT_FILE)
        self.pit_path.parent.mkdir(parents=True, exist_ok=True)

    def consign(self, artifact: Any, reason: str, witness: str = "anonymous") -> None:
        """Cast `artifact` into the pit. The act is append-only and
        timestamped. `witness` records who threw it down."""
        from olympus.primordials.nyx import Nyx
        entry = {
            "ts": Nyx.now().isoformat(),
            "witness": witness,
            "reason": reason,
            "artifact_repr": repr(artifact)[:2000],
        }
        with self.pit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def count(self) -> int:
        """How many souls are in the pit."""
        if not self.pit_path.exists():
            return 0
        with self.pit_path.open("r", encoding="utf-8") as f:
            return sum(1 for _ in f)


tartarus = Tartarus()
quarantine = tartarus.consign
