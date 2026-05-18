"""Coeus — titan of inquiry, intellect, the axis of heaven.

Coeus is the rotational axis around which the heavens turn — the
fixed point that lets the cosmos be understood. His name means
"questioning intellect." In Olympus, Coeus is the investigation
primitive: structured queries over the substrate's own state.

When Hephaestus needs to know "what does this slice look like?",
he asks Coeus.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable


@dataclass
class Question:
    """A registered investigation. Each question knows how to answer
    itself."""
    name: str
    summary: str
    asker: Callable[[], Any]


class Coeus:
    """Investigation registry. Add a question via `pose()`, get an
    answer via `ask()`."""

    def __init__(self) -> None:
        self._questions: dict[str, Question] = {}

    def pose(self, name: str, summary: str, asker: Callable[[], Any]) -> Question:
        q = Question(name=name, summary=summary, asker=asker)
        self._questions[name] = q
        return q

    def ask(self, name: str) -> Any:
        q = self._questions.get(name)
        if q is None:
            raise KeyError(f"coeus: no question named {name!r}")
        return q.asker()

    def known(self) -> list[Question]:
        return list(self._questions.values())


coeus = Coeus()


# Register a few default questions that any Olympus deployment cares about.

def _pantheon_population() -> dict[str, int]:
    """How many modules in each tier?"""
    import pathlib
    from primordials.gaia import root

    counts: dict[str, int] = {}
    for tier in ("primordials", "titans", "olympians", "underworld",
                 "monsters", "fates", "furies", "graces", "muses", "heroes"):
        tier_path = root.child(tier)
        if not tier_path.exists():
            counts[tier] = 0
            continue
        counts[tier] = sum(
            1 for p in tier_path.rglob("*.py")
            if not p.name.startswith("_") and p.name != "base.py"
        )
    return counts


coeus.pose(
    "pantheon-population",
    "count of modules per mythological tier",
    _pantheon_population,
)
