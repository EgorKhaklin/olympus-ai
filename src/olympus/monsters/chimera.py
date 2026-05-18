"""The Chimera — lion-headed, goat-bodied, serpent-tailed.

The Chimera was a single beast composed of three creatures fused
together. In Olympus, the Chimera is the composite-test runner: she
runs heterogeneous tests as a single bundle and reports per-head
verdicts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class Head:
    name: str               # e.g., "structural", "semantic", "performance"
    fn: Callable[[], Any]   # returns truthy on success
    label: str              # one-line description


@dataclass
class CompositeVerdict:
    head: str
    passed: bool
    detail: str


class Chimera:
    """Composite-test orchestrator."""

    def __init__(self) -> None:
        self._heads: dict[str, Head] = {}

    def graft(self, head: Head) -> None:
        self._heads[head.name] = head

    def breathe(self) -> list[CompositeVerdict]:
        """Run every head; return per-head verdicts."""
        verdicts: list[CompositeVerdict] = []
        for name, head in self._heads.items():
            try:
                result = head.fn()
                passed = bool(result)
                detail = "passed" if passed else f"falsy: {result!r}"
            except Exception as exc:
                passed = False
                detail = f"raised: {type(exc).__name__}: {exc}"
            verdicts.append(CompositeVerdict(head=name, passed=passed, detail=detail))
        return verdicts


chimera = Chimera()
