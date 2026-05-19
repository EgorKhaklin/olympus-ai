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

    def register(self, eye_or_cls) -> None:
        """Add an Eye to the colony. Accepts either:
          - an Eye subclass (will be instantiated with no args), OR
          - an Eye instance (used directly)

        The instance path was added by the argos-eyes arc to support
        parameterized Eyes (e.g., FilesystemEye(spec))."""
        if isinstance(eye_or_cls, Eye):
            self._eyes.append(eye_or_cls)
        else:
            self._eyes.append(eye_or_cls())

    def eyes(self) -> list[Eye]:
        return list(self._eyes)

    # Lachesis quota — per-eye per-deploy cap (anti-flood)
    PER_EYE_QUOTA_NAME = "argos.per-eye-per-deploy"
    PER_EYE_QUOTA_CEILING = 50.0  # max pheromones one eye may emit per pass

    def deploy(self, *, deposit: bool = True) -> Census:
        """Run every Eye's scan(); aggregate findings into pheromones;
        optionally append to the pheromone log.

        Per-eye output is capped by a Lachesis quota; an eye that exceeds
        the cap has its excess truncated and a single drift pheromone
        appended explaining the cap was hit (S8 reconstructability)."""
        from olympus.fates.lachesis import lachesis, Quota
        from olympus.runtime.boundaries import bounded

        # Register quota lazily
        if self.PER_EYE_QUOTA_NAME not in lachesis._quotas:
            lachesis.allot(Quota(name=self.PER_EYE_QUOTA_NAME,
                                  ceiling=self.PER_EYE_QUOTA_CEILING,
                                  units="pheromones"))

        census = Census()
        for eye in self._eyes:
            # Reset per-eye accounting at the start of each eye's scan
            lachesis.reset(self.PER_EYE_QUOTA_NAME)

            scanner = bounded(name=f"colony.scan.{eye.NAME}")(eye.scan)
            br = scanner()
            if br.ok and br.value is not None:
                findings = br.value
            else:
                findings = [EyeFinding(
                    eye=eye.NAME, slice=eye.SLICE,
                    kind="alert", intensity=10.0,
                    detail=f"eye raised: {br.error}",
                )]

            # Apply Lachesis cap
            allowed: list[EyeFinding] = []
            for f in findings:
                if lachesis.measure(self.PER_EYE_QUOTA_NAME, 1.0):
                    allowed.append(f)
                else:
                    allowed.append(EyeFinding(
                        eye=eye.NAME, slice=eye.SLICE,
                        kind="drift", intensity=5.0,
                        detail=(f"eye exceeded Lachesis cap "
                                f"({self.PER_EYE_QUOTA_CEILING:.0f} pheromones); "
                                f"remainder truncated"),
                    ))
                    break

            phers = [Pheromone.from_finding(f) for f in allowed]
            census.pheromones.extend(phers)
            census.by_eye[eye.NAME] = phers

        if deposit:
            # Use atomic append for concurrency safety
            from olympus.runtime.concurrency import atomic_append
            for p in census.pheromones:
                atomic_append(self.log_path, json.dumps(p.as_dict(), default=str))

        mnemosyne.remember(
            kind="colony.deploy",
            actor="argos",
            summary=(f"deployed {len(self._eyes)} eye(s); "
                     f"{census.count} pheromone(s) emitted"),
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

    # Per Delphi 2026-05-19-argos-eyes-arc.md: register one
    # FilesystemEye per operator-declared WatchSpec.
    try:
        from olympus.monsters.argos.eyes.eye_filesystem import (
            register_filesystem_eyes,
        )
        register_filesystem_eyes(colony)
    except Exception:  # noqa: BLE001
        pass


_register_defaults()
