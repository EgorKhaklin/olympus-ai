"""Hygieia — daughter of Asclepius, goddess of health and well-being.

In myth: daughter of Asclepius (the healer) and Epione; personification
of health, cleanliness, and the maintenance of well-being. Where
Asclepius cured the sick, Hygieia kept the healthy *healthy*.

In Olympus, Hygieia is the **whole-substrate cohesion checker**.
Asclepius rebuilds derived state. Hygieia asks the deeper question:
*"are the modules' views of the world still consistent with each
other?"* Cross-module checks that would fall through any single
module's responsibility:

  - **Pan ↔ recent invariants:** Pan's panicked-state vs the actual
    rate of `invariant.violated` in the last window
  - **Atlas ↔ session.completed:** burden count vs unreleased sessions
  - **Daedalus ↔ disk:** every `_COGNITIVE_FLOW` node exists as a module
  - **Plato ↔ disk:** classified figures exist; on-disk figures are
    classified
  - **Themis ↔ records:** recent records pass their JSON Schemas
  - **Charon ↔ Atlas:** burdens released > retention should have been
    ferried

Each check returns a HygieiaFinding. Non-`well` findings become
candidate Hephaestus proposals — Hygieia never directly fixes; she
reports.

Per Delphi 2026-05-18-aegis-arc.md.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field, asdict
from typing import Any

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class HygieiaFinding:
    """One wellness check's outcome."""
    check: str
    status: str               # 'well' | 'warning' | 'incoherent'
    detail: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class WellnessReport:
    started_at: str
    ended_at: str = ""
    findings: list[HygieiaFinding] = field(default_factory=list)

    @property
    def well_count(self) -> int:
        return sum(1 for f in self.findings if f.status == "well")

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.status == "warning")

    @property
    def incoherent_count(self) -> int:
        return sum(1 for f in self.findings if f.status == "incoherent")


# ─────────────────────────────────────────────────────────
# Hygieia
# ─────────────────────────────────────────────────────────


class Hygieia:
    """Cross-module wellness. Reports, never auto-fixes."""

    def check(self) -> WellnessReport:
        """Run every registered check. Returns the report."""
        report = WellnessReport(started_at=Nyx.now().isoformat())

        report.findings.append(self._check_pan_vs_invariants())
        report.findings.append(self._check_atlas_vs_sessions())
        report.findings.append(self._check_daedalus_vs_disk())
        report.findings.append(self._check_plato_vs_disk())
        report.findings.append(self._check_themis_vs_records())
        report.findings.append(self._check_charon_backlog())

        report.ended_at = Nyx.now().isoformat()
        mnemosyne.remember(
            kind="hygieia.check",
            actor="hygieia",
            summary=(f"wellness pass: {report.well_count} well, "
                     f"{report.warning_count} warning, "
                     f"{report.incoherent_count} incoherent"),
            well=report.well_count,
            warnings=report.warning_count,
            incoherent=report.incoherent_count,
            findings=[asdict(f) for f in report.findings],
        )
        return report

    # ─────────────────────────────────────────────────────────
    # Individual checks
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _check_pan_vs_invariants() -> HygieiaFinding:
        """Pan's persisted state should reflect the recent invariant
        rate. If Pan says calm but invariants are firing fast, that's
        incoherent."""
        from olympus.olympians.pan import pan
        state = pan.state()
        # Count invariants in the last Pan window (defaults to 300s)
        window = pan.window_seconds
        cutoff = Nyx.now() - datetime.timedelta(seconds=window)
        recent = [
            m for m in mnemosyne.recall("invariant.violated")
            if Hygieia._parse(m.remembered_at) and
               Hygieia._parse(m.remembered_at) >= cutoff
        ]
        recent_count = len(recent)
        threshold = pan.threshold

        if state.panicked and recent_count == 0:
            return HygieiaFinding(
                check="pan-vs-invariants",
                status="warning",
                detail=(f"Pan panicked but no invariants fired in last "
                        f"{window:.0f}s — may need clear"),
                evidence={"panicked": True, "recent_count": 0,
                          "threshold": threshold},
            )
        if not state.panicked and recent_count > threshold * 2:
            return HygieiaFinding(
                check="pan-vs-invariants",
                status="incoherent",
                detail=(f"Pan calm but {recent_count} invariants fired "
                        f"in last {window:.0f}s (threshold {threshold})"),
                evidence={"panicked": False, "recent_count": recent_count,
                          "threshold": threshold},
            )
        return HygieiaFinding(
            check="pan-vs-invariants",
            status="well",
            detail=(f"Pan {'panicked' if state.panicked else 'calm'} · "
                    f"{recent_count} recent invariants (threshold {threshold})"),
            evidence={"panicked": state.panicked,
                      "recent_count": recent_count,
                      "threshold": threshold},
        )

    @staticmethod
    def _check_atlas_vs_sessions() -> HygieiaFinding:
        """Atlas current burdens should be a subset of sessions whose
        completion is not yet recorded. If Atlas has 'session' burdens
        whose session_id appears in session.completed, that's stale."""
        from olympus.titans.atlas import atlas
        shoulders = atlas.shoulders()
        session_burdens = [b for b in shoulders.current
                            if b.op == "session"]
        completed_ids = {
            (m.body or {}).get("session_id", "")
            for m in mnemosyne.recall("session.completed")
        }
        stale = [b for b in session_burdens if b.owner in completed_ids]
        if stale:
            return HygieiaFinding(
                check="atlas-vs-sessions",
                status="incoherent",
                detail=(f"{len(stale)} Atlas session burden(s) are "
                        f"stale — their session.completed exists"),
                evidence={"stale_burdens": [b.id for b in stale]},
            )
        return HygieiaFinding(
            check="atlas-vs-sessions",
            status="well",
            detail=(f"{shoulders.current_count} burden(s) in flight; "
                    f"none stale against session.completed"),
            evidence={"in_flight": shoulders.current_count},
        )

    @staticmethod
    def _check_daedalus_vs_disk() -> HygieiaFinding:
        """Every node in Daedalus's _COGNITIVE_FLOW should correspond
        to a known module. The check is approximate (names like
        'ActionQueue' don't have a module — they're concepts)."""
        from olympus.heroes.daedalus import Daedalus
        from olympus.primordials.gaia import root as _root
        nodes = set()
        for src, dst, _ in Daedalus._COGNITIVE_FLOW:
            nodes.add(src.lower())
            nodes.add(dst.lower())
        # Strip plural / non-figure names — names with capitals like
        # ActionQueue / CorrelationEngine are concepts, not modules
        candidates = {n for n in nodes
                       if n.isalpha() or "-" not in n and "." not in n}
        # Resolve against disk
        known_figures = set()
        for tier in ("primordials", "titans", "olympians", "underworld",
                     "fates", "furies", "graces", "muses", "heroes",
                     "monsters"):
            tier_path = _root.child("src", "olympus", tier)
            if tier_path.exists():
                for p in tier_path.iterdir():
                    if p.is_file() and p.suffix == ".py":
                        known_figures.add(p.stem)
                    elif p.is_dir() and not p.name.startswith("_"):
                        known_figures.add(p.name)
        # Concepts that are NOT modules but are valid graph nodes
        non_module_nodes = {"actionqueue", "session", "correlationengine",
                            "architecturemd", "wisdom"}
        unresolved = candidates - known_figures - non_module_nodes
        if unresolved:
            return HygieiaFinding(
                check="daedalus-vs-disk",
                status="warning",
                detail=(f"{len(unresolved)} _COGNITIVE_FLOW node(s) "
                        f"don't resolve to known modules"),
                evidence={"unresolved": sorted(unresolved)},
            )
        return HygieiaFinding(
            check="daedalus-vs-disk",
            status="well",
            detail=(f"all {len(candidates)} graph nodes resolve to "
                    f"modules or known concepts"),
            evidence={"node_count": len(candidates)},
        )

    @staticmethod
    def _check_plato_vs_disk() -> HygieiaFinding:
        """Plato's taxonomy should reference real modules. Figures on
        disk should be classified."""
        from olympus.heroes.plato import _FIGURE_TO_SOLID
        from olympus.primordials.gaia import root as _root
        known_figures = set()
        for tier in ("primordials", "titans", "olympians", "underworld",
                     "fates", "furies", "graces", "muses", "heroes",
                     "monsters"):
            tier_path = _root.child("src", "olympus", tier)
            if tier_path.exists():
                for p in tier_path.iterdir():
                    if p.is_file() and p.suffix == ".py" \
                       and not p.name.startswith("_"):
                        known_figures.add(p.stem)
                    elif p.is_dir() and not p.name.startswith("_"):
                        known_figures.add(p.name)
        classified = set(_FIGURE_TO_SOLID.keys())
        unclassified_on_disk = known_figures - classified
        classified_but_gone = classified - known_figures
        problems = []
        if unclassified_on_disk:
            problems.append(f"{len(unclassified_on_disk)} on-disk "
                             f"figures missing from taxonomy")
        if classified_but_gone:
            problems.append(f"{len(classified_but_gone)} taxonomy "
                             f"entries with no on-disk module")
        if problems:
            return HygieiaFinding(
                check="plato-vs-disk",
                status="warning",
                detail="; ".join(problems),
                evidence={
                    "unclassified_on_disk": sorted(unclassified_on_disk),
                    "classified_but_gone": sorted(classified_but_gone),
                },
            )
        return HygieiaFinding(
            check="plato-vs-disk",
            status="well",
            detail=(f"all {len(known_figures)} on-disk figures "
                    f"classified by Plato"),
            evidence={"figures": len(known_figures)},
        )

    @staticmethod
    def _check_themis_vs_records() -> HygieiaFinding:
        """Recent records should pass their JSON Schemas (sample one
        per kind that has a schema, validate the latest record)."""
        from olympus.titans.themis import themis
        schemas = themis.kinds_with_schemas()
        problems: list[str] = []
        for hyphenated in schemas:
            dotted = hyphenated.replace("-", ".")
            recs = mnemosyne.recall(dotted)
            if not recs:
                continue
            errs = themis.validate_record(dotted, recs[-1].body or {})
            if errs:
                problems.append(f"{dotted}: {errs[0]}")
        if problems:
            return HygieiaFinding(
                check="themis-vs-records",
                status="incoherent",
                detail=f"{len(problems)} recent record(s) fail schema",
                evidence={"failures": problems},
            )
        return HygieiaFinding(
            check="themis-vs-records",
            status="well",
            detail=(f"latest records pass all {len(schemas)} "
                    f"registered per-kind schemas"),
            evidence={"schemas_checked": len(schemas)},
        )

    @staticmethod
    def _check_charon_backlog() -> HygieiaFinding:
        """Are there released Atlas burdens older than Charon's
        retention that haven't been ferried?"""
        from olympus.underworld.charon import charon
        bears = mnemosyne.recall("atlas.bear")
        releases = mnemosyne.recall("atlas.release")
        release_by_id: dict[str, str] = {}
        for r in releases:
            body = r.body or {}
            rid = body.get("id")
            if rid:
                release_by_id[rid] = body.get("released_at",
                                               r.remembered_at)
        already_ferried = {
            (m.body or {}).get("burden_id", "")
            for m in mnemosyne.recall("charon.crossing")
        }
        cutoff = Nyx.now() - datetime.timedelta(
            days=charon.retention_days)
        backlog = 0
        for b in bears:
            body = b.body or {}
            bid = body.get("id", "")
            rel_ts = release_by_id.get(bid)
            if not rel_ts or bid in already_ferried:
                continue
            rel_dt = Hygieia._parse(rel_ts)
            if rel_dt and rel_dt < cutoff:
                backlog += 1
        if backlog > 0:
            return HygieiaFinding(
                check="charon-backlog",
                status="warning",
                detail=(f"{backlog} released burden(s) older than "
                        f"{charon.retention_days} days await ferrying"),
                evidence={"backlog": backlog,
                          "retention_days": charon.retention_days},
            )
        return HygieiaFinding(
            check="charon-backlog",
            status="well",
            detail="no ferrying backlog",
            evidence={"retention_days": charon.retention_days},
        )

    # ─────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _parse(ts: str) -> datetime.datetime | None:
        try:
            return datetime.datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return None


hygieia = Hygieia()
