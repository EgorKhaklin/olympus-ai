"""Pan — circuit breaker.

The claim being tested: Pan enters panic when violation rate exceeds
threshold; gate_ratification raises PanicError while panicked; clear()
restores; auto-clear works after quiet window; ratify is blocked.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import datetime
import pathlib
import tempfile
import unittest


def _fresh_pan(threshold: int = 3, window: float = 60.0,
               quiet: float = 0.0) -> "Pan":  # type: ignore
    from olympus.olympians.pan import Pan
    p = Pan(threshold=threshold, window_seconds=window, quiet_seconds=quiet)
    # Redirect state file to a tmp dir per test so we don't bleed
    p._state_path = pathlib.Path(tempfile.mkdtemp()) / "state.json"
    return p


def _seed_violations(n: int) -> None:
    from olympus.titans.mnemosyne import mnemosyne
    for i in range(n):
        mnemosyne.remember(
            kind="invariant.violated",
            actor="test:alecto",
            summary=f"seeded violation {i}",
            invariant_id="S1",
            evidence=None,
        )


class TestPan(unittest.TestCase):

    def test_calm_by_default(self):
        # Use a window so tiny that no seeded violation from other tests
        # in this run can count — only violations from the last 0.001s.
        p = _fresh_pan(threshold=3, window=0.001)
        s = p.evaluate()
        self.assertFalse(s.panicked)

    def test_enters_panic_above_threshold(self):
        p = _fresh_pan(threshold=3, window=3600.0)
        _seed_violations(4)
        s = p.evaluate()
        self.assertTrue(s.panicked)
        self.assertGreaterEqual(s.triggering_violations, 3)

    def test_guard_raises_when_panicked(self):
        from olympus.olympians.pan import PanicError
        p = _fresh_pan(threshold=2, window=3600.0)
        _seed_violations(3)
        p.evaluate()  # enter panic
        with self.assertRaises(PanicError):
            p.guard_ratification(action_id="test-act-1")

    def test_clear_restores(self):
        p = _fresh_pan(threshold=2, window=3600.0)
        _seed_violations(3)
        p.evaluate()
        self.assertTrue(p.state().panicked)
        cleared = p.clear(by="test", reason="unit-test cleanup")
        self.assertFalse(cleared.panicked)
        self.assertFalse(p.state().panicked)
        # Guard now allows again — but only if violations have aged out
        # of the window OR Pan respects the cleared state. Pan's
        # evaluate() will re-panic if violations are still in window.
        # That's CORRECT behavior — clear is a manual override but the
        # underlying condition persists. Test the manual-state path:
        self.assertFalse(cleared.panicked)

    def test_auto_clear_after_quiet_window(self):
        """When quiet_seconds=0 (effectively immediate), a tick with
        n=0 violations auto-clears."""
        from olympus.titans.mnemosyne import mnemosyne
        p = _fresh_pan(threshold=2, window=0.01, quiet=0.0)
        # Seed violations and enter panic
        _seed_violations(3)
        p.evaluate()
        self.assertTrue(p.state().panicked)
        # Wait so the violations age out of the (very small) window
        import time as _t
        _t.sleep(0.05)
        # Now no recent violations — should auto-clear
        s2 = p.evaluate()
        self.assertFalse(s2.panicked)

    def test_action_queue_ratify_refused_during_panic(self):
        """The ratification path actually consults Pan."""
        from olympus.action import action_queue
        from olympus.olympians.pan import pan, PanicError
        # Enter panic via singleton (use a high threshold so seeded
        # violations are decisive; window is 5min so recent count matters)
        # Force-set Pan's state to panicked directly via clear+manual
        from olympus.olympians.pan import PanicState
        pan._write_state(PanicState(
            panicked=True,
            entered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            last_transition_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            detail="forced panic for test",
        ))
        try:
            # Drop a queued action; try to ratify; expect refusal
            from olympus.action import Action
            import time as _t
            action_id = f"pan-test-{_t.time_ns()}"
            queued = Action(
                id=action_id, proposal_id="pan-test",
                risk_class="LOW", summary="test panic guard",
                status="queued",
            )
            from dataclasses import asdict
            action_queue._append(asdict(queued))
            with self.assertRaises(PanicError):
                action_queue.ratify(action_id, quote="test")
        finally:
            pan.clear(by="test", reason="cleanup")


if __name__ == "__main__":
    unittest.main()
