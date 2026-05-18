"""Ares — god of war and violent conflict.

Ares is brutal where Athena is strategic. He represents force without
restraint. In Olympus, Ares is the adversarial-testing primitive: he
attacks the substrate to see what breaks. Failure cases live in the
arena Ares prepares.

Use Ares for chaos engineering, fault injection, and red-team scenarios.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class Assault:
    """A single adversarial scenario."""
    name: str
    description: str
    fn: Callable[[], None]
    expected_outcome: str  # "refused" / "absorbed" / "raised"


class Ares:
    """Adversarial-test orchestrator. Registers and runs assaults
    against the substrate."""

    def __init__(self) -> None:
        self._assaults: dict[str, Assault] = {}

    def declare_war(self, name: str, description: str,
                    fn: Callable[[], None],
                    expected_outcome: str = "refused") -> Assault:
        """Register an adversarial scenario."""
        a = Assault(name, description, fn, expected_outcome)
        self._assaults[name] = a
        return a

    def battle(self, name: str) -> dict[str, Any]:
        """Run a single assault; return result with outcome."""
        a = self._assaults.get(name)
        if a is None:
            return {"name": name, "outcome": "no-such-assault"}
        actual = "absorbed"
        exc_str: str | None = None
        try:
            a.fn()
        except Exception as exc:
            actual = "raised"
            exc_str = f"{type(exc).__name__}: {exc}"
        verdict = "passed" if actual == a.expected_outcome else "failed"
        return {
            "name": name,
            "description": a.description,
            "expected": a.expected_outcome,
            "actual": actual,
            "verdict": verdict,
            "exception": exc_str,
        }

    def total_war(self) -> list[dict[str, Any]]:
        """Run every registered assault."""
        return [self.battle(name) for name in self._assaults]


ares = Ares()
