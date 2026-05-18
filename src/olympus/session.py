"""olympus.session — the canonical cognitive loop.

One Session is one pass through the substrate's full observe-correlate-
decide cycle:

    Zeus                  (optional directive)
       ↓
    Rhea                  ensure substrate is whole
       ↓
    HYDRA                 read-only observation (9 heads)
       ↓
    Argos                 decentralized scan (9 eyes → pheromones)
       ↓
    Athena                synthesis (HYDRA + Argos → brief)
       ↓
    Apollo                falsifiable predictions (optional)
       ↓
    Hephaestus            surface proposals from the brief
       ↓
    Momus                 contest each proposal via AP1–AP8
       ↓
    Action queue          promote by risk class (LOW autonomous / MEDIUM proposed / HIGH delphi)
       ↓
    Mnemosyne             record the session
       ↓
    Polyhymnia            hymn the Styx chain state

Every link is Olympus-native. No external dependencies. The loop runs
deterministically against the live substrate; results are reproducible
modulo wall-clock timestamps.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any

from olympus.primordials.nyx import Nyx
from olympus.fates.clotho import spin
from olympus.titans.mnemosyne import mnemosyne
from olympus.olympians.hestia import hestia
from olympus.titans.rhea import rhea
from olympus.monsters.hydra import hydra
from olympus.monsters.argos.colony import colony
from olympus.olympians.athena import athena, Brief
from olympus.olympians.hephaestus import hephaestus
from olympus.heroes.momus import momus
from olympus.muses.polyhymnia import polyhymnia
from olympus.action import action_queue, Action


@dataclass
class SessionReport:
    """Everything one session pass produced."""
    session_id: str
    directive: str | None
    started_at: str
    ended_at: str = ""

    hydra_findings: int = 0
    hydra_alerts: int = 0
    hydra_drifts: int = 0
    hydra_by_head: dict[str, int] = field(default_factory=dict)

    argos_pheromones: int = 0
    argos_by_eye: dict[str, int] = field(default_factory=dict)
    argos_alerts: int = 0

    brief_label: str = ""
    brief_findings: int = 0
    brief_recommendations: int = 0
    brief_confidence: float = 0.0

    proposals_count: int = 0
    contests_count: int = 0
    proposals: list[dict[str, Any]] = field(default_factory=list)

    actions_promoted: int = 0
    actions_autoratified: int = 0
    actions_queued_for_zeus: int = 0
    actions_delphi_pending: int = 0

    styx_total: int = 0
    styx_intact: bool = True

    error: str | None = None


class Session:
    """One pass through the cognitive loop."""

    def __init__(self, directive: str | None = None) -> None:
        self.directive = directive
        thread = spin(
            kind="session",
            spun_for=directive or "ambient-observation",
            seed=f"session::{Nyx.now().isoformat()}::{directive or ''}",
        )
        self.id = thread.id
        self.started_at = Nyx.now()

    # ─────────────────────────────────────────────────────────
    # The loop
    # ─────────────────────────────────────────────────────────

    def run(self) -> SessionReport:
        """Execute one full cognitive pass. Always returns a SessionReport;
        catastrophic errors are captured in report.error rather than raising."""
        report = SessionReport(
            session_id=self.id,
            directive=self.directive,
            started_at=self.started_at.isoformat(),
        )

        try:
            self._preflight()
            self._observe(report)
            self._synthesize(report)
            self._propose_and_contest(report)
            self._promote(report)
            self._record(report)
        except Exception as exc:  # noqa: BLE001
            report.error = f"{type(exc).__name__}: {exc}"
            mnemosyne.remember(
                kind="session.errored",
                actor="session-runner",
                summary=f"session {self.id} aborted: {report.error}",
                session_id=self.id, error=report.error,
            )
        finally:
            report.ended_at = Nyx.now().isoformat()
            hymn = polyhymnia.hymn()
            report.styx_total = hymn.total_oaths
            report.styx_intact = hymn.intact

        return report

    # ─────────────────────────────────────────────────────────
    # Phases
    # ─────────────────────────────────────────────────────────

    def _preflight(self) -> None:
        """Hestia must be lit; Rhea ensures the substrate."""
        if not hestia.is_lit():
            raise RuntimeError(
                "hearth is unlit — kindle Hestia before sessioning "
                "(invoke kindle <name> <vocation>)"
            )
        rhea.bring_forth()

    def _observe(self, report: SessionReport) -> None:
        """HYDRA reads + Argos scans, in that order. Read-only by S3."""
        h = hydra.behead()
        report.hydra_findings = h.total
        report.hydra_alerts = len(h.alerts)
        report.hydra_drifts = len(h.drifts)
        report.hydra_by_head = {name: len(fs) for name, fs in h.by_head.items()}
        self._hydra_report = h

        c = colony.deploy()
        report.argos_pheromones = c.count
        report.argos_by_eye = {name: len(ps) for name, ps in c.by_eye.items()}
        report.argos_alerts = sum(1 for p in c.pheromones if p.kind == "alert")
        self._argos_census = c

    def _synthesize(self, report: SessionReport) -> None:
        """Athena turns HYDRA + Argos into a brief."""
        label = f"session-{self.id[:16]}"
        brief = athena.compose_from(
            hydra_report=self._hydra_report,
            argos_census=self._argos_census,
            label=label,
            directive=self.directive,
        )
        report.brief_label = brief.label
        report.brief_findings = len(brief.findings)
        report.brief_recommendations = len(brief.recommendations)
        report.brief_confidence = brief.confidence
        self._brief = brief

    def _propose_and_contest(self, report: SessionReport) -> None:
        """Hephaestus surfaces proposals; Momus contests each."""
        proposals = hephaestus.surface_from(self._brief)
        for p in proposals:
            ap_ids = momus.contest_via_brief(p, self._brief)
            report.proposals.append({
                "id": p.id,
                "risk_class": p.risk_class,
                "drift": p.drift_observed,
                "fix": p.proposed_fix,
                "contests": ap_ids,
            })
            report.contests_count += len(ap_ids)
        report.proposals_count = len(proposals)
        self._proposals = proposals

    def _promote(self, report: SessionReport) -> None:
        """Each proposal becomes an Action, routed by risk class.

          LOW  + zero Momus contests  → auto-ratified
          LOW  + Momus contests       → queued for Zeus
          MEDIUM                       → queued for Zeus review
          HIGH / COMPOSITE             → delphi-pending (waits for Zeus oath)
        """
        for p in self._proposals:
            contests = next(
                (rp["contests"] for rp in report.proposals if rp["id"] == p.id),
                [],
            )
            action = action_queue.promote(p, contests=contests)
            report.actions_promoted += 1
            if action.status == "auto-ratified":
                report.actions_autoratified += 1
            elif action.status == "queued":
                report.actions_queued_for_zeus += 1
            elif action.status == "delphi-pending":
                report.actions_delphi_pending += 1

    def _record(self, report: SessionReport) -> None:
        """One Mnemosyne entry summarizing the session."""
        mnemosyne.remember(
            kind="session.completed",
            actor="session-runner",
            summary=(f"session {self.id[:16]} — {report.hydra_findings} hydra · "
                     f"{report.argos_pheromones} argos · "
                     f"{report.proposals_count} proposals "
                     f"({report.actions_autoratified} auto, "
                     f"{report.actions_queued_for_zeus} queued, "
                     f"{report.actions_delphi_pending} delphi)"),
            session_id=self.id,
            directive=self.directive,
            hydra_findings=report.hydra_findings,
            argos_pheromones=report.argos_pheromones,
            proposals=report.proposals_count,
        )


def run_session(directive: str | None = None) -> SessionReport:
    """Convenience: one-line session runner."""
    return Session(directive=directive).run()
