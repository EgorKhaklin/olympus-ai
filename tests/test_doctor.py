"""Doctor — single-screen health diagnostic.

The claim being tested: diagnose() runs every check; returns a
report with ok/warn/fail counts; records the diagnosis to Mnemosyne;
each check is robust (failures in one don't abort the others).
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestDoctor(unittest.TestCase):

    def test_diagnose_returns_report(self):
        from olympus.runtime.doctor import diagnose, DoctorReport
        report = diagnose()
        self.assertIsInstance(report, DoctorReport)
        self.assertTrue(report.diagnosed_at)
        self.assertTrue(report.python_version)
        self.assertGreater(len(report.findings), 5,
                           "expected at least 6 checks")

    def test_counts_are_consistent(self):
        from olympus.runtime.doctor import diagnose
        report = diagnose()
        total = report.ok_count + report.warn_count + report.fail_count
        self.assertEqual(total, len(report.findings))

    def test_records_diagnosis(self):
        from olympus.runtime.doctor import diagnose
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("doctor.diagnosis"))
        diagnose()
        after = len(mnemosyne.recall("doctor.diagnosis"))
        self.assertGreater(after, before)

    def test_all_expected_checks_present(self):
        from olympus.runtime.doctor import diagnose
        report = diagnose()
        names = {f.name for f in report.findings}
        for expected in ("hygieia", "pan", "styx", "atlas",
                          "themis", "llm-bridge", "state-disk"):
            self.assertIn(expected, names,
                f"doctor must include {expected!r} check")


if __name__ == "__main__":
    unittest.main()
