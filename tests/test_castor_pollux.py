"""Castor & Pollux — the Dioscuri.

The claim being tested: Castor materializes a shadow root, runs a
session there in a subprocess, returns a structured ShadowReport;
Pollux compares two session-report dicts and surfaces structural diffs.

The shadow session is heavy (it spawns Python). Tests are guarded by
a timeout and skip-cleanup of shadow tempdirs to keep things light.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import shutil
import unittest


class TestPollux(unittest.TestCase):

    def test_identical_reports_have_no_diffs(self):
        from olympus.heroes.pollux import Pollux
        a = {"hydra_findings": 5, "argos_pheromones": 5,
             "proposals_count": 0, "insights": ["a", "b"]}
        b = dict(a)
        report = Pollux().compare(a, b, left_label="prod",
                                  right_label="prod-replay")
        self.assertFalse(report.differs)
        self.assertGreaterEqual(len(report.same_fields), 4)

    def test_differing_fields_captured(self):
        from olympus.heroes.pollux import Pollux
        a = {"hydra_findings": 5, "argos_pheromones": 5,
             "proposals_count": 0}
        b = {"hydra_findings": 9, "argos_pheromones": 5,
             "proposals_count": 0}
        report = Pollux().compare(a, b)
        self.assertTrue(report.differs)
        fields_with_diff = [d.field for d in report.differences]
        self.assertIn("hydra_findings", fields_with_diff)
        self.assertNotIn("argos_pheromones", fields_with_diff)

    def test_only_in_left_surfaces(self):
        from olympus.heroes.pollux import Pollux
        a = {"insights": ["x"], "hydra_findings": 1}
        b = {"hydra_findings": 1}
        report = Pollux().compare(a, b)
        self.assertIn("insights", report.only_in_left)

    def test_comparison_recorded(self):
        from olympus.heroes.pollux import Pollux
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("pollux.comparison"))
        Pollux().compare({"hydra_findings": 1}, {"hydra_findings": 2})
        after = len(mnemosyne.recall("pollux.comparison"))
        self.assertGreater(after, before)


class TestCastor(unittest.TestCase):

    def test_shadow_session_runs_and_reports(self):
        """Spawn one shadow session. Verify the report has a return
        code and a shadow_root that exists."""
        from olympus.heroes.castor import Castor
        c = Castor()
        report = c.shadow_session(timeout_seconds=45.0)
        try:
            # Whether or not the shadow session succeeded fully (it might
            # hit hearth-unlit if the seed didn't propagate), we MUST
            # see a return-code and shadow_root path.
            self.assertNotEqual(report.return_code, -1,
                f"shadow subprocess didn't run; error: {report.error}; "
                f"stderr: {report.stderr_tail}")
            self.assertTrue(report.shadow_root)
            import os
            self.assertTrue(os.path.exists(report.shadow_root))
        finally:
            if report.shadow_root:
                shutil.rmtree(report.shadow_root, ignore_errors=True)

    def test_shadow_records_to_mnemosyne(self):
        from olympus.heroes.castor import Castor
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("castor.shadow"))
        report = Castor().shadow_session(timeout_seconds=45.0)
        try:
            after = len(mnemosyne.recall("castor.shadow"))
            self.assertGreater(after, before)
        finally:
            if report.shadow_root:
                shutil.rmtree(report.shadow_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
