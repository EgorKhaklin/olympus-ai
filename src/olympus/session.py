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
    hydra_alert_details: list[dict[str, str]] = field(default_factory=list)

    argos_pheromones: int = 0
    argos_by_eye: dict[str, int] = field(default_factory=dict)
    argos_alerts: int = 0
    argos_alert_details: list[dict[str, str]] = field(default_factory=list)

    brief_label: str = ""
    brief_findings: int = 0
    brief_recommendations: int = 0
    brief_recommendation_text: list[str] = field(default_factory=list)
    brief_confidence: float = 0.0

    proposals_count: int = 0
    contests_count: int = 0
    proposals: list[dict[str, Any]] = field(default_factory=list)

    correlation_clusters: int = 0
    correlation_cascades: int = 0
    correlation_quiet: int = 0
    correlation_summary: list[str] = field(default_factory=list)

    actions_promoted: int = 0
    actions_autoratified: int = 0
    actions_queued_for_zeus: int = 0
    actions_delphi_pending: int = 0

    styx_total: int = 0
    styx_intact: bool = True

    duration_ms: float = 0.0
    error: str | None = None

    # ─────────────────────────────────────────────────────────
    # Rendering — turn a report into operator-readable output
    # ─────────────────────────────────────────────────────────

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    def render(self, *, verbose: bool = False) -> str:
        """Format the report for terminal display. verbose=True shows
        the actual brief text, the proposal text, and the contest text;
        verbose=False shows a one-line-per-phase summary table."""
        from olympus.olympians.aphrodite import aphrodite, GOLD, RESET, BOLD, DIM, LAUREL, WINE, SEA
        from olympus.graces.aglaia import aglaia

        out: list[str] = []
        title = f"session {self.session_id[:16]}"
        if self.directive:
            subtitle = f"directive: {self.directive}"
        else:
            subtitle = f"ambient observation · {self.duration_ms:.0f}ms"
        out.append(aglaia.section(title))
        out.append(f"  {DIM}{subtitle}{RESET}")
        out.append("")

        # Phase 1: HYDRA
        out.append(f"{GOLD}❦ {BOLD}HYDRA{RESET} {DIM}— read-only observation across 9 heads{RESET}")
        out.append(f"  {self.hydra_findings} findings  "
                   f"({self.hydra_alerts} alerts, {self.hydra_drifts} drifts)")
        if verbose and self.hydra_alerts:
            for a in self.hydra_alert_details[:5]:
                out.append(f"  {WINE}◐{RESET} {a.get('head')}: {a.get('detail', '')[:100]}")
        if verbose:
            for head, n in self.hydra_by_head.items():
                marker = "·" if n else f"{WINE}!{RESET}"  # silent head is suspicious
                out.append(f"    {marker} {head}: {n}")
        out.append("")

        # Phase 2: Argos
        out.append(f"{GOLD}❦ {BOLD}Argos{RESET} {DIM}— decentralized swarm scan{RESET}")
        out.append(f"  {self.argos_pheromones} pheromones  ({self.argos_alerts} alerts)")
        if verbose and self.argos_alerts:
            for a in self.argos_alert_details[:5]:
                out.append(f"  {WINE}◐{RESET} {a.get('eye')}: {a.get('detail', '')[:100]}")
        out.append("")

        # Phase 3: Athena synthesis
        out.append(f"{GOLD}❦ {BOLD}Athena{RESET} {DIM}— cross-tier synthesis{RESET}")
        out.append(f"  brief {self.brief_label!r}")
        out.append(f"  {self.brief_findings} findings · {self.brief_recommendations} recommendations · "
                   f"confidence {self.brief_confidence:.2f}")
        if verbose and self.brief_recommendation_text:
            for r in self.brief_recommendation_text:
                out.append(f"    {SEA}→{RESET} {r}")
        out.append("")

        # Phase 4: Correlation
        if self.correlation_clusters or self.correlation_cascades or self.correlation_quiet:
            out.append(f"{GOLD}❦ {BOLD}Argos correlation{RESET} {DIM}— cross-eye patterns{RESET}")
            out.append(f"  {self.correlation_clusters} clusters · "
                       f"{self.correlation_cascades} cascades · "
                       f"{self.correlation_quiet} quiet")
            if verbose:
                for line in self.correlation_summary[:5]:
                    out.append(f"    {SEA}→{RESET} {line}")
            out.append("")

        # Phase 5: Hephaestus
        out.append(f"{GOLD}❦ {BOLD}Hephaestus{RESET} {DIM}— surface proposals{RESET}")
        out.append(f"  {self.proposals_count} proposal(s) surfaced")
        if verbose and self.proposals:
            for p in self.proposals:
                out.append(f"  {SEA}{p['id'][:18]}{RESET}  [{p['risk_class']}]")
                out.append(f"    drift: {p['drift'][:100]}")
                out.append(f"    fix:   {p['fix'][:100]}")
                if p.get("contests"):
                    out.append(f"    {WINE}Momus dings:{RESET} {', '.join(p['contests'])}")
        out.append("")

        # Phase 6: Momus
        out.append(f"{GOLD}❦ {BOLD}Momus{RESET} {DIM}— adversarial review{RESET}")
        out.append(f"  {self.contests_count} contest(s) issued via AP1-AP8")
        out.append("")

        # Phase 7: Actions
        out.append(f"{GOLD}❦ {BOLD}Action queue{RESET} {DIM}— promotion by risk class{RESET}")
        out.append(f"  {self.actions_promoted} promoted: "
                   f"{LAUREL}{self.actions_autoratified} auto-ratified{RESET}, "
                   f"{self.actions_queued_for_zeus} queued for Zeus, "
                   f"{self.actions_delphi_pending} delphi-pending")
        out.append("")

        # Phase 8: Styx
        styx_color = LAUREL if self.styx_intact else WINE
        out.append(f"{GOLD}❦ {BOLD}Styx{RESET} {DIM}— oath chain state{RESET}")
        out.append(f"  {self.styx_total} oaths  ·  chain {styx_color}{'intact' if self.styx_intact else 'BROKEN'}{RESET}")
        out.append("")

        if self.error:
            out.append(aphrodite.wine_dark(f"ERROR: {self.error}"))

        return "\n".join(out)


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
        import time
        start_t = time.perf_counter()
        report = SessionReport(
            session_id=self.id,
            directive=self.directive,
            started_at=self.started_at.isoformat(),
        )

        def _cb(phase: str, detail: str = "") -> None:
            if self._on_phase is not None:
                try:
                    self._on_phase(phase, detail, report)
                except Exception:  # noqa: BLE001
                    pass  # callbacks must never break the loop

        try:
            _cb("preflight", "Hestia + Rhea checks")
            self._preflight()
            _cb("observe.hydra", "HYDRA heads observing slices")
            self._observe_hydra(report)
            _cb("observe.argos", "Argos eyes scanning")
            self._observe_argos(report)
            _cb("synthesize", "Athena composing brief")
            self._synthesize(report)
            _cb("correlate", "CorrelationEngine over recent pheromones")
            self._correlate(report)
            _cb("propose", "Hephaestus surfacing proposals from brief")
            self._propose_and_contest(report)
            _cb("promote", "promoting to action queue")
            self._promote(report)
            _cb("record", "Mnemosyne summary")
            self._record(report)
            _cb("complete", "session done")
        except Exception as exc:  # noqa: BLE001
            report.error = f"{type(exc).__name__}: {exc}"
            mnemosyne.remember(
                kind="session.errored",
                actor="session-runner",
                summary=f"session {self.id} aborted: {report.error}",
                session_id=self.id, error=report.error,
            )
            _cb("error", report.error)
        finally:
            report.ended_at = Nyx.now().isoformat()
            report.duration_ms = (time.perf_counter() - start_t) * 1000.0
            hymn = polyhymnia.hymn()
            report.styx_total = hymn.total_oaths
            report.styx_intact = hymn.intact

        return report

    # ─────────────────────────────────────────────────────────
    # Public observability API
    # ─────────────────────────────────────────────────────────

    _on_phase = None  # type: ignore[assignment]

    def run_with_callback(self, on_phase) -> SessionReport:
        """Run + invoke on_phase(phase_name, detail, report) at each phase.
        The callback must not raise; if it does, the loop continues."""
        self._on_phase = on_phase
        try:
            return self.run()
        finally:
            self._on_phase = None

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

    def _observe_hydra(self, report: SessionReport) -> None:
        """HYDRA reads. Read-only by S3."""
        h = hydra.behead()
        report.hydra_findings = h.total
        report.hydra_alerts = len(h.alerts)
        report.hydra_drifts = len(h.drifts)
        report.hydra_by_head = {name: len(fs) for name, fs in h.by_head.items()}
        report.hydra_alert_details = [
            {"head": f.head, "slice": f.slice, "detail": f.detail}
            for f in h.alerts
        ]
        self._hydra_report = h

    def _observe_argos(self, report: SessionReport) -> None:
        """Argos scans. Deterministic by S2; decentralized by S4."""
        c = colony.deploy()
        report.argos_pheromones = c.count
        report.argos_by_eye = {name: len(ps) for name, ps in c.by_eye.items()}
        report.argos_alerts = sum(1 for p in c.pheromones if p.kind == "alert")
        report.argos_alert_details = [
            {"eye": p.eye, "slice": p.slice, "detail": p.detail}
            for p in c.pheromones if p.kind == "alert"
        ]
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
        report.brief_recommendation_text = list(brief.recommendations)
        report.brief_confidence = brief.confidence
        self._brief = brief

    def _correlate(self, report: SessionReport) -> None:
        """CorrelationEngine over the recent pheromone log — surfaces
        cross-eye patterns that no single Eye would see."""
        from olympus.monsters.argos.correlation import correlation
        from olympus.monsters.argos.colony import colony as _colony
        known_eyes = [e.NAME for e in _colony.eyes()]
        rep = correlation.correlate(window_hours=24.0, known_eyes=known_eyes)
        report.correlation_clusters = len(rep.clusters)
        report.correlation_cascades = len(rep.cascades)
        report.correlation_quiet = len(rep.quiet)
        # Compact summary for verbose render
        summary: list[str] = []
        for c in rep.clusters[:3]:
            summary.append(f"cluster: '{c.slice}' seen by {len(c.eyes)} eye(s) "
                           f"(intensity {c.intensity_sum:.1f})")
        for c in rep.cascades[:2]:
            summary.append(f"cascade: {c.leader} → {c.follower} ({c.instances}x)")
        for q in rep.quiet[:3]:
            summary.append(f"quiet: {q.eye} silent {q.hours_silent:.0f}h")
        report.correlation_summary = summary
        self._correlation = rep

    def _propose_and_contest(self, report: SessionReport) -> None:
        """Hephaestus surfaces proposals (brief + correlation); Momus contests."""
        proposals = hephaestus.surface_from(self._brief,
                                            correlation=self._correlation)
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
