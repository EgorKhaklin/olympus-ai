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

    def surface_from(self, brief: Any, correlation: Any = None) -> list[Proposal]:
        """Given an Athena brief (and optional CorrelationEngine report),
        surface zero or more proposals.

        Hephaestus's rule of thumb:
          - every ALERT in the brief becomes a proposal (one per unique slice)
          - cross-tier corroborations in recommendations become proposals
          - cluster slices (correlation) UPGRADE the risk class of related proposals
          - quiet eyes (correlation) generate proposals on their own — a stopped
            observer is itself a finding
          - cascade patterns (correlation) annotate the rationale
          - capped at 5 proposals per pass by Lachesis (prevents flooding)
        """
        from olympus.fates.lachesis import lachesis, Quota

        if "hephaestus.per-pass" not in lachesis._quotas:
            lachesis.allot(Quota(name="hephaestus.per-pass",
                                 ceiling=5.0, units="proposals"))

        # Index correlation signals by slice for risk-weighting
        clustered_slices: dict[str, int] = {}
        cascade_pairs: list[tuple[str, str, int]] = []
        quiet_eyes: list[tuple[str, float]] = []
        if correlation is not None:
            for c in getattr(correlation, "clusters", []):
                clustered_slices[c.slice] = len(c.eyes)
            for c in getattr(correlation, "cascades", []):
                cascade_pairs.append((c.leader, c.follower, c.instances))
            for q in getattr(correlation, "quiet", []):
                quiet_eyes.append((q.eye, q.hours_silent))

        # Hephaestus reads what Zeus already killed — the loop doesn't nag.
        recently_rejected = self._recently_rejected_drift_signatures(window_days=7)
        chronic_drifts = self._chronically_rejected_drift_signatures(threshold=3)

        surfaced: list[Proposal] = []
        seen_slices: set[str] = set()

        # 1. Brief alerts → proposals (risk upgraded if slice is clustered)
        for f in brief.findings:
            severity = f.get("severity") or f.get("kind") or "info"
            if severity != "alert":
                continue
            slice_name = f.get("slice", "<unspecified>")
            if slice_name in seen_slices:
                continue
            seen_slices.add(slice_name)

            # Rejection-aware: chronic check first (emit fatigue signal once),
            # then recently-rejected (silent skip).
            drift_sig = self._drift_signature(
                source=f.get("source", "?"),
                slice_name=slice_name,
            )
            if drift_sig in chronic_drifts:
                # Replace the would-be proposal with a single fatigue signal,
                # once per pass.
                if not any("proposal-fatigue" in p.drift_observed
                           for p in surfaced):
                    if lachesis.measure("hephaestus.per-pass", 1.0):
                        surfaced.append(self.propose(
                            drift_observed=(f"proposal-fatigue: drift "
                                            f"signature {drift_sig!r} has been "
                                            f"rejected ≥3 times — Hephaestus "
                                            f"stops nagging"),
                            proposed_fix=("review whether the underlying "
                                          "predicate should be retired or the "
                                          "domain rule changed"),
                            risk_class="LOW",
                            rationale="rejection-history saturation",
                        ))
                continue
            if drift_sig in recently_rejected:
                continue

            if not lachesis.measure("hephaestus.per-pass", 1.0):
                break

            base_risk = "MEDIUM" if "S" in str(f.get("detail", "")) else "LOW"
            cluster_strength = clustered_slices.get(slice_name, 0)
            # Risk-upgrade: ≥3 corroborating eyes upgrades LOW → MEDIUM → HIGH
            risk = base_risk
            if cluster_strength >= 3 and risk == "MEDIUM":
                risk = "HIGH"
            elif cluster_strength >= 3 and risk == "LOW":
                risk = "MEDIUM"

            rationale_parts = [
                f"alert surfaced by {f.get('source')} during session synthesis"
            ]
            if cluster_strength:
                rationale_parts.append(
                    f"corroborated by {cluster_strength} eye(s) (cluster)"
                )

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
                rationale=" · ".join(rationale_parts),
            )
            surfaced.append(p)

        # 2. Quiet eyes → proposals (a stopped observer IS a finding)
        for eye_name, hours in quiet_eyes:
            if not lachesis.measure("hephaestus.per-pass", 1.0):
                break
            p = self.propose(
                drift_observed=(
                    f"correlation engine reports eye {eye_name!r} silent "
                    f"for {hours:.0f} hour(s) — possible runtime failure"
                ),
                proposed_fix=(
                    f"verify {eye_name} executes on next colony.deploy() and "
                    f"either fix its scan() or retire it via Atropos"
                ),
                risk_class="MEDIUM",
                rationale="quiet-eye signal from CorrelationEngine",
            )
            surfaced.append(p)

        # 3. Brief recommendations with alert/investigate hints
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

    # ─────────────────────────────────────────────────────────
    # Rejection memory — Hephaestus learns what Zeus killed
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _drift_signature(*, source: str, slice_name: str) -> str:
        """Canonical signature for a drift, used to compare across sessions.
        Same source + slice → same signature. Source can be 'hydra' or
        'argos' or '?'."""
        return f"{source}::{slice_name}"

    def _recently_rejected_drift_signatures(self, *, window_days: int = 7) -> set[str]:
        """Read action.rejected memories from the last window_days; return
        the set of drift signatures the operator has refused recently."""
        from olympus.titans.mnemosyne import mnemosyne
        from olympus.titans.cronus import Cronus
        cutoff_s = window_days * 86400.0
        out: set[str] = set()
        for m in mnemosyne.recall("action.rejected"):
            if Cronus.age_seconds(m.remembered_at) > cutoff_s:
                continue
            sig = self._signature_for_action_id(m.body.get("action_id", ""))
            if sig:
                out.add(sig)
        return out

    def _chronically_rejected_drift_signatures(self, *, threshold: int = 3) -> set[str]:
        """Drift signatures that have been rejected ≥ threshold times total."""
        from olympus.titans.mnemosyne import mnemosyne
        counts: dict[str, int] = {}
        for m in mnemosyne.recall("action.rejected"):
            sig = self._signature_for_action_id(m.body.get("action_id", ""))
            if sig:
                counts[sig] = counts.get(sig, 0) + 1
        return {sig for sig, n in counts.items() if n >= threshold}

    def _signature_for_action_id(self, action_id: str) -> str | None:
        """Look up an action_id → its originating proposal → drift signature.
        Reads from the proposals on disk."""
        if not action_id:
            return None
        # action ids are 'act-<proposal_id>'
        if action_id.startswith("act-"):
            pid = action_id[4:]
        else:
            pid = action_id
        target = self.proposals_path / f"{pid}.json"
        if not target.exists():
            return None
        try:
            with target.open("r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:  # noqa: BLE001
            return None
        drift = d.get("drift_observed", "")
        # Parse signature from the drift text written by surface_from
        # Format: "{source} reports {sev} on slice '{slice}': ..."
        import re as _re
        match = _re.match(
            r"(hydra|argos|\?)\s+reports.*?slice\s+'([^']+)'",
            drift,
        )
        if match:
            return self._drift_signature(
                source=match.group(1), slice_name=match.group(2),
            )
        return None


hephaestus = Hephaestus()
