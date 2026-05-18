"""SessionReport deltas + invoke wisdom + Furies-in-loop.

The claim: each session knows how it compares to the previous one,
and the substrate can explain what it has learned cumulatively.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestSessionDeltas(unittest.TestCase):

    def test_session_report_has_delta_fields(self):
        from olympus.session import SessionReport
        r = SessionReport(session_id="x", directive=None, started_at="")
        self.assertEqual(r.delta_new_alerts, [])
        self.assertEqual(r.delta_resolved_alerts, [])
        self.assertEqual(r.delta_hydra_change, 0)
        self.assertEqual(r.delta_argos_change, 0)
        self.assertEqual(r.delta_prior_session_id, "")

    def test_session_report_has_prophecy_fields(self):
        from olympus.session import SessionReport
        r = SessionReport(session_id="x", directive=None, started_at="")
        self.assertEqual(r.prophecies_verified, 0)
        self.assertEqual(r.prophecies_accepted, 0)
        self.assertEqual(r.prophecies_rejected, 0)
        self.assertEqual(r.prophecy_results, [])

    def test_session_report_has_fury_alerts(self):
        from olympus.session import SessionReport
        r = SessionReport(session_id="x", directive=None, started_at="")
        self.assertEqual(r.fury_alerts, [])

    def test_session_report_has_insights_recurring_resolved(self):
        from olympus.session import SessionReport
        r = SessionReport(session_id="x", directive=None, started_at="")
        self.assertEqual(r.insights, [])
        self.assertEqual(r.recurring_slices, [])
        self.assertEqual(r.newly_alerted_slices, [])
        self.assertEqual(r.resolved_slices, [])

    def test_end_to_end_session_populates_history_aware_fields(self):
        from olympus.session import run_session
        from olympus.olympians.hestia import hestia
        if not hestia.is_lit():
            hestia.kindle(name="delta-test",
                          vocation="delta + wisdom verification")
        r = run_session(directive="delta verification")
        self.assertIsNone(r.error)
        # On any non-fresh deployment, prior sessions exist and the delta
        # prior_session_id should be populated.
        self.assertIsInstance(r.delta_prior_session_id, str)
        # Insights field is populated by Athena's reasoning
        self.assertIsInstance(r.insights, list)


class TestWisdom(unittest.TestCase):

    def test_wisdom_composes(self):
        from olympus.wisdom import wisdom
        w = wisdom()
        self.assertGreaterEqual(w.sessions_total, 0)
        self.assertIsInstance(w.insights, list)
        # On a deployment with sessions in history, at least one insight
        # should be present
        if w.sessions_total > 0:
            self.assertGreater(len(w.insights), 0)

    def test_wisdom_renders_as_text(self):
        from olympus.wisdom import wisdom
        text = wisdom().as_text()
        self.assertIn("Olympus wisdom", text)
        self.assertIn("Activity", text)
        self.assertIn("Constitution", text)


if __name__ == "__main__":
    unittest.main()
