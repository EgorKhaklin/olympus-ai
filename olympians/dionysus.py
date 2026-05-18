"""Dionysus — god of wine, ecstasy, and transformation.

Dionysus presides over the moment things become other things — grape
to wine, sober to drunk, ordinary to ecstatic. In Olympus, Dionysus
is the transformation primitive: every state change a component
undergoes is recorded as a Dionysian transition.

Use Dionysus for refactoring records, schema migrations, version bumps.
The transition is the artifact; the prior state is preserved in Hades.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, asdict
from typing import Any

from primordials.gaia import root
from primordials.nyx import Nyx
from underworld.hades import descend


@dataclass
class Transition:
    """A recorded state change."""
    subject: str          # what was transformed
    from_state: Any
    to_state: Any
    catalyst: str         # what caused the change
    happened_at: str


class Dionysus:
    """State-transition recorder."""

    LEDGER = "olympians/dionysus_transitions.jsonl"

    def __init__(self, path: pathlib.Path | None = None) -> None:
        self.path = path or root.child(self.LEDGER)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def transform(self, subject: str, from_state: Any, to_state: Any,
                  catalyst: str) -> Transition:
        """Record a transition. Archives `from_state` to Hades."""
        t = Transition(
            subject=subject,
            from_state=from_state,
            to_state=to_state,
            catalyst=catalyst,
            happened_at=Nyx.now().isoformat(),
        )
        descend(f"dionysus--{subject}--pre", from_state)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(t), default=str) + "\n")
        return t

    def history(self, subject: str | None = None) -> list[Transition]:
        if not self.path.exists():
            return []
        out: list[Transition] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                if subject is None or d["subject"] == subject:
                    out.append(Transition(**d))
        return out


dionysus = Dionysus()
