"""Asclepius — the healer.

The claim being tested: heal() runs every registered healer; failures
are isolated; built-in healers rebuild derived state without raising.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestAsclepius(unittest.TestCase):

    def test_register_and_list(self):
        from olympus.olympians.asclepius import Asclepius
        a = Asclepius()
        before = set(a.healers())
        a.register("my-healer", lambda: (True, True, "rebuilt"))
        self.assertIn("my-healer", set(a.healers()) - before)

    def test_heal_runs_all(self):
        from olympus.olympians.asclepius import Asclepius
        a = Asclepius()
        a.register("custom-1", lambda: (True, True, "ok"))
        report = a.heal()
        names = {r.healer for r in report.results}
        self.assertIn("custom-1", names)
        self.assertIn("iris-dashboard", names)

    def test_failing_healer_does_not_abort(self):
        from olympus.olympians.asclepius import Asclepius

        def boom():
            raise RuntimeError("intentional")

        a = Asclepius()
        a.register("boom-healer", boom)
        a.register("survives", lambda: (True, False, "no-op"))
        report = a.heal()
        boom_results = [r for r in report.results
                        if r.healer == "boom-healer"]
        ok_results = [r for r in report.results
                      if r.healer == "survives"]
        self.assertEqual(len(boom_results), 1)
        self.assertFalse(boom_results[0].succeeded)
        self.assertIn("intentional", boom_results[0].detail)
        self.assertTrue(ok_results[0].succeeded)

    def test_iris_healer_rebuilds_dashboard(self):
        from olympus.olympians.asclepius import Asclepius
        from olympus.primordials.gaia import root
        # Delete the iris html if it exists; healer should regenerate
        iris_path = root.child("state", "iris", "index.html")
        if iris_path.exists():
            iris_path.unlink()
        a = Asclepius()
        report = a.heal()
        iris_results = [r for r in report.results
                        if r.healer == "iris-dashboard"]
        self.assertEqual(len(iris_results), 1)
        self.assertTrue(iris_results[0].succeeded)
        self.assertTrue(iris_path.exists())

    def test_heal_pass_recorded(self):
        from olympus.olympians.asclepius import Asclepius
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("asclepius.heal"))
        Asclepius().heal()
        after = len(mnemosyne.recall("asclepius.heal"))
        self.assertGreater(after, before)

    def test_atlas_healer_flags_hung_burdens(self):
        """Seed a stale Atlas bear (started_at long ago, never released).
        Asclepius's atlas-burden healer should flag it but not auto-release."""
        from olympus.olympians.asclepius import Asclepius
        from olympus.titans.mnemosyne import mnemosyne
        # Seed a bear with a started_at 2 days ago, no matching release
        import uuid
        import datetime as _dt
        bid = uuid.uuid4().hex
        old = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=2)
        mnemosyne.remember(
            kind="atlas.bear",
            actor="atlas:test",
            summary="seeded stale burden",
            id=bid, op="test-stale", owner="asclepius-test",
            started_at=old.isoformat(),
            payload={},
        )
        before = len(mnemosyne.recall("asclepius.hung_burden"))
        Asclepius().heal()
        after = len(mnemosyne.recall("asclepius.hung_burden"))
        self.assertGreater(after, before)


if __name__ == "__main__":
    unittest.main()
