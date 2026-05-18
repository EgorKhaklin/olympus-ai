"""Colony — the orchestrator that dispatches Eyes and aggregates their
pheromones.

The colony does NOT call any Eye-internal method beyond scan(). It
does NOT inspect Eye state. It does NOT synthesize across eyes. All
synthesis is emergent at read time from the aggregated pheromone log.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Type

from olympus.monsters.argos.base import Eye, EyeFinding, Pheromone
from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class Census:
    """One colony run's outputs."""
    pheromones: list[Pheromone] = field(default_factory=list)
    by_eye: dict[str, list[Pheromone]] = field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.pheromones)


class Colony:
    """Argos colony orchestrator."""

    LOG = "state/argos_pheromones.jsonl"

    def __init__(self, log_path: pathlib.Path | None = None) -> None:
        self.log_path = log_path or root.child(self.LOG)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._eyes: list[Eye] = []

    def register(self, eye_cls: Type[Eye]) -> None:
        """Instantiate and add an Eye to the colony."""
        self._eyes.append(eye_cls())

    def eyes(self) -> list[Eye]:
        return list(self._eyes)

    def deploy(self, *, deposit: bool = True) -> Census:
        """Run every Eye's scan(); aggregate findings into pheromones;
        optionally append to the pheromone log."""
        census = Census()
        for eye in self._eyes:
            try:
                findings = eye.scan()
            except Exception as exc:
                findings = [EyeFinding(
                    eye=eye.NAME, slice=eye.SLICE,
                    kind="alert", intensity=10.0,
                    detail=f"eye raised: {type(exc).__name__}: {exc}",
                )]
            phers = [Pheromone.from_finding(f) for f in findings]
            census.pheromones.extend(phers)
            census.by_eye[eye.NAME] = phers

        if deposit:
            with self.log_path.open("a", encoding="utf-8") as f:
                for p in census.pheromones:
                    f.write(json.dumps(p.as_dict(), default=str) + "\n")

        mnemosyne.remember(
            kind="colony.deploy",
            actor="argos",
            summary=f"deployed {len(self._eyes)} eye(s); {census.count} pheromone(s) emitted",
            eye_count=len(self._eyes),
            pheromone_count=census.count,
            alerts=sum(1 for p in census.pheromones if p.kind == "alert"),
        )
        return census

    def read_log(self) -> list[Pheromone]:
        """Read every pheromone ever deposited."""
        if not self.log_path.exists():
            return []
        out: list[Pheromone] = []
        with self.log_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                out.append(Pheromone(**d))
        return out


colony = Colony()


# Register the default Olympus-native eyes.
def _register_defaults() -> None:
    from olympus.monsters.argos.eyes.eye_cosmogony_drift import EyeCosmogonyDrift
    from olympus.monsters.argos.eyes.eye_pantheon_completeness import EyePantheonCompleteness
    from olympus.monsters.argos.eyes.eye_styx_chain_intact import EyeStyxChainIntact
    from olympus.monsters.argos.eyes.eye_journal_silence import EyeJournalSilence
    from olympus.monsters.argos.eyes.eye_chronicle_gap import EyeChronicleGap
    from olympus.monsters.argos.eyes.eye_oath_freshness import EyeOathFreshness
    from olympus.monsters.argos.eyes.eye_apollo_coverage import EyeApolloCoverage
    from olympus.monsters.argos.eyes.eye_delphi_pending import EyeDelphiPending
    from olympus.monsters.argos.eyes.eye_understanding_gap import EyeUnderstandingGap

    for cls in (EyeCosmogonyDrift, EyePantheonCompleteness,
                EyeStyxChainIntact, EyeJournalSilence, EyeChronicleGap,
                EyeOathFreshness, EyeApolloCoverage, EyeDelphiPending,
                EyeUnderstandingGap):
        colony.register(cls)


_register_defaults()
