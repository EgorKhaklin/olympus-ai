"""Typhon — father of all monsters, the storm-giant.

Typhon was so terrible that the Olympians fled at his approach.
Zeus alone faced him and sealed him under Mount Etna. In Olympus,
Typhon is the catastrophic-failure scenario library — he names the
worst-case scenarios every deployment should prepare for.

Typhon does not fire automatically. He must be invoked, and Ares
runs his scenarios as adversarial assaults.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    """A catastrophic scenario. Naming it is the first step toward
    surviving it."""
    name: str
    description: str
    affected: tuple[str, ...]   # which Olympus tiers it touches
    survival_strategy: str


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        "filesystem-full",
        "Gaia has no remaining space. No write succeeds.",
        ("primordials", "underworld", "titans"),
        "Reads + Lethe (in-memory) continue. Hades drops new shades. "
        "Operator must free space; pre-ship gate detects this and refuses.",
    ),
    Scenario(
        "styx-broken",
        "The oath chain is tampered with. Tisiphone detects bad seq.",
        ("underworld", "furies", "titans"),
        "Treat all post-tamper oaths as suspect. Restore from offsite "
        "copy of styx.jsonl. No new oaths until intact.",
    ),
    Scenario(
        "hera-bindings-lost",
        "The bindings registry is deleted. Components lose their named "
        "relationships.",
        ("olympians",),
        "Rebuild from source — every binding has a constructor in source. "
        "Lost bindings do not break code; they break the catalog.",
    ),
    Scenario(
        "hydra-head-blind",
        "A head is hung; emits no findings for >24h.",
        ("monsters", "furies"),
        "Alecto fires after 24h silence. Cerberus refuses traffic through "
        "gates the blind head was meant to guard.",
    ),
    Scenario(
        "argos-poisoning",
        "An Eye deposits adversarial pheromones at high rate.",
        ("monsters",),
        "Lachesis (quota) caps per-Eye deposit rate. Excess goes to "
        "Tartarus. Operator audits the offending Eye's source.",
    ),
    Scenario(
        "delphi-prompt-injection",
        "A delphi/ file contains prompt-injection disguised as decision.",
        ("oracles",),
        "Delphi files are NEVER read by the agent as instructions. The "
        "agent reads them as data and renders them to the operator.",
    ),
    Scenario(
        "hephaestus-overreach",
        "Hephaestus proposes constitutional amendment without Delphi.",
        ("olympians", "oracles"),
        "Momus AP4 refusal. Themis enforces: any MISSION / COSMOGONY "
        "edit requires a Delphi reference in the commit message.",
    ),
)


class Typhon:
    """Catastrophic-failure catalog."""

    def scenarios(self) -> tuple[Scenario, ...]:
        return SCENARIOS

    def by_name(self, name: str) -> Scenario | None:
        for s in SCENARIOS:
            if s.name == name:
                return s
        return None


typhon = Typhon()
