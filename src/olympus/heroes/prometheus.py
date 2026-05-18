"""Prometheus — the Titan who stole fire and gave it to humanity.

In myth: forethought-bringer, champion of human improvement against
the will of Zeus. In Olympus: the agent that reads Hephaestus's
proposals and ACTS on the safe ones. Bounded by S7 — only LOW-risk
actions with zero Momus contests are eligible. Every action records
before/after to Mnemosyne so the change is reconstructible (S8).

Prometheus does not modify source code. He does not amend the
constitution. He performs the boring, safe maintenance that keeps
the substrate healthy:

    state-rotation        rotate a JSONL file that exceeded its cap
    brief-archive-compact prune briefs older than the recent window
    prophecy-graduate     mark a 5-times-accepted prediction as graduated
    prophecy-retire       mark a 3-times-rejected prediction as retired
    dead-eye-flag         flag an eye that hasn't emitted in 30 days

Each handler is a small function. New handlers are added by domain
deployments. The dispatch is by drift signature — same pattern
Hephaestus uses for rejection memory.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field, asdict
from typing import Callable, Any

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class ImprovementResult:
    """One run of a Prometheus handler."""
    handler: str
    action_id: str | None
    before: dict[str, Any] = field(default_factory=dict)
    after: dict[str, Any] = field(default_factory=dict)
    succeeded: bool = True
    detail: str = ""
    ran_at: str = ""

    def __post_init__(self) -> None:
        if not self.ran_at:
            self.ran_at = Nyx.now().isoformat()


@dataclass
class ImprovementReport:
    started_at: str
    ended_at: str = ""
    handlers_invoked: int = 0
    handlers_succeeded: int = 0
    results: list[ImprovementResult] = field(default_factory=list)


# A handler returns (before_state, after_state) or raises.
# Signature: handler(action: Action | None) -> tuple[dict, dict]
Handler = Callable[[Any], tuple[dict[str, Any], dict[str, Any]]]


class Prometheus:
    """The forethought-bringer. Reads ratified-LOW actions; dispatches
    to handlers; records before/after."""

    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}
        # Register the substrate-level handlers
        self.register("state-rotation", self._h_state_rotation)
        self.register("brief-archive-compact", self._h_brief_compact)
        self.register("prophecy-graduate", self._h_prophecy_graduate)
        self.register("prophecy-retire", self._h_prophecy_retire)
        self.register("dead-eye-flag", self._h_dead_eye_flag)

    # ─────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────

    def register(self, name: str, fn: Handler) -> None:
        """Register a handler under a name. Domain deployments call
        this to add their own."""
        self._handlers[name] = fn

    def handlers(self) -> list[str]:
        return sorted(self._handlers.keys())

    def improve(self) -> ImprovementReport:
        """Run one improvement pass. Each registered handler runs in
        the order it was registered; failures are caught and recorded;
        the loop continues. Returns a full report. Atlas bears the
        pass for its lifetime so `invoke shoulders` can show it."""
        from olympus.titans.atlas import atlas
        report = ImprovementReport(started_at=Nyx.now().isoformat())
        burden = atlas.bear(op="improvement-pass",
                            owner="prometheus",
                            handlers=list(self._handlers.keys()))
        try:
            for name, handler in self._handlers.items():
                result = self._invoke_one(name, handler, action=None)
                report.results.append(result)
                report.handlers_invoked += 1
                if result.succeeded:
                    report.handlers_succeeded += 1
            report.ended_at = Nyx.now().isoformat()

            mnemosyne.remember(
                kind="prometheus.pass",
                actor="prometheus",
                summary=(f"improvement pass: {report.handlers_succeeded}/"
                         f"{report.handlers_invoked} handler(s) succeeded"),
                handlers=[r.handler for r in report.results],
                succeeded=report.handlers_succeeded,
                invoked=report.handlers_invoked,
            )
            return report
        finally:
            outcome = ("ok" if report.handlers_succeeded ==
                       report.handlers_invoked else "partial")
            atlas.release(burden.id, outcome=outcome)

    def loop(self, *, interval_seconds: float = 600.0,
             max_iterations: int = -1) -> None:
        """Run improve() repeatedly. -1 iterations = forever (until
        KeyboardInterrupt)."""
        import time
        i = 0
        while max_iterations < 0 or i < max_iterations:
            i += 1
            self.improve()
            if max_iterations < 0 or i < max_iterations:
                time.sleep(interval_seconds)

    # ─────────────────────────────────────────────────────────
    # Internal: invoke one handler with before/after tracking
    # ─────────────────────────────────────────────────────────

    def _invoke_one(self, name: str, handler: Handler,
                    action: Any | None) -> ImprovementResult:
        action_id = getattr(action, "id", None) if action is not None else None
        try:
            before, after = handler(action)
            changed = before != after
            result = ImprovementResult(
                handler=name,
                action_id=action_id,
                before=before,
                after=after,
                succeeded=True,
                detail=("changed" if changed else "no-op"),
            )
        except Exception as exc:  # noqa: BLE001
            result = ImprovementResult(
                handler=name,
                action_id=action_id,
                succeeded=False,
                detail=f"raised: {type(exc).__name__}: {exc}",
            )

        # Record this handler's outcome
        mnemosyne.remember(
            kind="prometheus.handler",
            actor=f"prometheus:{name}",
            summary=f"{name}: {result.detail}",
            handler=name,
            succeeded=result.succeeded,
            before=result.before,
            after=result.after,
        )
        return result

    # ─────────────────────────────────────────────────────────
    # Built-in handlers — each is a small, safe transformation
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _h_state_rotation(action: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        """Rotate JSONL files in state/ that exceed 10k lines."""
        from olympus.primordials.gaia import root
        from olympus.runtime.persistence import rotate_jsonl

        state_dir = root.child("state")
        rotated: list[str] = []
        sizes_before: dict[str, int] = {}
        sizes_after: dict[str, int] = {}

        if state_dir.exists():
            for jsonl in state_dir.rglob("*.jsonl"):
                # don't rotate archive files themselves
                if "archive" in jsonl.name:
                    continue
                with jsonl.open("r", encoding="utf-8") as f:
                    lines = sum(1 for _ in f)
                sizes_before[jsonl.name] = lines
                if lines > 10_000:
                    archive = rotate_jsonl(jsonl, max_lines=10_000)
                    if archive is not None:
                        rotated.append(jsonl.name)
                with jsonl.open("r", encoding="utf-8") as f:
                    sizes_after[jsonl.name] = sum(1 for _ in f)
                # If we didn't rotate, before == after
                if jsonl.name not in [r for r in rotated]:
                    sizes_after[jsonl.name] = sizes_before[jsonl.name]

        return (
            {"sizes": sizes_before},
            {"sizes": sizes_after, "rotated": rotated},
        )

    @staticmethod
    def _h_brief_compact(action: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        """Move briefs older than the last 50 to an archive subdir."""
        from olympus.primordials.gaia import root

        briefs_dir = root.child("state", "athena")
        if not briefs_dir.exists():
            return ({"briefs": 0}, {"briefs": 0, "archived": 0})

        briefs = sorted(briefs_dir.glob("*.json"))
        before_count = len(briefs)
        if before_count <= 50:
            return (
                {"briefs": before_count},
                {"briefs": before_count, "archived": 0},
            )

        archive_dir = briefs_dir / "archive"
        archive_dir.mkdir(exist_ok=True)
        to_archive = briefs[:-50]
        for b in to_archive:
            target = archive_dir / b.name
            b.rename(target)

        after_count = before_count - len(to_archive)
        return (
            {"briefs": before_count},
            {"briefs": after_count, "archived": len(to_archive)},
        )

    @staticmethod
    def _h_prophecy_graduate(action: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        """Find predictions accepted ≥5 consecutive times — mark graduated."""
        before: dict[str, Any] = {"graduated": []}
        after: dict[str, Any] = {"graduated": []}

        # Group prophecy.verified by prediction name
        from collections import defaultdict
        history: dict[str, list[bool]] = defaultdict(list)
        for m in mnemosyne.recall("prophecy.verified"):
            name = m.body.get("prediction")
            accepted = m.body.get("accepted")
            if name and accepted is not None:
                history[name].append(bool(accepted))

        already = {
            m.body.get("prediction")
            for m in mnemosyne.recall("prophecy.graduated")
            if m.body.get("prediction")
        }
        before["graduated"] = sorted(already)

        graduated: list[str] = []
        for name, outcomes in history.items():
            if name in already:
                continue
            # last 5 outcomes must all be True
            if len(outcomes) >= 5 and all(outcomes[-5:]):
                mnemosyne.remember(
                    kind="prophecy.graduated",
                    actor="prometheus:prophecy-graduate",
                    summary=f"prophecy {name!r} accepted 5+ times consecutively",
                    prediction=name,
                )
                graduated.append(name)

        after["graduated"] = sorted(already | set(graduated))
        after["new_this_pass"] = graduated
        return (before, after)

    @staticmethod
    def _h_prophecy_retire(action: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        """Find predictions rejected ≥3 times — mark retired."""
        before: dict[str, Any] = {"retired": []}
        after: dict[str, Any] = {"retired": []}

        from collections import Counter
        rejection_count: Counter[str] = Counter()
        for m in mnemosyne.recall("prophecy.verified"):
            if m.body.get("accepted") is False:
                name = m.body.get("prediction")
                if name:
                    rejection_count[name] += 1

        already = {
            m.body.get("prediction")
            for m in mnemosyne.recall("prophecy.retired")
            if m.body.get("prediction")
        }
        before["retired"] = sorted(already)

        retired: list[str] = []
        for name, n in rejection_count.items():
            if name in already:
                continue
            if n >= 3:
                mnemosyne.remember(
                    kind="prophecy.retired",
                    actor="prometheus:prophecy-retire",
                    summary=f"prophecy {name!r} rejected {n} times — retired",
                    prediction=name,
                    rejection_count=n,
                )
                retired.append(name)

        after["retired"] = sorted(already | set(retired))
        after["new_this_pass"] = retired
        return (before, after)

    @staticmethod
    def _h_dead_eye_flag(action: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        """Flag any eye that has emitted INFO findings but never an ALERT
        for 30+ days. Surfaces as a recommendation, not a deletion."""
        from olympus.monsters.argos.colony import colony
        from olympus.titans.cronus import Cronus

        before = {"flagged_dead_eyes": []}
        after: dict[str, Any] = {"flagged_dead_eyes": [], "candidates": []}

        # Read recent pheromones via colony
        all_phers = colony.read_log()

        per_eye_age: dict[str, float] = {}
        per_eye_kinds: dict[str, set[str]] = {}
        for p in all_phers:
            age = Cronus.age_seconds(p.deposited_at) / 86400.0
            if p.eye not in per_eye_age or age < per_eye_age[p.eye]:
                per_eye_age[p.eye] = age
            per_eye_kinds.setdefault(p.eye, set()).add(p.kind)

        candidates: list[dict[str, Any]] = []
        already_flagged = {
            m.body.get("eye")
            for m in mnemosyne.recall("prometheus.dead-eye-flagged")
            if m.body.get("eye")
        }
        before["flagged_dead_eyes"] = sorted(already_flagged)

        for eye in colony.eyes():
            name = eye.NAME
            if name in already_flagged:
                continue
            age = per_eye_age.get(name)
            kinds = per_eye_kinds.get(name, set())
            # Eye has emitted ONLY info for 30+ days → flag
            if age is not None and age >= 30 and kinds <= {"info"}:
                mnemosyne.remember(
                    kind="prometheus.dead-eye-flagged",
                    actor="prometheus:dead-eye-flag",
                    summary=(f"eye {name!r} emitted only INFO for "
                             f"{age:.0f} day(s); flag for Zeus review"),
                    eye=name,
                    days_since_any_signal=age,
                )
                candidates.append({"eye": name, "days_info_only": age})

        after["candidates"] = candidates
        after["flagged_dead_eyes"] = sorted(
            already_flagged | {c["eye"] for c in candidates}
        )
        return (before, after)


prometheus = Prometheus()
