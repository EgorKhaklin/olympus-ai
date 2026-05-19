"""Asclepius — god of medicine and healing.

In myth: son of Apollo, taught medicine by the centaur Chiron. He
healed mortals so effectively that he raised the dead — Zeus killed
him with a thunderbolt to preserve the order of mortality. Among
healers, he is the singular master.

In Olympus, Asclepius is the **healer**: distinct from Hecate (single-
operation error recovery), Asclepius rebuilds *derived* state from
canonical sources. The Iris dashboard, the pantheon population
counts, the slice heatmap — all are derived; all can be rebuilt from
Mnemosyne plus the source filesystem.

Asclepius is a registry of healers (same pattern as Prometheus's
handler registry). Each healer is a small idempotent function that:

  - reads only from canonical sources (Mnemosyne, source files, state)
  - writes only to derived state (state/iris/, state/atlas/burdens,
    state/pan/state.json, derived JSONL caches)
  - is safe to run twice — second run is a no-op if state is healthy

Asclepius never edits source code, never modifies Mnemosyne, never
amends the constitution. Per Delphi 2026-05-18-compass-rose-arc.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Callable, Any

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class HealingResult:
    """One healer's outcome."""
    healer: str
    succeeded: bool
    detail: str = ""
    changed: bool = False
    healed_at: str = ""

    def __post_init__(self) -> None:
        if not self.healed_at:
            self.healed_at = Nyx.now().isoformat()


@dataclass
class HealingReport:
    started_at: str
    ended_at: str = ""
    healers_invoked: int = 0
    healers_succeeded: int = 0
    healers_changed: int = 0
    results: list[HealingResult] = field(default_factory=list)


# Healer signature — returns (succeeded, changed, detail) or raises.
Healer = Callable[[], tuple[bool, bool, str]]


class Asclepius:
    """The master healer. Heal registered components on demand."""

    def __init__(self) -> None:
        self._healers: dict[str, Healer] = {}
        # Register substrate-level healers
        self.register("iris-dashboard", self._h_iris)
        self.register("pan-state-validity", self._h_pan_state)
        self.register("atlas-burden-consistency", self._h_atlas)
        self.register("rhea-directory-structure", self._h_directories)
        # Per Delphi 2026-05-19-tartarus-arc.md
        self.register("atlas-test-burden-release", self._h_release_test)

    # ─────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────

    def register(self, name: str, fn: Healer) -> None:
        self._healers[name] = fn

    def healers(self) -> list[str]:
        return sorted(self._healers.keys())

    def heal(self) -> HealingReport:
        """Run every healer; report. Failures don't abort the pass."""
        report = HealingReport(started_at=Nyx.now().isoformat())
        for name, fn in self._healers.items():
            try:
                succeeded, changed, detail = fn()
                result = HealingResult(
                    healer=name, succeeded=bool(succeeded),
                    changed=bool(changed), detail=str(detail),
                )
            except Exception as exc:  # noqa: BLE001
                result = HealingResult(
                    healer=name, succeeded=False, changed=False,
                    detail=f"raised: {type(exc).__name__}: {exc}",
                )
            report.results.append(result)
            report.healers_invoked += 1
            if result.succeeded:
                report.healers_succeeded += 1
            if result.changed:
                report.healers_changed += 1

        report.ended_at = Nyx.now().isoformat()
        mnemosyne.remember(
            kind="asclepius.heal",
            actor="asclepius",
            summary=(f"healing pass: {report.healers_succeeded}/"
                     f"{report.healers_invoked} ok · "
                     f"{report.healers_changed} changed"),
            healers=[r.healer for r in report.results],
            succeeded=report.healers_succeeded,
            changed=report.healers_changed,
        )
        return report

    # ─────────────────────────────────────────────────────────
    # Built-in healers — each is small, idempotent, ground-touching
    # only on derived state.
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _h_iris() -> tuple[bool, bool, str]:
        """Rebuild the Iris dashboard from current substrate state.
        Always changed=True on first run; idempotent thereafter."""
        from olympus.iris import build
        out = build(open_in_browser=False)
        return (True, True, f"rebuilt {out.as_posix()}")

    @staticmethod
    def _h_pan_state() -> tuple[bool, bool, str]:
        """Validate Pan's state file; rewrite if corrupt or missing."""
        from olympus.olympians.pan import pan
        from dataclasses import asdict as _asdict
        import json
        state = pan.state()
        path = pan._state_path  # internal — healer privilege
        if not path.exists() or path.read_text(encoding="utf-8").strip() == "":
            path.write_text(json.dumps(_asdict(state), default=str, indent=2),
                            encoding="utf-8")
            return (True, True, "rewrote missing pan state file")
        return (True, False, f"pan state intact (panicked={state.panicked})")

    @staticmethod
    def _h_atlas() -> tuple[bool, bool, str]:
        """Force-evaluate Atlas burden consistency. If a bear has been
        in flight longer than 24h with no release, that's a hung
        burden — record a `asclepius.hung_burden` for operator
        attention. Does NOT auto-release (that would lie about state)."""
        from olympus.titans.atlas import atlas
        import datetime
        report = atlas.shoulders()
        now = Nyx.now()
        hung = []
        for b in report.current:
            try:
                started = datetime.datetime.fromisoformat(b.started_at)
                age_hours = (now - started).total_seconds() / 3600.0
            except (ValueError, TypeError):
                continue
            if age_hours > 24.0:
                hung.append({"id": b.id, "op": b.op, "owner": b.owner,
                             "age_hours": age_hours})
        if hung:
            mnemosyne.remember(
                kind="asclepius.hung_burden",
                actor="asclepius",
                summary=f"{len(hung)} burden(s) in flight > 24h",
                hung=hung,
            )
            return (True, True, f"{len(hung)} hung burden(s) flagged "
                                  f"(NOT auto-released)")
        return (True, False, f"{report.current_count} burden(s) in flight, "
                              f"all healthy")

    @staticmethod
    def _h_release_test() -> tuple[bool, bool, str]:
        """Release Atlas burdens whose owner is a test seed. Per Delphi
        2026-05-19-tartarus-arc.md: investigation found 100% of the
        substrate's reported 'in-flight' burdens were test residue
        (charon-test, asclepius-test, test-owner). They should NOT
        appear as production load. Each release is recorded individually
        so the audit trail is complete."""
        from olympus.titans.atlas import atlas
        from olympus.runtime.test_seeds import is_test_owner
        report = atlas.shoulders()
        released = 0
        kept_test = []  # release-failures we want to surface
        for b in report.current:
            if not is_test_owner(b.owner):
                continue
            try:
                atlas.release(b.id, outcome="asclepius:test-seed-cleanup")
                released += 1
            except Exception as exc:  # noqa: BLE001
                kept_test.append((b.id, str(exc)))
        if released or kept_test:
            mnemosyne.remember(
                kind="asclepius.test_burden_release",
                actor="asclepius",
                summary=(f"released {released} test-seed burden(s); "
                          f"{len(kept_test)} release-failures"),
                released=released,
                failures=kept_test[:20],
            )
        return (True, bool(released),
                f"released {released} test-seed burden(s)"
                + (f"; {len(kept_test)} failed" if kept_test else ""))

    @staticmethod
    def _h_directories() -> tuple[bool, bool, str]:
        """Rhea ensures directory structure. Re-run her."""
        from olympus.titans.rhea import rhea
        statuses = rhea.bring_forth()
        created = [k for k, v in statuses.items() if v != "extant"]
        if created:
            return (True, True, f"created/repaired: {', '.join(created)}")
        return (True, False, f"all {len(statuses)} dirs extant")


asclepius = Asclepius()
