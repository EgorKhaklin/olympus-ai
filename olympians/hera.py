"""Hera — queen of the gods, goddess of marriage and bindings.

Hera's domain is *what is married to what*. In Olympus, Hera tracks
named relationships between components: which Eye reports to which
Phalanx, which Hero serves which directive, which Head watches which
slice of substrate.

The bindings table is queryable but immutable per-binding (you can add,
you cannot edit). Breaking a binding requires Atropos.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, asdict

from primordials.gaia import root
from primordials.nyx import Nyx


@dataclass(frozen=True)
class Binding:
    """A marriage between two named things."""
    name: str            # short name (e.g., "head_security_watches_substrate")
    left: str            # e.g., "monsters.hydra.heads.head_security"
    right: str           # e.g., "monsters.argos.phalanges.phalanx_substrate"
    role: str            # what kind of binding (watches, reports-to, serves, ...)
    bound_at: str        # ISO timestamp


class Hera:
    """Registry of named relationships."""

    REGISTRY = "olympians/hera_bindings.jsonl"

    def __init__(self, path: pathlib.Path | None = None) -> None:
        self.path = path or root.child(self.REGISTRY)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def bind(self, name: str, left: str, right: str, role: str) -> Binding:
        """Record a binding. Appends to the registry."""
        b = Binding(
            name=name, left=left, right=right, role=role,
            bound_at=Nyx.now().isoformat(),
        )
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(b)) + "\n")
        return b

    def bindings(self) -> list[Binding]:
        if not self.path.exists():
            return []
        out: list[Binding] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                out.append(Binding(**d))
        return out

    def of(self, left: str) -> list[Binding]:
        """All bindings where `left` is on the left side."""
        return [b for b in self.bindings() if b.left == left]


hera = Hera()
