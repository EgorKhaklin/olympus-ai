"""Pan — god of the wild, shepherds, and panic.

The word "panic" comes from Pan's name. He could induce sudden,
contagious fear in herds and armies — a panic — by his cry. In
Olympus, Pan is the circuit breaker.

When the Furies report invariant violations faster than a configurable
threshold (default: 3 violations in 5 minutes), Pan **enters panic
state**. While in panic:

  - new action ratifications are refused (Pan throws PanicError)
  - the self-improvement loop pauses non-essential work
  - the operator is signaled (via Mnemosyne and via the daemon log)

Recovery is either explicit (operator clears) or automatic (the
violation rate drops below threshold for a quiet window). Every
transition records to Mnemosyne under `kind="pan.transition"`.

Pan is read-mostly: he observes the violation stream and writes only
state transitions. He does not edit source, modify the constitution,
or take any action other than refusing ratification while panicked.

Per Delphi 2026-05-18-compass-rose-arc.md (zero Momus dings).
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, asdict
from typing import Any

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


class PanicError(RuntimeError):
    """Raised when an action is attempted while Pan is in panic state."""
    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


@dataclass
class PanicState:
    """Current state of the circuit breaker."""
    panicked: bool
    entered_at: str = ""
    last_transition_at: str = ""
    triggering_violations: int = 0
    window_seconds: float = 0.0
    detail: str = ""
    # Violations recorded at or before this ts are 'acknowledged' and
    # do not count toward future panic. Set by clear(); read by
    # evaluate(). Lets an operator say "I saw those, move on."
    acknowledged_through: str = ""


# ─────────────────────────────────────────────────────────
# Pan
# ─────────────────────────────────────────────────────────


class Pan:
    """The wild-god circuit breaker."""

    # Defaults — overridable per instance for tests
    DEFAULT_THRESHOLD = 3
    DEFAULT_WINDOW_SECONDS = 300.0
    DEFAULT_QUIET_SECONDS = 600.0   # auto-clear after N quiet seconds
    STATE_FILE = "state/pan/state.json"

    def __init__(self,
                 threshold: int | None = None,
                 window_seconds: float | None = None,
                 quiet_seconds: float | None = None) -> None:
        self.threshold = threshold if threshold is not None else self.DEFAULT_THRESHOLD
        self.window_seconds = (window_seconds if window_seconds is not None
                               else self.DEFAULT_WINDOW_SECONDS)
        self.quiet_seconds = (quiet_seconds if quiet_seconds is not None
                              else self.DEFAULT_QUIET_SECONDS)
        self._state_path = root.child(*self.STATE_FILE.split("/"))
        self._state_path.parent.mkdir(parents=True, exist_ok=True)

    # ─────────────────────────────────────────────────────────
    # State persistence — single JSON file (state, not audit)
    # ─────────────────────────────────────────────────────────

    def _read_state(self) -> PanicState:
        if not self._state_path.exists():
            return PanicState(panicked=False)
        import json
        try:
            d = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return PanicState(panicked=False)
        return PanicState(**d)

    def _write_state(self, s: PanicState) -> None:
        import json
        self._state_path.write_text(
            json.dumps(asdict(s), default=str, indent=2),
            encoding="utf-8",
        )

    # ─────────────────────────────────────────────────────────
    # Observe — count recent violations
    # ─────────────────────────────────────────────────────────

    def _recent_violations(self, *, now: datetime.datetime | None = None
                            ) -> list[Any]:
        if now is None:
            now = Nyx.now()
        cutoff = now - datetime.timedelta(seconds=self.window_seconds)
        # Acknowledged-through: any violations at or before this ts are
        # treated as resolved (operator clear). Subsequent ones still
        # count.
        ack = self._read_state().acknowledged_through
        ack_dt: datetime.datetime | None = None
        if ack:
            try:
                ack_dt = datetime.datetime.fromisoformat(ack)
            except (ValueError, TypeError):
                ack_dt = None
        out = []
        for m in mnemosyne.recall("invariant.violated"):
            try:
                ts = datetime.datetime.fromisoformat(m.remembered_at)
            except (ValueError, TypeError):
                continue
            if ts < cutoff:
                continue
            if ack_dt is not None and ts <= ack_dt:
                continue
            out.append(m)
        return out

    # ─────────────────────────────────────────────────────────
    # Evaluate — read violations, update state if needed
    # ─────────────────────────────────────────────────────────

    def evaluate(self) -> PanicState:
        """Read the current violation stream; transition into or out
        of panic as needed; return the post-evaluation state."""
        now = Nyx.now()
        recent = self._recent_violations(now=now)
        n = len(recent)

        state = self._read_state()

        if not state.panicked and n >= self.threshold:
            # ENTER panic
            state = PanicState(
                panicked=True,
                entered_at=now.isoformat(),
                last_transition_at=now.isoformat(),
                triggering_violations=n,
                window_seconds=self.window_seconds,
                detail=(f"{n} invariant violations in last "
                        f"{self.window_seconds:.0f}s exceeded threshold "
                        f"{self.threshold}"),
            )
            self._write_state(state)
            mnemosyne.remember(
                kind="pan.transition",
                actor="pan",
                summary=f"PANIC entered — {state.detail}",
                **asdict(state),
                transition="enter",
            )
            return state

        if state.panicked and n == 0:
            # Quiet enough to auto-clear?
            try:
                entered = datetime.datetime.fromisoformat(
                    state.last_transition_at or state.entered_at,
                )
                quiet_for = (now - entered).total_seconds()
            except (ValueError, TypeError):
                quiet_for = 0
            if quiet_for >= self.quiet_seconds:
                cleared = PanicState(
                    panicked=False,
                    last_transition_at=now.isoformat(),
                    detail=f"auto-cleared after {quiet_for:.0f}s quiet",
                )
                self._write_state(cleared)
                mnemosyne.remember(
                    kind="pan.transition",
                    actor="pan",
                    summary=f"PANIC cleared — {cleared.detail}",
                    **asdict(cleared),
                    transition="auto-clear",
                )
                return cleared

        return state

    # ─────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────

    def state(self) -> PanicState:
        """Return the current persisted state (does not re-evaluate)."""
        return self._read_state()

    def is_panicked(self) -> bool:
        """Convenience predicate. Re-evaluates first so callers see
        a fresh answer."""
        return self.evaluate().panicked

    def clear(self, *, by: str = "operator",
              reason: str = "operator cleared") -> PanicState:
        """Operator-initiated panic clear. Sets acknowledged_through =
        now, so violations recorded up to this moment no longer count.
        New violations after now DO count toward future panic."""
        now = Nyx.now()
        cleared = PanicState(
            panicked=False,
            last_transition_at=now.isoformat(),
            detail=f"cleared by {by}: {reason}",
            acknowledged_through=now.isoformat(),
        )
        self._write_state(cleared)
        mnemosyne.remember(
            kind="pan.transition",
            actor="pan",
            summary=f"PANIC cleared by {by} — {reason}",
            **asdict(cleared),
            transition="manual-clear",
            cleared_by=by,
        )
        return cleared

    def guard_ratification(self, *, action_id: str = "") -> None:
        """Called from the ratification path. Raises PanicError if Pan
        is in panic state. The operator must explicitly `invoke panic
        --clear` to ratify during a panic."""
        state = self.evaluate()
        if state.panicked:
            raise PanicError(
                f"ratification refused — Pan is in panic state "
                f"(entered {state.entered_at[:19]}; {state.detail}). "
                f"Run `invoke panic --clear` after addressing the cause."
            )


pan = Pan()
