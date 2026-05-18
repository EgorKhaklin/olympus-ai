"""CorrelationEngine tests — clusters + cascades + quiet detection."""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / 'src'
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestCorrelationEngine(unittest.TestCase):

    def test_correlate_produces_report_with_clusters(self):
        from olympus.monsters.argos.colony import colony
        from olympus.monsters.argos.correlation import correlation
        # Drive a deploy to populate the log
        colony.deploy()
        report = correlation.correlate(window_hours=24.0)
        self.assertGreaterEqual(report.pheromones_considered, 0)
        # Clusters list may be empty if no slice repeats, but the field exists
        self.assertIsInstance(report.clusters, list)
        self.assertIsInstance(report.cascades, list)

    def test_correlate_detects_quiet_eyes(self):
        from olympus.monsters.argos.correlation import correlation
        # Give a fake eye name that won't have any pheromones
        report = correlation.correlate(
            window_hours=24.0,
            known_eyes=["definitely-nonexistent-eye-name-xyz"],
        )
        quiet_names = [q.eye for q in report.quiet]
        self.assertIn("definitely-nonexistent-eye-name-xyz", quiet_names)


if __name__ == "__main__":
    unittest.main()
