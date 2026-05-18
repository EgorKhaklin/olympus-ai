"""Prometheus — the self-improvement Titan.

The claim being tested: handler registration works, dispatch records
before/after to Mnemosyne, failed handlers don't poison the pass, and
the built-in substrate handlers don't raise on a fresh substrate.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestPrometheusDispatch(unittest.TestCase):

    def _fresh(self):
        from olympus.heroes.prometheus import Prometheus
        return Prometheus()

    def test_register_and_list(self):
        p = self._fresh()
        before = set(p.handlers())
        p.register("test-handler", lambda _a: ({"x": 1}, {"x": 2}))
        after = set(p.handlers())
        self.assertIn("test-handler", after - before)

    def test_dispatch_records_before_after(self):
        from olympus.titans.mnemosyne import mnemosyne
        p = self._fresh()
        p.register("recordable",
                   lambda _a: ({"a": 1}, {"a": 2, "delta": "added"}))
        before_count = len(mnemosyne.recall("prometheus.handler"))
        p.improve()
        after_records = mnemosyne.recall("prometheus.handler")
        self.assertGreater(len(after_records), before_count)
        # Find OUR record (the one for "recordable")
        ours = [m for m in after_records
                if m.body.get("handler") == "recordable"]
        self.assertGreaterEqual(len(ours), 1)
        rec = ours[-1]
        self.assertEqual(rec.body.get("before"), {"a": 1})
        self.assertEqual(rec.body.get("after"),
                         {"a": 2, "delta": "added"})
        self.assertTrue(rec.body.get("succeeded"))

    def test_failing_handler_does_not_stop_pass(self):
        from olympus.titans.mnemosyne import mnemosyne
        p = self._fresh()

        def boom(_a):
            raise RuntimeError("intentional test failure")

        p.register("boom-handler", boom)
        p.register("survives",
                   lambda _a: ({"ok": False}, {"ok": True}))
        report = p.improve()
        # At least both registered handlers were invoked (plus built-ins)
        invoked = {r.handler for r in report.results}
        self.assertIn("boom-handler", invoked)
        self.assertIn("survives", invoked)
        # boom recorded as failure
        boom_results = [r for r in report.results
                        if r.handler == "boom-handler"]
        self.assertEqual(len(boom_results), 1)
        self.assertFalse(boom_results[0].succeeded)
        self.assertIn("intentional test failure",
                      boom_results[0].detail)
        # survives recorded as success
        ok_results = [r for r in report.results
                      if r.handler == "survives"]
        self.assertTrue(ok_results[0].succeeded)
        # And a failure-record reached Mnemosyne
        fail_records = [m for m in mnemosyne.recall("prometheus.handler")
                        if m.body.get("handler") == "boom-handler"
                        and m.body.get("succeeded") is False]
        self.assertGreaterEqual(len(fail_records), 1)

    def test_pass_summary_remembered(self):
        from olympus.titans.mnemosyne import mnemosyne
        p = self._fresh()
        before = len(mnemosyne.recall("prometheus.pass"))
        p.improve()
        after = len(mnemosyne.recall("prometheus.pass"))
        self.assertGreater(after, before)
        last = mnemosyne.recall("prometheus.pass")[-1]
        self.assertIn("improvement pass", last.summary)

    def test_builtin_handlers_present(self):
        p = self._fresh()
        names = set(p.handlers())
        for expected in (
            "state-rotation",
            "brief-archive-compact",
            "prophecy-graduate",
            "prophecy-retire",
            "dead-eye-flag",
        ):
            self.assertIn(expected, names)

    def test_builtin_pass_does_not_raise(self):
        """The built-in handlers must tolerate any substrate state —
        empty briefs, empty prophecies, missing dirs, etc. — without
        raising."""
        p = self._fresh()
        report = p.improve()
        # Every result must be an ImprovementResult with succeeded set
        self.assertGreaterEqual(report.handlers_invoked, 5)
        for r in report.results:
            self.assertTrue(
                r.succeeded,
                f"handler {r.handler!r} failed: {r.detail}",
            )

    def test_register_overrides_previous(self):
        p = self._fresh()
        p.register("dup", lambda _a: ({"v": 1}, {"v": 2}))
        p.register("dup", lambda _a: ({"v": 9}, {"v": 10}))
        # handlers() shouldn't have it twice
        self.assertEqual(
            sum(1 for h in p.handlers() if h == "dup"), 1,
        )


if __name__ == "__main__":
    unittest.main()
