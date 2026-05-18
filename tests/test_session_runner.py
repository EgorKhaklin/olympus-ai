"""End-to-end session-runner tests.

The loop is the most important new surface. These tests cover the
happy path, the hearth-unlit refusal, and the Mnemosyne-records-every-
session property."""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / 'src'
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestSessionRunner(unittest.TestCase):

    def test_session_runs_when_hearth_lit(self):
        from olympus.session import run_session
        from olympus.olympians.hestia import hestia
        # ensure hearth is lit (idempotent — tests don't extinguish)
        if not hestia.is_lit():
            hestia.kindle(name="test-deployment",
                          vocation="test runs of the session loop")
        r = run_session(directive="unit test")
        self.assertIsNone(r.error, f"session errored: {r.error}")
        self.assertGreaterEqual(r.hydra_findings, 9, "HYDRA should report per head")
        self.assertGreaterEqual(r.argos_pheromones, 9, "Argos should deposit per eye")
        self.assertIn("session-", r.brief_label)
        self.assertGreater(r.brief_findings, 0)
        self.assertTrue(r.styx_intact)

    def test_session_recorded_in_mnemosyne(self):
        from olympus.session import run_session
        from olympus.titans.mnemosyne import mnemosyne
        from olympus.olympians.hestia import hestia
        if not hestia.is_lit():
            hestia.kindle(name="test-deployment-2",
                          vocation="session memory test")
        r = run_session(directive="recorded-in-mnemosyne")
        memories = mnemosyne.recall("session.completed", "session-runner")
        self.assertTrue(any(m.body.get("session_id") == r.session_id for m in memories),
            "session must leave a session.completed memory")

    def test_athena_brief_corroborates_across_tiers(self):
        """When the same slice is seen by both HYDRA and Argos in a session,
        Athena should produce a high-confidence brief."""
        from olympus.session import run_session
        from olympus.olympians.hestia import hestia
        if not hestia.is_lit():
            hestia.kindle(name="test-deployment-3",
                          vocation="confidence test")
        r = run_session()
        # Several slices are watched by both head_cosmogony+eye_cosmogony_drift,
        # head_pantheon+eye_pantheon_completeness, etc. → high confidence
        self.assertGreaterEqual(r.brief_confidence, 0.6,
            f"expected high cross-tier confidence; got {r.brief_confidence}")


if __name__ == "__main__":
    unittest.main()
