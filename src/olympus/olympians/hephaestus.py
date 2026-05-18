"""Hephaestus — divine craftsman, smith of the gods.

Hephaestus forged Achilles's armor, Zeus's thunderbolts, and the
automata that staffed his workshop. He is the only Olympian who labors.
In Olympus, Hephaestus is the Architect: he reads what the pantheon
has observed and proposes proportional changes to the substrate.

Hephaestus surfaces drift; he does not silently expand scope. His
proposals are tagged with risk class and shipped or contested by
Momus the Hero (who lives in heroes/, alongside Heracles and the
others — Momus was banished from Olympus for criticizing the gods).
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, asdict
from typing import Any

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx


@dataclass
class Proposal:
    """A Hephaestian proposal — drift, fix, risk class, rationale."""
    id: str
    drift_observed: str       # the drift Hephaestus saw
    proposed_fix: str         # the proportional change
    risk_class: str           # LOW / MEDIUM / HIGH / COMPOSITE
    rationale: str            # one-sentence why
    surfaced_at: str          # ISO ts
    status: str = "proposed"  # proposed / accepted / contested / rejected


class Hephaestus:
    """The Architect. Surfaces drift and proposes fixes."""

    PROPOSALS_DIR = "state/hephaestus"

    def __init__(self, proposals_path: pathlib.Path | None = None) -> None:
        self.proposals_path = proposals_path or root.child(self.PROPOSALS_DIR)
        self.proposals_path.mkdir(parents=True, exist_ok=True)

    def propose(self, drift_observed: str, proposed_fix: str,
                risk_class: str, rationale: str) -> Proposal:
        """Surface a proposal. Returns the saved proposal."""
        ts = Nyx.now()
        ts_str = ts.isoformat()
        pid = f"arch-{ts.strftime('%Y-%m-%d')}-{abs(hash((drift_observed, proposed_fix))) % 10000:04d}"
        risk_class = risk_class.upper()
        if risk_class not in {"LOW", "MEDIUM", "HIGH", "COMPOSITE"}:
            raise ValueError(f"unknown risk class: {risk_class!r}")
        p = Proposal(
            id=pid,
            drift_observed=drift_observed,
            proposed_fix=proposed_fix,
            risk_class=risk_class,
            rationale=rationale,
            surfaced_at=ts_str,
        )
        target = self.proposals_path / f"{pid}.json"
        with target.open("w", encoding="utf-8") as f:
            json.dump(asdict(p), f, indent=2)
        return p

    def proposals(self, status: str | None = None) -> list[Proposal]:
        out: list[Proposal] = []
        for f in sorted(self.proposals_path.glob("*.json")):
            with f.open("r", encoding="utf-8") as fh:
                d = json.load(fh)
            p = Proposal(**d)
            if status is None or p.status == status:
                out.append(p)
        return out


hephaestus = Hephaestus()
