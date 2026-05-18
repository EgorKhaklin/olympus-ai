"""Atlas — the load-bearer.

The claim being tested: bear() registers a burden; release() marks it
complete; shoulders() reports current load by filtering bear events
without a matching release. Append-only invariant preserved (S1).
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestAtlas(unittest.TestCase):

    def test_bear_returns_burden_with_id(self):
        from olympus.titans.atlas import Atlas
        a = Atlas()
        b = a.bear("test-op", "test-owner", note="x")
        try:
            self.assertTrue(b.id)
            self.assertEqual(b.op, "test-op")
            self.assertEqual(b.owner, "test-owner")
            self.assertEqual(b.payload.get("note"), "x")
            self.assertEqual(b.released_at, "")
        finally:
            a.release(b.id, outcome="test-cleanup")

    def test_shoulders_lists_unreleased_burdens(self):
        from olympus.titans.atlas import Atlas
        a = Atlas()
        b = a.bear("test-shoulders-op", "shoulders-test-owner")
        try:
            report = a.shoulders()
            ids = {bb.id for bb in report.current}
            self.assertIn(b.id, ids,
                          "bearing a burden should appear in shoulders()")
        finally:
            a.release(b.id, outcome="test-cleanup")

    def test_release_removes_from_current(self):
        from olympus.titans.atlas import Atlas
        a = Atlas()
        b = a.bear("test-release-op", "release-test-owner")
        a.release(b.id, outcome="ok")
        report = a.shoulders()
        ids = {bb.id for bb in report.current}
        self.assertNotIn(b.id, ids,
                         "released burden should drop from current shoulders")
        # And should appear in recently_released
        released_ids = {bb.id for bb in report.recently_released}
        self.assertIn(b.id, released_ids)

    def test_release_records_outcome(self):
        from olympus.titans.atlas import Atlas
        a = Atlas()
        b = a.bear("outcome-test-op", "outcome-test-owner")
        a.release(b.id, outcome="error")
        report = a.shoulders()
        matched = [bb for bb in report.recently_released if bb.id == b.id]
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0].outcome, "error")

    def test_context_manager_releases_on_exit(self):
        from olympus.titans.atlas import Atlas
        a = Atlas()
        with a.bearing("ctx-op", "ctx-owner") as b:
            burden_id = b.id
            mid = a.shoulders()
            self.assertIn(burden_id, {bb.id for bb in mid.current})
        after = a.shoulders()
        self.assertNotIn(burden_id, {bb.id for bb in after.current})

    def test_context_manager_releases_with_error_on_exception(self):
        from olympus.titans.atlas import Atlas
        a = Atlas()
        burden_id = ""
        with self.assertRaises(RuntimeError):
            with a.bearing("ctx-err-op", "ctx-err-owner") as b:
                burden_id = b.id
                raise RuntimeError("intentional")
        report = a.shoulders()
        released = [bb for bb in report.recently_released
                    if bb.id == burden_id]
        self.assertEqual(len(released), 1)
        self.assertTrue(released[0].outcome.startswith("error"))


class TestAtlasIntegration(unittest.TestCase):
    """Atlas is wired into Session.run() and Prometheus.improve()."""

    def test_session_run_bears_and_releases(self):
        from olympus.session import run_session
        from olympus.titans.atlas import atlas
        from olympus.olympians.hestia import hestia
        if not hestia.is_lit():
            hestia.kindle(name="atlas-test",
                          vocation="atlas integration check")
        # Snapshot bear count BEFORE
        from olympus.titans.mnemosyne import mnemosyne
        before_bears = len(mnemosyne.recall("atlas.bear"))
        before_releases = len(mnemosyne.recall("atlas.release"))
        r = run_session(directive="atlas integration test")
        self.assertIsNone(r.error)
        # At least one new bear AND release (the session itself)
        after_bears = len(mnemosyne.recall("atlas.bear"))
        after_releases = len(mnemosyne.recall("atlas.release"))
        self.assertGreater(after_bears, before_bears)
        self.assertGreater(after_releases, before_releases)
        # After the session, this session's burden is not in current
        shoulders = atlas.shoulders()
        owners = {b.owner for b in shoulders.current}
        self.assertNotIn(r.session_id, owners,
                         "session should release its burden when run finishes")

    def test_prometheus_improve_bears_and_releases(self):
        from olympus.heroes.prometheus import Prometheus
        from olympus.titans.atlas import atlas
        from olympus.titans.mnemosyne import mnemosyne
        before_bears = len([m for m in mnemosyne.recall("atlas.bear")
                            if (m.body or {}).get("op") == "improvement-pass"])
        Prometheus().improve()
        after_bears = len([m for m in mnemosyne.recall("atlas.bear")
                           if (m.body or {}).get("op") == "improvement-pass"])
        self.assertGreater(after_bears, before_bears)
        # And no in-flight improvement-pass burdens after improve() returns
        report = atlas.shoulders()
        in_flight_ops = [b.op for b in report.current]
        self.assertNotIn("improvement-pass", in_flight_ops)


if __name__ == "__main__":
    unittest.main()
