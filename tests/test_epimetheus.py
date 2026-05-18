"""Epimetheus — the afterthought-bringer.

The claim being tested: reflect() reads events from Mnemosyne and
produces hindsight records with expected/actual/lesson; surprising
records flag where actual diverged from expected; the pass itself is
recorded to Mnemosyne for re-querying.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestEpimetheus(unittest.TestCase):

    def test_reflect_returns_report(self):
        from olympus.titans.epimetheus import Epimetheus, ReflectionReport
        e = Epimetheus()
        report = e.reflect(lookback_hours=24.0)
        self.assertIsInstance(report, ReflectionReport)
        self.assertTrue(report.started_at)
        self.assertTrue(report.ended_at)
        self.assertEqual(report.lookback_hours, 24.0)

    def test_reflect_processes_prophecies(self):
        """A truthy prophecy verification should produce a hindsight
        with surprising=False; a falsy one should produce surprising=True."""
        from olympus.titans.epimetheus import Epimetheus
        from olympus.titans.mnemosyne import mnemosyne
        # Seed prophecy verifications directly via Mnemosyne
        mnemosyne.remember(
            kind="prophecy.verified",
            actor="test:apollo",
            summary="seed accepted",
            prediction="epimetheus-seed-accepted",
            statement="seed", horizon="2020-01-01",
            accepted=True,
        )
        mnemosyne.remember(
            kind="prophecy.verified",
            actor="test:apollo",
            summary="seed rejected",
            prediction="epimetheus-seed-rejected",
            statement="seed", horizon="2020-01-01",
            accepted=False,
        )
        report = Epimetheus().reflect(lookback_hours=0)  # 0 = no cutoff
        names = {r.subject_id for r in report.records
                 if r.subject_kind == "prophecy"}
        self.assertIn("epimetheus-seed-accepted", names)
        self.assertIn("epimetheus-seed-rejected", names)
        # Find each
        accepted = next(r for r in report.records
                        if r.subject_kind == "prophecy"
                        and r.subject_id == "epimetheus-seed-accepted")
        rejected = next(r for r in report.records
                        if r.subject_kind == "prophecy"
                        and r.subject_id == "epimetheus-seed-rejected")
        self.assertFalse(accepted.surprising)
        self.assertTrue(rejected.surprising)

    def test_reflect_processes_session_errors(self):
        from olympus.titans.epimetheus import Epimetheus
        from olympus.titans.mnemosyne import mnemosyne
        mnemosyne.remember(
            kind="session.errored",
            actor="test:session",
            summary="seeded error",
            session_id="epimetheus-seed-session",
            error="TestError: intentional",
        )
        report = Epimetheus().reflect(lookback_hours=0)
        matched = [r for r in report.records
                   if r.subject_kind == "session"
                   and r.subject_id == "epimetheus-seed-session"]
        self.assertGreaterEqual(len(matched), 1)
        self.assertTrue(matched[0].surprising)
        self.assertIn("error", matched[0].actual.lower())

    def test_reflect_processes_handler_failures(self):
        from olympus.titans.epimetheus import Epimetheus
        from olympus.titans.mnemosyne import mnemosyne
        mnemosyne.remember(
            kind="prometheus.handler",
            actor="test:prometheus:seeded",
            summary="seeded handler failure",
            handler="epimetheus-seed-handler",
            succeeded=False,
        )
        report = Epimetheus().reflect(lookback_hours=0)
        matched = [r for r in report.records
                   if r.subject_kind == "handler"
                   and r.subject_id == "epimetheus-seed-handler"]
        self.assertGreaterEqual(len(matched), 1)
        self.assertTrue(matched[0].surprising)

    def test_pass_is_recorded_to_mnemosyne(self):
        from olympus.titans.epimetheus import Epimetheus
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("epimetheus.pass"))
        Epimetheus().reflect(lookback_hours=24.0)
        after = len(mnemosyne.recall("epimetheus.pass"))
        self.assertGreater(after, before)

    def test_hindsights_query_returns_recorded(self):
        from olympus.titans.epimetheus import Epimetheus
        from olympus.titans.mnemosyne import mnemosyne
        # Seed at least one prophecy so a hindsight gets recorded
        mnemosyne.remember(
            kind="prophecy.verified",
            actor="test:apollo",
            summary="hindsights-query-seed",
            prediction="epimetheus-hindsights-query",
            accepted=True,
        )
        e = Epimetheus()
        e.reflect(lookback_hours=0)
        hindsights = e.hindsights(limit=200)
        # At least one hindsight references our seeded prophecy
        seen = [h for h in hindsights
                if h.subject_id == "epimetheus-hindsights-query"]
        self.assertGreaterEqual(len(seen), 1)


if __name__ == "__main__":
    unittest.main()
