"""Athena reads Mnemosyne — synthesis becomes history-aware.

The claim being tested: Athena's brief surfaces cross-session insights
that aren't derivable from the current session's findings alone.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import pathlib
import tempfile
import unittest


class _FakeHydraFinding:
    def __init__(self, head, slice, severity, detail=""):
        self.head = head; self.slice = slice; self.severity = severity
        self.detail = detail


class _FakeHydraReport:
    def __init__(self, findings):
        self.findings = findings


class _FakePheromone:
    def __init__(self, eye, slice, kind, intensity=1.0, detail=""):
        self.eye = eye; self.slice = slice; self.kind = kind
        self.intensity = intensity; self.detail = detail


class _FakeCensus:
    def __init__(self, phers):
        self.pheromones = phers


def _fresh_athena():
    """Return an Athena instance whose briefs_path is a fresh tmp dir,
    so history-aware reasoning sees a clean slate per test."""
    from olympus.olympians.athena import Athena
    return Athena(briefs_path=pathlib.Path(tempfile.mkdtemp()))


class TestHistoryAwareAthena(unittest.TestCase):

    def test_brief_has_history_aware_fields(self):
        athena = _fresh_athena()
        hr = _FakeHydraReport([_FakeHydraFinding("h1", "slice-x", "info")])
        ac = _FakeCensus([_FakePheromone("e1", "slice-x", "info")])
        brief = athena.compose_from(hr, ac, label="history-test-1")
        # All new fields exist (even if empty)
        self.assertIsInstance(brief.insights, list)
        self.assertIsInstance(brief.recurring_slices, list)
        self.assertIsInstance(brief.newly_alerted_slices, list)
        self.assertIsInstance(brief.resolved_slices, list)
        self.assertIsInstance(brief.stable_slices, list)

    def test_repeated_alerts_surface_as_recurring(self):
        """Simulate 3 sessions all alerting on the same slice; the 3rd
        brief should surface 'slice-recurring' as recurring."""
        athena = _fresh_athena()
        SLICE = "test-recurring-slice"
        for i in range(4):
            hr = _FakeHydraReport([
                _FakeHydraFinding(f"h{i}", SLICE, "alert",
                                   detail=f"alert {i}"),
            ])
            ac = _FakeCensus([
                _FakePheromone(f"e{i}", SLICE, "alert", detail=f"alert {i}"),
            ])
            brief = athena.compose_from(hr, ac, label=f"recurring-{i}")
        # 4 briefs in a row, all alerting on SLICE → recurring detected
        recurring_slices = [r["slice"] for r in brief.recurring_slices]
        self.assertIn(SLICE, recurring_slices)

    def test_insights_nonempty_when_history_present(self):
        """After running compose_from a few times, insights should be
        non-empty (at minimum the 'stable' baseline insight)."""
        athena = _fresh_athena()
        for i in range(3):
            hr = _FakeHydraReport([
                _FakeHydraFinding("h-stable", "stable-slice-a", "info"),
                _FakeHydraFinding("h-stable", "stable-slice-b", "info"),
            ])
            ac = _FakeCensus([
                _FakePheromone("e-stable", "stable-slice-a", "info"),
                _FakePheromone("e-stable", "stable-slice-b", "info"),
            ])
            brief = athena.compose_from(hr, ac, label=f"stable-{i}")
        # The brief should have at least one insight
        self.assertGreater(len(brief.insights), 0)

    def test_resolved_slice_detected(self):
        """One session alerts on slice-r; next session does not. The
        second brief should list slice-r as resolved."""
        athena = _fresh_athena()
        SLICE = "test-resolved-slice"
        # Alert session
        athena.compose_from(
            _FakeHydraReport([_FakeHydraFinding("h", SLICE, "alert")]),
            _FakeCensus([_FakePheromone("e", SLICE, "alert")]),
            label="resolve-pre",
        )
        # Quiet session — no findings on SLICE
        brief = athena.compose_from(
            _FakeHydraReport([_FakeHydraFinding("h", "OTHER-SLICE", "info")]),
            _FakeCensus([_FakePheromone("e", "OTHER-SLICE", "info")]),
            label="resolve-post",
        )
        self.assertIn(SLICE, brief.resolved_slices)


if __name__ == "__main__":
    unittest.main()
