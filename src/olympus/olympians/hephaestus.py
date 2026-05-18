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

    # ─────────────────────────────────────────────────────────
    # Surface proposals from a brief (the loop's decide phase)
    # ─────────────────────────────────────────────────────────

    def surface_from(self, brief: Any) -> list[Proposal]:
        """Given an Athena brief, surface zero or more proposals.

        Hephaestus's rule of thumb:
          - every ALERT in the brief becomes a proposal (one per unique slice)
          - cross-tier corroborations in recommendations become proposals
          - capped at 5 proposals per pass by Lachesis (prevents flooding)
        """
        from olympus.fates.lachesis import lachesis, Quota

        if "hephaestus.per-pass" not in lachesis._quotas:
            lachesis.allot(Quota(name="hephaestus.per-pass",
                                 ceiling=5.0, units="proposals"))

        surfaced: list[Proposal] = []
        seen_slices: set[str] = set()

        # Walk the brief's findings; alerts get a proposal
        for f in brief.findings:
            severity = f.get("severity") or f.get("kind") or "info"
            if severity != "alert":
                continue
            slice_name = f.get("slice", "<unspecified>")
            if slice_name in seen_slices:
                continue
            seen_slices.add(slice_name)

            if not lachesis.measure("hephaestus.per-pass", 1.0):
                break  # quota exhausted

            risk = "MEDIUM" if "S" in str(f.get("detail", "")) else "LOW"
            p = self.propose(
                drift_observed=(
                    f"{f.get('source', '?')} reports {severity} on slice "
                    f"'{slice_name}': {str(f.get('detail', ''))[:120]}"
                ),
                proposed_fix=(
                    f"investigate slice '{slice_name}' and either fix the "
                    f"underlying cause or update the watcher predicate"
                ),
                risk_class=risk,
                rationale=f"alert surfaced by {f.get('source')} during session synthesis",
            )
            surfaced.append(p)

        # Recommendations with investigate/alert hints get proposals too
        for rec in brief.recommendations:
            low = rec.lower()
            if "alert" not in low and "investigate" not in low:
                continue
            if not lachesis.measure("hephaestus.per-pass", 1.0):
                break
            p = self.propose(
                drift_observed=f"Athena recommendation: {rec[:140]}",
                proposed_fix="ratify or contest this recommendation in next session",
                risk_class="LOW",
                rationale="brief-level cross-tier corroboration",
            )
            surfaced.append(p)

        lachesis.reset("hephaestus.per-pass")
        return surfaced


hephaestus = Hephaestus()
