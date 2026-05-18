"""Heracles — strongest of mortal heroes, completer of twelve labors.

Heracles was set twelve impossible tasks by King Eurystheus. He
completed every one. In Olympus, Heracles is the kill-test runner:
a battery of twelve adversarial scenarios, each meant to break a
specific substrate invariant. A run is successful only when all
twelve are completed without breakage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class Labor:
    """One of the twelve. Named after the original myth."""
    number: int
    name: str            # canonical name (e.g., "Nemean Lion")
    target: str          # which Olympus surface this attacks
    fn: Callable[[], bool]   # runner; True = survived, False = broke


@dataclass
class Verdict:
    labor: Labor
    survived: bool
    detail: str


class Heracles:
    """The twelve-labor kill-test runner."""

    def __init__(self) -> None:
        self._labors: dict[int, Labor] = {}

    def assign(self, labor: Labor) -> None:
        """Register a labor. Number must be 1..12."""
        if not 1 <= labor.number <= 12:
            raise ValueError(f"labor number must be 1..12; got {labor.number}")
        self._labors[labor.number] = labor

    def perform(self) -> list[Verdict]:
        """Run all assigned labors. Returns one Verdict per labor."""
        verdicts: list[Verdict] = []
        for n in range(1, 13):
            labor = self._labors.get(n)
            if labor is None:
                continue
            try:
                survived = bool(labor.fn())
                detail = "survived" if survived else "broke"
            except Exception as exc:
                survived = False
                detail = f"raised: {type(exc).__name__}: {exc}"
            verdicts.append(Verdict(labor=labor, survived=survived, detail=detail))
        return verdicts


heracles = Heracles()


# The canonical twelve labors (placeholders — deployments fill in fn=).
CANONICAL_LABORS = [
    Labor(1,  "Nemean Lion",          "monsters/hydra",           lambda: True),
    Labor(2,  "Lernaean Hydra",       "monsters/hydra",           lambda: True),
    Labor(3,  "Ceryneian Hind",       "olympians/artemis",        lambda: True),
    Labor(4,  "Erymanthian Boar",     "olympians/ares",           lambda: True),
    Labor(5,  "Augean Stables",       "underworld/lethe",         lambda: True),
    Labor(6,  "Stymphalian Birds",    "monsters/argos",           lambda: True),
    Labor(7,  "Cretan Bull",          "olympians/poseidon",       lambda: True),
    Labor(8,  "Mares of Diomedes",    "fates/atropos",            lambda: True),
    Labor(9,  "Belt of Hippolyta",    "olympians/hera",           lambda: True),
    Labor(10, "Cattle of Geryon",     "olympians/demeter",        lambda: True),
    Labor(11, "Apples of Hesperides", "olympians/apollo",         lambda: True),
    Labor(12, "Cerberus",             "monsters/cerberus",        lambda: True),
]
