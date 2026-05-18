"""Metis — Titaness of wise counsel, first wife of Zeus, mother of Athena.

In myth: Zeus was warned that any child Metis bore would surpass him in
wisdom. He swallowed her whole so that her counsel would always live
inside him. Athena then sprang fully-armed from his head — wisdom
*through* the swallowed Metis, *as* Athena.

In Olympus, Metis is the **self-tuning advisor**. She observes outcomes
— Epimetheus hindsights, Cassandra vindications, daemon iteration
statistics — and produces *recommendations* about substrate parameters:

  - Pan's panic threshold and window
  - Charon's archive retention window
  - Daemon iteration interval
  - Asclepius's healer order (heuristic priority)

**Metis never directly tunes.** Her recommendations are emitted as
Hephaestus-style proposals that go through the standard pipeline:
Momus contests them, Delphi records strategic decisions, Zeus
ratifies. The recursive loop is *bounded by the same constitutional
discipline* as every other change. This is the meta-meta layer: the
substrate proposes tweaks to itself, but the discipline of bounded
autonomy still gates them.

Re-arguing the prior refusal. The missing-figures arc refused Metis on
AP8 ("duplicates Athena's pre-synthesis"). The new role is *outcome-
driven parameter tuning of the substrate itself* — concrete, load-
bearing, and distinct from Athena's per-session brief composition.

Per Delphi 2026-05-18-recursion-arc.md.
"""
from __future__ import annotations

import datetime
import json
from dataclasses import dataclass, field, asdict
from typing import Any

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class Recommendation:
    """One Metis recommendation — a proposed parameter change."""
    parameter: str            # e.g. 'pan.threshold' or 'charon.retention_days'
    current: Any              # current value (if observable)
    proposed: Any             # what Metis suggests
    rationale: str            # why
    confidence: float = 0.5   # 0.0–1.0; higher = stronger evidence
    risk_class: str = "LOW"   # LOW / MEDIUM / HIGH per S7
    evidence_kinds: list[str] = field(default_factory=list)


@dataclass
class TuningReport:
    started_at: str
    ended_at: str = ""
    lookback_hours: float = 168.0   # one week of evidence by default
    recommendations: list[Recommendation] = field(default_factory=list)
    proposals_raised: int = 0

    @property
    def total(self) -> int:
        return len(self.recommendations)


# ─────────────────────────────────────────────────────────
# Helpers — read evidence from Mnemosyne with a lookback
# ─────────────────────────────────────────────────────────


def _within(ts: str, cutoff: datetime.datetime | None) -> bool:
    if cutoff is None:
        return True
    try:
        dt = datetime.datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return False
    return dt >= cutoff


def _recent(kind: str, *, cutoff: datetime.datetime | None) -> list[Any]:
    return [m for m in mnemosyne.recall(kind)
            if _within(m.remembered_at, cutoff)]


# ─────────────────────────────────────────────────────────
# Metis
# ─────────────────────────────────────────────────────────


class Metis:
    """The swallowed counsel. Observes outcomes; advises parameters."""

    def advise(self, *,
               lookback_hours: float = 168.0,
               raise_proposals: bool = True) -> TuningReport:
        """Run one tuning pass. lookback_hours = how far back to look at
        evidence. If raise_proposals=True, recommendations are also
        written as Hephaestus-channel proposals so they enter the
        standard Momus + Delphi review."""
        report = TuningReport(
            started_at=Nyx.now().isoformat(),
            lookback_hours=lookback_hours,
        )
        cutoff: datetime.datetime | None = None
        if lookback_hours > 0:
            cutoff = Nyx.now() - datetime.timedelta(hours=lookback_hours)

        # Evidence
        hindsights = _recent("epimetheus.hindsight", cutoff=cutoff)
        vindications = _recent("cassandra.vindicated", cutoff=cutoff)
        pan_transitions = _recent("pan.transition", cutoff=cutoff)
        # daemon.log is NOT in Mnemosyne; read it directly
        daemon_iterations = _read_daemon_iterations(cutoff=cutoff)

        report.recommendations.extend(self._advise_pan(
            pan_transitions=pan_transitions,
            daemon_iterations=daemon_iterations,
        ))
        report.recommendations.extend(self._advise_charon(
            hindsights=hindsights,
        ))
        report.recommendations.extend(self._advise_daemon_interval(
            daemon_iterations=daemon_iterations,
        ))
        report.recommendations.extend(self._advise_prometheus_priority(
            hindsights=hindsights,
            vindications=vindications,
        ))

        # Raise as proposals (so Momus contests; Zeus ratifies)
        if raise_proposals:
            report.proposals_raised = self._raise_proposals(
                report.recommendations,
            )

        mnemosyne.remember(
            kind="metis.advice",
            actor="metis",
            summary=(f"tuning pass: {report.total} recommendation(s); "
                     f"{report.proposals_raised} raised as proposals"),
            recommendations=[asdict(r) for r in report.recommendations],
            proposals_raised=report.proposals_raised,
            lookback_hours=lookback_hours,
        )
        report.ended_at = Nyx.now().isoformat()
        return report

    # ─────────────────────────────────────────────────────────
    # Per-parameter advisors — each emits 0 or more Recommendations
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _advise_pan(*, pan_transitions: list[Any],
                    daemon_iterations: list[dict]) -> list[Recommendation]:
        """If panic events happen frequently, the window may be too
        wide or the threshold too low. If they never happen but
        invariants do fire occasionally, the threshold is fine."""
        enters = [t for t in pan_transitions
                  if (t.body or {}).get("transition") == "enter"]
        recs: list[Recommendation] = []
        if len(enters) >= 5:
            recs.append(Recommendation(
                parameter="pan.threshold",
                current=3,
                proposed=5,
                rationale=(f"{len(enters)} panic-entries in the lookback "
                           f"window suggests the threshold is too "
                           f"sensitive; raise from 3 → 5"),
                confidence=min(0.5 + 0.05 * len(enters), 0.9),
                risk_class="LOW",
                evidence_kinds=["pan.transition"],
            ))
        # If daemon was skipping a lot due to panic, propose a wider
        # window so transient bursts don't trigger as easily.
        skipped = sum(1 for i in daemon_iterations
                      if i.get("event") == "daemon.skipped")
        if skipped >= 10:
            recs.append(Recommendation(
                parameter="pan.window_seconds",
                current=300.0,
                proposed=600.0,
                rationale=(f"{skipped} daemon iterations skipped due to "
                           f"panic state in the lookback; widening the "
                           f"window to 600s makes the breaker less "
                           f"sensitive to short bursts"),
                confidence=0.6,
                risk_class="LOW",
                evidence_kinds=["daemon.iteration"],
            ))
        return recs

    @staticmethod
    def _advise_charon(*, hindsights: list[Any]) -> list[Recommendation]:
        """If many hindsights surface old hung-burden flags, retention
        is too long. If none surface, retention may be fine or too short."""
        hung_flags = sum(1 for h in hindsights
                         if "hung" in (h.body or {}).get("lesson", "").lower())
        if hung_flags >= 3:
            return [Recommendation(
                parameter="charon.retention_days",
                current=30.0,
                proposed=14.0,
                rationale=(f"{hung_flags} hindsights mention hung burdens; "
                           f"shortening retention to 14 days lets Charon "
                           f"sweep them sooner"),
                confidence=0.6,
                risk_class="LOW",
                evidence_kinds=["epimetheus.hindsight"],
            )]
        return []

    @staticmethod
    def _advise_daemon_interval(*,
                                 daemon_iterations: list[dict]
                                 ) -> list[Recommendation]:
        """If iteration duration is consistently > 50% of interval, the
        loop is hot — consider widening the interval. If << 1% — the
        interval may be wider than needed."""
        completed = [i for i in daemon_iterations
                     if i.get("event") == "daemon.iteration"
                     and i.get("duration_ms") is not None]
        if len(completed) < 5:
            return []
        avg_ms = sum(i["duration_ms"] for i in completed) / len(completed)
        # daemon.start records the configured interval
        starts = [i for i in daemon_iterations
                  if i.get("event") == "daemon.start"]
        if not starts:
            return []
        last_interval_seconds = float(starts[-1].get("interval_seconds", 600))
        last_interval_ms = last_interval_seconds * 1000.0
        ratio = avg_ms / last_interval_ms if last_interval_ms > 0 else 0.0

        if ratio > 0.5:
            return [Recommendation(
                parameter="daemon.interval_seconds",
                current=last_interval_seconds,
                proposed=last_interval_seconds * 2.0,
                rationale=(f"avg iteration duration ({avg_ms:.0f}ms) is "
                           f"{ratio:.0%} of interval "
                           f"({last_interval_seconds}s); doubling the "
                           f"interval gives the loop breathing room"),
                confidence=0.7,
                risk_class="LOW",
                evidence_kinds=["daemon.iteration"],
            )]
        return []

    @staticmethod
    def _advise_prometheus_priority(*,
                                    hindsights: list[Any],
                                    vindications: list[Any]
                                    ) -> list[Recommendation]:
        """If a Prometheus handler consistently fails (surfaces in
        hindsights as 'handler raised'), Metis advises adding a
        precondition or retiring the handler."""
        failures: dict[str, int] = {}
        for h in hindsights:
            body = h.body or {}
            if body.get("subject_kind") == "handler" and body.get("surprising"):
                handler_name = body.get("subject_id", "")
                if handler_name:
                    failures[handler_name] = failures.get(handler_name, 0) + 1
        recs: list[Recommendation] = []
        for handler, n in failures.items():
            if n >= 5:
                recs.append(Recommendation(
                    parameter=f"prometheus.handler.{handler}",
                    current="active",
                    proposed="gated_or_retired",
                    rationale=(f"handler {handler!r} failed {n} times in "
                               f"lookback; either add a precondition or "
                               f"retire it"),
                    confidence=min(0.4 + 0.1 * n, 0.95),
                    risk_class="MEDIUM",
                    evidence_kinds=["epimetheus.hindsight"],
                ))
        return recs

    # ─────────────────────────────────────────────────────────
    # Raise recommendations as Hephaestus-channel proposals
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _raise_proposals(recommendations: list[Recommendation]) -> int:
        """Convert each recommendation into a proposal JSON file under
        state/hephaestus/proposals/. The standard pipeline picks them
        up: Hephaestus reviews, Momus contests, Zeus ratifies."""
        if not recommendations:
            return 0
        proposals_dir = root.child("state", "hephaestus", "proposals")
        proposals_dir.mkdir(parents=True, exist_ok=True)
        n = 0
        ts = Nyx.now().strftime("%Y%m%dT%H%M%SZ")
        for i, rec in enumerate(recommendations):
            pid = f"metis-{ts}-{i:02d}-{rec.parameter.replace('.', '_')}"
            payload = {
                "id": pid,
                "drift_observed": (
                    f"metis recommends tuning slice '{rec.parameter}': "
                    f"{rec.rationale}"
                ),
                "risk_class": rec.risk_class,
                "proposed_fix": {
                    "parameter": rec.parameter,
                    "from": rec.current,
                    "to": rec.proposed,
                },
                "confidence": rec.confidence,
                "raised_by": "metis",
                "raised_at": Nyx.now().isoformat(),
                "evidence_kinds": rec.evidence_kinds,
            }
            target = proposals_dir / f"{pid}.json"
            target.write_text(json.dumps(payload, indent=2, default=str),
                              encoding="utf-8")
            n += 1
        return n


# ─────────────────────────────────────────────────────────
# Daemon-log reader — not in Mnemosyne
# ─────────────────────────────────────────────────────────


def _read_daemon_iterations(*,
                             cutoff: datetime.datetime | None
                             ) -> list[dict]:
    """Read state/daemon.log lines as JSON; filter by ts >= cutoff."""
    path = root.child("state", "daemon.log")
    if not path.exists():
        return []
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = row.get("ts", "")
            if cutoff is None or _within(ts, cutoff):
                out.append(row)
    return out


metis = Metis()
