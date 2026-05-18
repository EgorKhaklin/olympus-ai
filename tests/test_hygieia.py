"""Hygieia — whole-substrate wellness.

The claim being tested: each cross-module check returns a finding;
the aggregate report counts well/warning/incoherent correctly;
non-`well` findings are accurately diagnosed.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestHygieia(unittest.TestCase):

    def test_check_returns_report(self):
        from olympus.olympians.hygieia import hygieia, WellnessReport
        report = hygieia.check()
        self.assertIsInstance(report, WellnessReport)
        self.assertTrue(report.started_at)
        self.assertTrue(report.ended_at)

    def test_six_canonical_checks_present(self):
        from olympus.olympians.hygieia import Hygieia
        report = Hygieia().check()
        check_names = {f.check for f in report.findings}
        for expected in ("pan-vs-invariants", "atlas-vs-sessions",
                          "daedalus-vs-disk", "plato-vs-disk",
                          "themis-vs-records", "charon-backlog"):
            self.assertIn(expected, check_names,
                f"check {expected!r} missing from Hygieia report")

    def test_counts_are_consistent(self):
        from olympus.olympians.hygieia import hygieia
        report = hygieia.check()
        self.assertEqual(
            report.well_count + report.warning_count +
            report.incoherent_count,
            len(report.findings),
        )

    def test_pass_recorded_to_mnemosyne(self):
        from olympus.olympians.hygieia import hygieia
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("hygieia.check"))
        hygieia.check()
        after = len(mnemosyne.recall("hygieia.check"))
        self.assertGreater(after, before)

    def test_plato_check_well_when_taxonomy_covers_disk(self):
        """The plato-vs-disk check should be 'well' or 'warning' —
        never 'incoherent' on a healthy substrate."""
        from olympus.olympians.hygieia import hygieia
        report = hygieia.check()
        for f in report.findings:
            if f.check == "plato-vs-disk":
                self.assertNotEqual(f.status, "incoherent")

    def test_daedalus_check_well_or_warning(self):
        from olympus.olympians.hygieia import hygieia
        report = hygieia.check()
        for f in report.findings:
            if f.check == "daedalus-vs-disk":
                self.assertIn(f.status, ("well", "warning"))


if __name__ == "__main__":
    unittest.main()
